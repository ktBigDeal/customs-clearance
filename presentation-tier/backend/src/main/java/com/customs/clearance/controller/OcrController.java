package com.customs.clearance.controller;

import org.springframework.core.io.ByteArrayResource;
import org.springframework.core.io.Resource;
import org.springframework.http.*;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.multipart.MultipartFile;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.io.IOException;

/**
 * 관세 문서 OCR 처리를 위한 컨트롤러
 * - 3종 문서 업로드
 * - FastAPI OCR 호출
 * - 결과 JSON 반환
 */
@RestController
@RequestMapping("/ocr")
public class OcrController {

    private final RestTemplate restTemplate = new RestTemplate();

    @PostMapping(
    value = "/analyze-documents",
    consumes = MediaType.MULTIPART_FORM_DATA_VALUE,
    produces = MediaType.APPLICATION_JSON_VALUE  // 리턴 타입 명시
    )
    public ResponseEntity<JsonNode> analyzeDocuments(
            @RequestPart("invoice_file") MultipartFile invoiceFile,
            @RequestPart("packing_list_file") MultipartFile packingListFile,
            @RequestPart("bill_of_lading_file") MultipartFile billOfLadingFile
    ) throws IOException {

        String fastApiUrl = "http://localhost:8000/api/v1/models/model-ocr/analyze-documents";

        MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
        body.add("invoice_file", convertToResource(invoiceFile));
        body.add("packing_list_file", convertToResource(packingListFile));
        body.add("bill_of_lading_file", convertToResource(billOfLadingFile));

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.MULTIPART_FORM_DATA);

        HttpEntity<MultiValueMap<String, Object>> request = new HttpEntity<>(body, headers);

        ResponseEntity<String> response = restTemplate.postForEntity(fastApiUrl, request, String.class);

        ObjectMapper mapper = new ObjectMapper();
        JsonNode jsonNode = mapper.readTree(response.getBody());

        return ResponseEntity.status(response.getStatusCode())
                            .contentType(MediaType.APPLICATION_JSON)
                            .body(jsonNode);
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
}
