package com.customs.clearance.service;

import com.customs.clearance.entity.Attachment;
import com.customs.clearance.entity.Declaration;
import com.customs.clearance.entity.Declaration.DeclarationStatus;
import com.customs.clearance.entity.User;
import com.customs.clearance.repository.AttachmentRepository;
import com.customs.clearance.repository.DeclarationRepository;
import com.customs.clearance.repository.UserRepository;
import com.customs.clearance.security.JwtTokenProvider;
import com.customs.clearance.util.DeclarationServiceUtils;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import lombok.RequiredArgsConstructor;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

@Service
@RequiredArgsConstructor
public class DeclarationService {

    private final DeclarationRepository declarationRepository;
    private final AttachmentRepository attachmentRepository;
    private final UserRepository userRepository;

    private final RestTemplate restTemplate;

    private final JwtTokenProvider jwtTokenProvider;

    @Value("${customs.clearance.file.upload-dir}")
    private String uploadDir;

    public Declaration postDeclaration(
        Declaration declaration, 
        MultipartFile invoiceFile, 
        MultipartFile packingListFile, 
        MultipartFile billOfLadingFile,
        MultipartFile certificateOfOriginFile,
        String token
    ) throws IOException {

        if (declaration == null) {
            throw new IllegalArgumentException("신고 정보 누락");
        }

        boolean allFilesEmpty = (invoiceFile == null || invoiceFile.isEmpty())
                            && (packingListFile == null || packingListFile.isEmpty())
                            && (billOfLadingFile == null || billOfLadingFile.isEmpty());

        if (allFilesEmpty) {
            throw new IllegalArgumentException("파일 정보 누락");
        }

        User user = getUserByToken(token);

        String jsonString = callAiPipeLine(declaration.getDeclarationType().toString(), invoiceFile, packingListFile, billOfLadingFile);

        declaration.setDeclarationDetails(jsonString);       
        declaration.setStatus(DeclarationStatus.DRAFT);
        declaration.setCreatedBy(user.getId());

        declaration = declarationRepository.save(declaration);

        saveAttachment(declaration, invoiceFile, "invoice", user.getId());
        saveAttachment(declaration, packingListFile, "packing_list", user.getId());
        saveAttachment(declaration, billOfLadingFile, "bill_of_lading", user.getId());
        saveAttachment(declaration, certificateOfOriginFile, "certificate_of_origin", user.getId());

        return declaration;
    }

    private User getUserByToken(String token){

        if (token == null || !jwtTokenProvider.validateToken(token)) {
            throw new IllegalArgumentException("사용자 접근 거부");
        }
        
        String username = jwtTokenProvider.getUsernameFromToken(token);
        User user = userRepository.findByUsername(username).orElseThrow(() -> new RuntimeException("사용자 정보 없음"));

        return user;
    }

    private void saveAttachment(
        Declaration declaration,
        MultipartFile file,
        String typeName,
        Long uploadedBy
    ) throws IOException {

        if (file != null && !file.isEmpty()) {

            String newName = declaration.getId() + "_" + typeName;
            String filePath = DeclarationServiceUtils.saveFile(file, newName, uploadDir);

            Attachment attachment = new Attachment(
                declaration.getId(),
                newName + DeclarationServiceUtils.getExtension(file),   // filename
                file.getOriginalFilename(),                             // originalFilename
                filePath,
                file.getSize(),
                file.getContentType(),
                uploadedBy
            );

            attachmentRepository.save(attachment);
        }
    }

    private String callAiPipeLine(
        String declarationType,
        MultipartFile invoiceFile,
        MultipartFile packingListFile,
        MultipartFile billOfLadingFile
    ) throws IOException {

        String fastApiUrl = "http://localhost:8000/api/v1/pipeline/process-complete-workflow";

        MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
        body.add("declaration_type", declarationType.toLowerCase());
        body.add("invoice_file", DeclarationServiceUtils.convertToResource(invoiceFile, uploadDir));
        body.add("packing_list_file", DeclarationServiceUtils.convertToResource(packingListFile, uploadDir));
        body.add("bill_of_lading_file", DeclarationServiceUtils.convertToResource(billOfLadingFile, uploadDir));

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.MULTIPART_FORM_DATA);

        HttpEntity<MultiValueMap<String, Object>> request = new HttpEntity<>(body, headers);

