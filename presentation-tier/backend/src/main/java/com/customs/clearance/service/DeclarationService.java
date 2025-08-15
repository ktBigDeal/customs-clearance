package com.customs.clearance.service;

import com.customs.clearance.entity.Attachment;
import com.customs.clearance.entity.Declaration;
import com.customs.clearance.entity.Declaration.DeclarationStatus;
import com.customs.clearance.entity.User;
import com.customs.clearance.dto.DeclarationAdminDto;
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
import java.util.HashMap;
import java.time.LocalDateTime;

import com.customs.clearance.dto.DeclarationStatsDto;
import com.customs.clearance.service.KcsImportXmlMapper;
import com.customs.clearance.service.KcsExportXmlMapper;

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

    public List<Declaration> getDeclarationList(String status, String token) {
        
        User user = getUserByToken(token);

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

            list = declarationRepository.findAllByCreatedByAndStatus(user.getId(), enumStatus);
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

    public List<Attachment> getAttachmentListByUser(String token){

        User user = getUserByToken(token);

        List<Declaration> deList = declarationRepository.findAllByCreatedBy(user.getId());

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

    /**
     * 관리자용 신고서 목록 조회 (사용자 정보 포함)
     * 
     * @param status 필터링할 상태 (null이면 전체)
     * @param token 관리자 토큰
     * @return 사용자 정보가 포함된 신고서 목록
     */
    public List<DeclarationAdminDto> getAdminDeclarationList(String status, String token) {
        User user = getUserByToken(token);
        
        if (!user.getRole().equals("ADMIN")) {
            throw new RuntimeException("관리자 권한 사용자만 조회할 수 있습니다.");
        }
        
        List<Declaration> declarations;
        if (status == null) {
            declarations = declarationRepository.findAll();
        } else {
            try {
                DeclarationStatus statusEnum = DeclarationStatus.valueOf(status.toUpperCase());
                declarations = declarationRepository.findAllByStatus(statusEnum);
            } catch (IllegalArgumentException e) {
                throw new RuntimeException("잘못된 상태값: " + status);
            }
        }
        
        List<DeclarationAdminDto> result = new ArrayList<>();
        
        for (Declaration declaration : declarations) {
            DeclarationAdminDto dto = DeclarationAdminDto.fromEntity(declaration);
            
            // 사용자 정보 추가
            if (declaration.getCreatedBy() != null) {
                userRepository.findById(declaration.getCreatedBy()).ifPresent(creator -> {
                    dto.withUserInfo(creator.getName(), creator.getEmail(), creator.getCompany());
                });
            }
            
            result.add(dto);
        }
        
        return result;
    }

    /**
     * 대시보드용 통계 데이터 조회
     */
    public DeclarationStatsDto getDeclarationStats(String token) {
        User user = getUserByToken(token);
        List<Declaration> userDeclarations;
        
        if (user.getRole().equals("ADMIN")) {
            // 관리자는 전체 통계
            userDeclarations = declarationRepository.findAll();
        } else {
            // 일반 사용자는 본인 신고서만
            userDeclarations = declarationRepository.findAllByCreatedBy(user.getId());
        }
        
        long total = userDeclarations.size();
        long pending = userDeclarations.stream()
            .mapToLong(d -> d.getStatus() == DeclarationStatus.DRAFT || d.getStatus() == DeclarationStatus.UPDATED ? 1 : 0)
            .sum();
        long underReview = userDeclarations.stream()
            .mapToLong(d -> d.getStatus() == DeclarationStatus.UNDER_REVIEW ? 1 : 0)
            .sum();
        long approved = userDeclarations.stream()
            .mapToLong(d -> d.getStatus() == DeclarationStatus.APPROVED ? 1 : 0)
            .sum();
        long rejected = userDeclarations.stream()
            .mapToLong(d -> d.getStatus() == DeclarationStatus.REJECTED ? 1 : 0)
            .sum();
        long cleared = userDeclarations.stream()
            .mapToLong(d -> d.getStatus() == DeclarationStatus.SUBMITTED ? 1 : 0)
            .sum();
            
        return new DeclarationStatsDto(total, pending, underReview, approved, rejected, cleared);
    }

    /**
     * 대시보드용 최근 신고서 목록 조회
     */
    public List<Declaration> getRecentDeclarations(int limit, String token) {
        User user = getUserByToken(token);
        
        if (user.getRole().equals("ADMIN")) {
            // 관리자는 전체 최근 신고서
            return declarationRepository.findTop5ByOrderByCreatedAtDesc()
                .stream()
                .limit(limit)
                .toList();
        } else {
            // 일반 사용자는 본인 신고서만
            return declarationRepository.findAllByCreatedByOrderByCreatedAtDesc(user.getId())
                .stream()
                .limit(limit)
                .toList();
        }
    }

    /**
     * 대시보드용 차트 데이터 조회
     */
    public Map<String, Object> getDashboardChartData(String token) {
        User user = getUserByToken(token);
        List<Declaration> userDeclarations;
        
        if (user.getRole().equals("ADMIN")) {
            userDeclarations = declarationRepository.findAll();
        } else {
            userDeclarations = declarationRepository.findAllByCreatedBy(user.getId());
        }
        
        Map<String, Object> result = new HashMap<>();
        
        // 월별 처리 건수 (최근 6개월)
        List<Map<String, Object>> monthlyData = new ArrayList<>();
        for (int i = 5; i >= 0; i--) {
            LocalDateTime monthStart = LocalDateTime.now().minusMonths(i).withDayOfMonth(1).withHour(0).withMinute(0).withSecond(0);
            LocalDateTime monthEnd = monthStart.plusMonths(1).minusSeconds(1);
            
            long count = userDeclarations.stream()
                .filter(d -> d.getCreatedAt().isAfter(monthStart) && d.getCreatedAt().isBefore(monthEnd))
                .count();
                
            Map<String, Object> monthData = new HashMap<>();
            monthData.put("month", monthStart.getMonth().toString());
            monthData.put("count", count);
            monthlyData.add(monthData);
        }
        result.put("monthlyData", monthlyData);
        
        // 상태별 분포
        List<Map<String, Object>> statusData = new ArrayList<>();
        for (DeclarationStatus status : DeclarationStatus.values()) {
            long count = userDeclarations.stream()
                .filter(d -> d.getStatus() == status)
                .count();
            if (count > 0) {
                Map<String, Object> statusEntry = new HashMap<>();
                statusEntry.put("status", status.name());
                statusEntry.put("count", count);
                statusEntry.put("label", getStatusKoreanName(status));
                statusData.add(statusEntry);
            }
        }
        result.put("statusData", statusData);
        
        return result;
    }
    
    private String getStatusKoreanName(DeclarationStatus status) {
        switch (status) {
            case DRAFT: return "초안";
            case UPDATED: return "수정됨";
            case SUBMITTED: return "제출됨";
            case UNDER_REVIEW: return "심사 중";
            case APPROVED: return "승인";
            case REJECTED: return "반려";
            default: return status.name();
        }
    }
}
