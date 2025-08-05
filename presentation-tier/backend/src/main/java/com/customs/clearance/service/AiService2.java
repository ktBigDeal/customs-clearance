package com.customs.clearance.service;

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

import com.customs.clearance.entity.Declaration;
import com.customs.clearance.entity.Declaration.DeclarationStatus;
import com.customs.clearance.entity.User;
import com.customs.clearance.repository.DeclarationRepository;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import lombok.RequiredArgsConstructor;

import java.io.IOException;

@Service
@RequiredArgsConstructor
public class AiService2 {

    private final DeclarationRepository declarationRepository;

    private final RestTemplate restTemplate = new RestTemplate();

    public Declaration analyzeDocuments(
        Declaration declaration, 
        MultipartFile invoiceFile, 
        MultipartFile packingListFile, 
        MultipartFile billOfLadingFile,
        MultipartFile certificateOfOriginFile
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

        Long userId = getCurrentUserId();

        if(userId == null){
            throw new IllegalArgumentException("사용자 접근 거부");
        }

        String fastApiUrl = "http://localhost:8000/api/v1/models/model-ocr/analyze-documents";

        MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
        body.add("invoice_file", convertToResource(invoiceFile));
        body.add("packing_list_file", convertToResource(packingListFile));
        body.add("bill_of_lading_file", convertToResource(billOfLadingFile));

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.MULTIPART_FORM_DATA);

        HttpEntity<MultiValueMap<String, Object>> request = new HttpEntity<>(body, headers);

        try {
            ResponseEntity<String> response = restTemplate.postForEntity(fastApiUrl, request, String.class);

            if (!response.getStatusCode().is2xxSuccessful() || response.getBody() == null) {
                throw new RuntimeException("Ai api 호출 에러" + response.getStatusCode());
            }

            // json 출력값
            // ObjectMapper mapper = new ObjectMapper();
            // JsonNode jsonNode = mapper.readTree(response.getBody());

            String jsonString = response.getBody();

            declaration.setDeclarationDetails(jsonString);
            declaration.setStatus(DeclarationStatus.SUBMITTED);
            declaration.setCreatedBy(userId);

            return declarationRepository.save(declaration);
            
        } catch (RestClientException e) {
            // 네트워크, HTTP 오류 처리
            throw new RuntimeException("네트워크 에러", e);
        // } catch (IOException e) {
        //     // JSON 파싱 오류 처리
        //     throw new RuntimeException("AI 출력 파싱 에러 발생", e);
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
