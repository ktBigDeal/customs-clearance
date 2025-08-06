package com.customs.clearance.service;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.core.io.Resource;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;

import com.customs.clearance.entity.Attachment;
import com.customs.clearance.entity.Declaration;
import com.customs.clearance.entity.Declaration.DeclarationStatus;
import com.customs.clearance.entity.User;
import com.customs.clearance.repository.AttachmentRepository;
import com.customs.clearance.repository.DeclarationRepository;
import com.customs.clearance.repository.UserRepository;
import com.customs.clearance.security.JwtTokenProvider;

import lombok.RequiredArgsConstructor;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.Optional;

@Service
@RequiredArgsConstructor
public class AiService2 {

    private final DeclarationRepository declarationRepository;
    private final AttachmentRepository attachmentRepository;
    private final UserRepository userRepository;

    private final RestTemplate restTemplate;

    private final JwtTokenProvider jwtTokenProvider;

    @Value("${customs.clearance.file.upload-dir}")
    private String uploadDir;

    public Declaration insertDeclaration(
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
                            && (billOfLadingFile == null || billOfLadingFile.isEmpty())
                            && (certificateOfOriginFile == null || certificateOfOriginFile.isEmpty());

        if (allFilesEmpty) {
            throw new IllegalArgumentException("파일 정보 누락");
        }

        // 토큰으로부터 username 추출
        if (token == null || !jwtTokenProvider.validateToken(token)) {
            throw new IllegalArgumentException("사용자 접근 거부");
        }
        
        String username = jwtTokenProvider.getUsernameFromToken(token);
        Long userId = userRepository.findByUsername(username)
                        .map(User::getId)
                        .orElseThrow(() -> new RuntimeException("사용자 미확인"));

        String jsonString = callAiPipeLine(invoiceFile, packingListFile, billOfLadingFile);

        declaration.setDeclarationDetails(jsonString);
        declaration.setStatus(DeclarationStatus.SUBMITTED);
        declaration.setCreatedBy(userId);

        declaration = declarationRepository.save(declaration);

        saveAttachment(declaration, invoiceFile, "invoice", userId);
        saveAttachment(declaration, packingListFile, "packing_list", userId);
        saveAttachment(declaration, billOfLadingFile, "bill_of_lading", userId);
        saveAttachment(declaration, certificateOfOriginFile, "certificate_of_origin", userId);

        return declaration;

    }

    private void saveAttachment(
        Declaration declaration,
        MultipartFile file,
        String typeName,
        Long uploadedBy
    ) throws IOException {
        if (file != null && !file.isEmpty()) {
            String newName = declaration.getId() + "_" + typeName;
            String filePath = saveFile(file, newName);

            Attachment attachment = new Attachment(
                declaration.getId(),
                newName + getExtension(file),   // filename
                file.getOriginalFilename(),     // originalFilename
                filePath,
                file.getSize(),
                file.getContentType(),
                uploadedBy
            );

            attachmentRepository.save(attachment);
        }
    }

    private String getExtension(MultipartFile file) {
        String name = file.getOriginalFilename();
        if (name != null && name.contains(".")) {
            return name.substring(name.lastIndexOf("."));
        }
        return "";
    }

    private String saveFile(MultipartFile file, String newFilename) throws IOException {
        File dir = new File(uploadDir);
        if (!dir.exists()) {
            dir.mkdirs();
        }

        String originalExtension = Optional.ofNullable(file.getOriginalFilename())
            .filter(f -> f.contains("."))
            .map(f -> f.substring(f.lastIndexOf(".")))
            .orElse("");

        String finalFilename = newFilename + originalExtension;
        File destination = new File(dir, finalFilename);

        try (InputStream input = file.getInputStream();
            OutputStream output = new FileOutputStream(destination)) {
            byte[] buffer = new byte[8192];
            int bytesRead;
            while ((bytesRead = input.read(buffer)) != -1) {
                output.write(buffer, 0, bytesRead);
            }
        }

        return "uploads/" + finalFilename;
    }

    private String callAiPipeLine(
        MultipartFile invoiceFile,
        MultipartFile packingListFile,
        MultipartFile billOfLadingFile
    ) throws IOException {

        String fastApiUrl = "http://localhost:8000/api/v1/models/model-ocr/analyze-documents";

        MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
        if (invoiceFile != null && !invoiceFile.isEmpty())
            body.add("invoice_file", convertToResource(invoiceFile));
        if (packingListFile != null && !packingListFile.isEmpty())
            body.add("packing_list_file", convertToResource(packingListFile));
        if (billOfLadingFile != null && !billOfLadingFile.isEmpty())
            body.add("bill_of_lading_file", convertToResource(billOfLadingFile));

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.MULTIPART_FORM_DATA);

        HttpEntity<MultiValueMap<String, Object>> request = new HttpEntity<>(body, headers);

        try {
            ResponseEntity<String> response = restTemplate.postForEntity(fastApiUrl, request, String.class);

            if (!response.getStatusCode().is2xxSuccessful() || response.getBody() == null) {
                throw new RuntimeException("Ai 호출 에러: " + response.getStatusCode());
            }

            return response.getBody();

        } catch (RestClientException e) {
            throw new RuntimeException("FastAPI 서버 통신 오류", e);
        }
    }

    // MultipartFile -> Resource 변환
    private Resource convertToResource(MultipartFile file) throws IOException {
        return new ByteArrayResource(file.getBytes()) {
            @Override public String getFilename() {
                return file.getOriginalFilename();
            }
            @Override public long contentLength() {
                return file.getSize();
            }
        };
    }

    public Long getCurrentUserId() {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();

        if (authentication != null && authentication.isAuthenticated()) {
            User user = (User) authentication.getPrincipal();
            return user.getId();
        }

        return null;
    }

}
