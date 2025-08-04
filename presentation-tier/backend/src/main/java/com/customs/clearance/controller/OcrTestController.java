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

/**
 * OCR 서비스 테스트용 컸트롤러
 * 
 * Spring Boot 애플리케이션에서 FastAPI 기반 OCR 서비스를 호출하여 테스트하는 컸트롤러입니다.
 * 관세 관련 문서 3종(Invoice, Packing List, Bill of Lading)을 동시에 업로드하여 OCR 처리를 수행합니다.
 * 
 * <p>주요 기능:</p>
 * <ul>
 *   <li>3개 문서 동시 업로드 및 처리</li>
 *   <li>FastAPI OCR 서비스와의 REST 통신</li>
 *   <li>MultipartFile → Resource 변환</li>
 *   <li>파일명 및 Content-Type 유지</li>
 * </ul>
 * 
 * <p>테스트 용도:</p>
 * <pre>
 * POST /test-ocr/call-ocr
 * - invoice_file: 인보이스 문서 파일
 * - packing_list_file: 포장 명세서 파일
 * - bill_of_lading_file: 선하증권 파일
 * </pre>
 * 
 * @author Customs Clearance Team
 * @version 1.0.0
 * @see RestTemplate
 * @see MultipartFile
 * @since 2024-01-01
 */
@RestController
@RequestMapping("/test-ocr")
public class OcrTestController {
    private final RestTemplate restTemplate = new RestTemplate();

    /**
     * FastAPI OCR 서비스 호출 메서드
     * 
     * 세 개의 관세 문서를 동시에 업로드하여 FastAPI OCR 서비스로 전송합니다.
     * MultipartFile을 Resource로 변환하여 HTTP 요청을 전송하고 결과를 반환합니다.
     * 
     * @param invoiceFile 인보이스 문서 파일
     * @param packingListFile 포장 명세서 문서 파일
     * @param billOfLadingFile 선하증권 문서 파일
     * @return OCR 처리 결과를 담은 JSON 응답
     * @throws IOException 파일 읽기 오류 발생 시
     */
    @PostMapping("/call-ocr")
    public ResponseEntity<String> callFastApiOcr(
            @RequestParam("invoice_file") MultipartFile invoiceFile,
            @RequestParam("packing_list_file") MultipartFile packingListFile,
            @RequestParam("bill_of_lading_file") MultipartFile billOfLadingFile
    ) throws IOException {

        // FastAPI OCR 서비스 엔드포인트 URL
        String fastApiUrl = "http://localhost:8001/ocr/";

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

    /**
     * MultipartFile을 Resource로 변환하는 내부 메서드
     * 
     * Spring의 RestTemplate에서 사용할 수 있도록 MultipartFile을 ByteArrayResource로 변환합니다.
     * 원본 파일명과 컨텐츠 크기 정보를 유지하여 전송합니다.
     * 
     * @param file 변환할 MultipartFile 객체
     * @return 변환된 Resource 객체
     * @throws IOException 파일 읽기 오류 발생 시
     */
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
