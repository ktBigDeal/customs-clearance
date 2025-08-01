package com.customs.clearance.controller;

import org.springframework.core.io.ByteArrayResource;
import org.springframework.core.io.Resource;
import org.springframework.http.*;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;

@RestController
@RequestMapping("/test-ocr")
public class OcrTestController {
    private final RestTemplate restTemplate = new RestTemplate();

    @PostMapping("/call-ocr")
    public ResponseEntity<String> callFastApiOcr(
            @RequestParam("invoice_file") MultipartFile invoiceFile,
            @RequestParam("packing_list_file") MultipartFile packingListFile,
            @RequestParam("bill_of_lading_file") MultipartFile billOfLadingFile
    ) throws IOException {

        String fastApiUrl = "http://localhost:8000/ocr/"; // FastAPI 서버 주소에 맞게 수정

        MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();

        body.add("invoice_file", toResource(invoiceFile));
        body.add("packing_list_file", toResource(packingListFile));
        body.add("bill_of_lading_file", toResource(billOfLadingFile));

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.MULTIPART_FORM_DATA);

        HttpEntity<MultiValueMap<String, Object>> requestEntity = new HttpEntity<>(body, headers);

        ResponseEntity<String> response = restTemplate.postForEntity(fastApiUrl, requestEntity, String.class);

        return ResponseEntity.status(response.getStatusCode()).body(response.getBody());
    }

    // MultipartFile -> Resource 변환 (파일명, content-type 유지)
    private Resource toResource(MultipartFile file) throws IOException {
        return new ByteArrayResource(file.getBytes()) {
            @Override
            public String getFilename() {
                return file.getOriginalFilename();
            }
            @Override
            public long contentLength() {
                return file.getSize();
            }
        };
    }
}