        try {
            ResponseEntity<String> response = restTemplate.postForEntity(fastApiUrl, request, String.class);

            if (!response.getStatusCode().is2xxSuccessful() || response.getBody() == null) {
                throw new RuntimeException("Ai 호출 에러: " + response.getStatusCode());
            }
            
            ObjectMapper mapper = new ObjectMapper();

            JsonNode root = mapper.readTree(response.getBody());

            JsonNode step3Data = root.path("pipeline_results").path("step_3_declaration").path("data");

            return mapper.writeValueAsString(step3Data);

        } catch (RestClientException e) {
            throw new RuntimeException("FastAPI 서버 통신 오류", e);
        }
    }

    public Map<String, Object> getDeclaration(Long declarationId, String token){
        
        Declaration declaration = declarationRepository.findById(declarationId).orElseThrow(() -> new RuntimeException("신고서 정보 없음"));

        User user = getUserByToken(token);

        if(user.getRole().equals("USER") && !user.getId().equals(declaration.getCreatedBy())){
            throw new RuntimeException("다른 사용자의 신고서는 조회할 수 없습니다.");
        }

        return DeclarationServiceUtils.convertDeclarationToMap(declaration);
    }

    public Map<String, Object> putDeclaration(Long declarationId, Map<String, Object> declarationMap, String token){

        Declaration declaration = declarationRepository.findById(declarationId).orElseThrow(() -> new RuntimeException("신고서 정보 없음"));

        User user = getUserByToken(token);

        if(user.getRole().equals("USER") && !user.getId().equals(declaration.getCreatedBy())){
            throw new RuntimeException("다른 사용자의 신고서는 수정할 수 없습니다.");
        }

        Declaration updatedDeclaration = DeclarationServiceUtils.convertMapToDeclaration(declarationMap, declaration);
        updatedDeclaration.setUpdatedBy(user.getId());
        updatedDeclaration.setStatus(DeclarationStatus.UPDATED);

        declaration = declarationRepository.save(updatedDeclaration);

        return DeclarationServiceUtils.convertDeclarationToMap(declaration);
    }

    public boolean deleteDeclaration(Long declarationId, String token){
        
        Declaration declaration = declarationRepository.findById(declarationId).orElseThrow(() -> new RuntimeException("신고서 정보 없음"));

        User user = getUserByToken(token);

        if(user.getRole().equals("USER") && !user.getId().equals(declaration.getCreatedBy())){
            throw new RuntimeException("다른 사용자의 신고서는 삭제할 수 없습니다.");
        }

        List<Attachment> attachments = attachmentRepository.findByDeclarationId(declarationId);

        DeclarationServiceUtils.deleteFiles(attachments, uploadDir);

        declarationRepository.delete(declaration);

        return true;
    }

    public List<Declaration> getDeclarationList(Long userId, String status, String token) {
        
        User user = getUserByToken(token);

        if(user.getRole().equals("USER") && !user.getId().equals(userId)){
            throw new RuntimeException("다른 사용자의 신고서 목록은 조회할 수 없습니다.");
        }

        List<Declaration> list = new ArrayList<>(); 

        if (user.getRole().equals("USER") && status == null) {
            list = declarationRepository.findAllByCreatedBy(user.getId());
        } else if (user.getRole().equals("USER") && status != null) {
            
            Declaration.DeclarationStatus enumStatus;

            try {
                enumStatus = Declaration.DeclarationStatus.valueOf(status.toUpperCase());
            } catch (IllegalArgumentException e) {
                throw new RuntimeException("잘못된 상태 값입니다: " + status);
            }

            list = declarationRepository.findAllByCreatedByAndStatus(userId, enumStatus);
        } else if(user.getRole().equals("ADMIN") && status == null){
            list = declarationRepository.findAll();
        } else if(user.getRole().equals("ADMIN") && status != null){
            
            Declaration.DeclarationStatus enumStatus;

            try {
                enumStatus = Declaration.DeclarationStatus.valueOf(status.toUpperCase());
            } catch (IllegalArgumentException e) {
                throw new RuntimeException("잘못된 상태 값입니다: " + status);
            }

            list = declarationRepository.findAllByStatus(enumStatus);
        }

        return list;
    }

    public List<Attachment> getAttachmentListByDeclaration(Long declarationId, String token){

        User user = getUserByToken(token);
        Declaration declaration = declarationRepository.findById(declarationId).orElseThrow(() -> new RuntimeException("신고서 정보 없음"));

        if(user.getRole().equals("USER") && !user.getId().equals(declaration.getCreatedBy())){
            throw new RuntimeException("다른 사용자의 파일 목록은 조회할 수 없습니다.");
        }

        List<Attachment> list = attachmentRepository.findByDeclarationId(declarationId);

         return list;
    }

    public List<Attachment> getAttachmentListByUser(Long userId, String token){

        User user = getUserByToken(token);

        if(user.getRole().equals("USER") && !user.getId().equals(userId)){
            throw new RuntimeException("다른 사용자의 파일 목록은 조회할 수 없습니다.");
        }

        List<Declaration> deList = declarationRepository.findAllByCreatedBy(userId);

        List<Attachment> list = new ArrayList<>();

        for(Declaration declaration : deList){
            List<Attachment> atList = attachmentRepository.findByDeclarationId(declaration.getId());
            list.addAll(atList);
        }

         return list;
    }

    public List<Attachment> getAttachmentListByAdmin(String token){

        User user = getUserByToken(token);

        if(!user.getRole().equals("ADMIN")){
            throw new RuntimeException("관리자 권한 사용자만 조회할 수 있습니다.");
        }

        List<Attachment> list = attachmentRepository.findAll();

         return list;
    }

    private final KcsImportXmlMapper kcsImportXmlMapper;
    private final KcsExportXmlMapper kcsExportXmlMapper;

    public byte [] generateKcsXml(Long declarationId, String docType, String token) {
        Declaration dec = declarationRepository.findById(declarationId)
                .orElseThrow(() -> new RuntimeException("신고서 정보 없음"));
        User user = getUserByToken(token);
        if (user.getRole().equals("USER") && !user.getId().equals(dec.getCreatedBy())) {
            throw new RuntimeException("다른 사용자의 신고서는 조회할 수 없습니다.");
        }

        // declarationDetails(JSON string) -> Map
        try {
            // docType이 null이면 엔티티 타입에 맞춤
            String type = (docType!=null? docType : dec.getDeclarationType().name()).toLowerCase();

            if ("import".equals(type)) {
                return kcsImportXmlMapper.buildImportXml(dec);
            } else if ("export".equals(type)) {
                return kcsExportXmlMapper.buildExportXml(dec);
            } else {
                throw new IllegalArgumentException("docType 은 import/export 중 하나여야 합니다.");
            }
        } catch (IOException e) {
            throw new RuntimeException("신고서 상세(JSON) 파싱 오류", e);
        } catch (Exception e) {
            throw new RuntimeException("KCS XML 생성 실패", e);
        }
    }
}
