package com.customs.clearance.controller;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import com.customs.clearance.entity.Attachment;
import com.customs.clearance.entity.Declaration;
import com.customs.clearance.dto.DeclarationAdminDto;
import com.customs.clearance.service.DeclarationService;
import com.customs.clearance.util.DeclarationServiceUtils;

import jakarta.servlet.http.HttpServletRequest;
import lombok.RequiredArgsConstructor;

import java.io.File;
import java.io.IOException;
import java.util.List;
import java.util.Map;
import java.util.Arrays;
import java.util.HashMap;

import com.customs.clearance.dto.DeclarationStatsDto;


@RestController
@RequestMapping("/declaration")
@RequiredArgsConstructor
public class DeclarationController {

    private final DeclarationService declarationService;

    @Value("${customs.clearance.file.upload-dir}")
    private String uploadDir;

    @PostMapping(value = "/test", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public String testFileUpload(
        @RequestParam("invoiceFile") MultipartFile invoiceFile
    ) throws IOException {
        if (invoiceFile == null || invoiceFile.isEmpty()) {
            throw new IllegalArgumentException("파일이 비어있습니다.");
        }

        String path = DeclarationServiceUtils.saveFile(invoiceFile, "test", uploadDir);
        return path;
    }

    @DeleteMapping("test")
    public boolean testFileDelete(
        @RequestParam String filename
    ) throws IOException {

        File file = new File(uploadDir, filename);

        boolean deleted = false;
        if (file.exists()) {
            deleted = file.delete();

            if (!deleted) {
                System.err.println("파일 삭제 실패: " + file.getAbsolutePath());
            }
        }

        return deleted;
    }

    @GetMapping("/test")
    public List<String> listFiles() {
        File dir = new File(uploadDir);
        if (!dir.exists() || dir.listFiles() == null) {
            return List.of("업로드 디렉토리가 비어있거나 존재하지 않습니다.");
        }
        return Arrays.stream(dir.listFiles())
                    .map(File::getName)
                    .toList();
    }

    @PostMapping
    public Declaration postDeclaration(
        @ModelAttribute Declaration declaration,
        @RequestPart(value = "invoiceFile", required = false) MultipartFile invoiceFile,
        @RequestPart(value = "packingListFile", required = false) MultipartFile packingListFile,
        @RequestPart(value = "billOfLadingFile", required = false) MultipartFile billOfLadingFile,
        @RequestPart(value = "certificateOfOriginFile", required = false) MultipartFile certificateOfOriginFile,
        HttpServletRequest request
    ) throws IOException {

        String authHeader = request.getHeader("Authorization");
        String token = null;
        
        if (authHeader != null && authHeader.startsWith("Bearer ")) {
            token = authHeader.substring(7);
        }

        return declarationService.postDeclaration(declaration, invoiceFile, packingListFile, billOfLadingFile, certificateOfOriginFile, token);
    }

    @GetMapping("/{declarationId}")
    public Map<String, Object> getDeclaration(
        @PathVariable Long declarationId,
        HttpServletRequest request
    ) throws IOException {
        
        String authHeader = request.getHeader("Authorization");
        String token = null;
        
        if (authHeader != null && authHeader.startsWith("Bearer ")) {
            token = authHeader.substring(7);
        }

        return declarationService.getDeclaration(declarationId, token);
    }

    @PutMapping("/{declarationId}")
    public Map<String, Object> putDeclaration(
        @PathVariable Long declarationId, 
        @RequestBody Map<String, Object> declarationMap,
        HttpServletRequest request
    ) {

        String authHeader = request.getHeader("Authorization");
        String token = null;
        
        if (authHeader != null && authHeader.startsWith("Bearer ")) {
            token = authHeader.substring(7);
        }
        
        return declarationService.putDeclaration(declarationId, declarationMap, token);
    }

    @DeleteMapping("/{declarationId}")
    public boolean deleteDeclaration(
        @PathVariable Long declarationId,
        HttpServletRequest request
    ) {

        String authHeader = request.getHeader("Authorization");
        String token = null;
        
        if (authHeader != null && authHeader.startsWith("Bearer ")) {
            token = authHeader.substring(7);
        }
        
        return declarationService.deleteDeclaration(declarationId, token);
    }

    @GetMapping("/user")
    public List<Declaration> getUserDeclarationList(
        HttpServletRequest request
    ) {
        
        String authHeader = request.getHeader("Authorization");
        String token = null;
        
        if (authHeader != null && authHeader.startsWith("Bearer ")) {
            token = authHeader.substring(7);
        }

        return declarationService.getDeclarationList(null, token);
    }

    @GetMapping("/user/{status}")
    public List<Declaration> getUserDeclarationListByStatus(
        @PathVariable String status,
        HttpServletRequest request
    ) {
        
        String authHeader = request.getHeader("Authorization");
        String token = null;
        
        if (authHeader != null && authHeader.startsWith("Bearer ")) {
            token = authHeader.substring(7);
        }

        return declarationService.getDeclarationList(status, token);
    }

    @GetMapping("/admin")
    public List<DeclarationAdminDto> getAdminDeclarationList(
        HttpServletRequest request
    ) {
        
        String authHeader = request.getHeader("Authorization");
        String token = null;
        
        if (authHeader != null && authHeader.startsWith("Bearer ")) {
            token = authHeader.substring(7);
        }

        return declarationService.getAdminDeclarationList(null, token);
    }

    @GetMapping("/admin/{status}")
    public List<DeclarationAdminDto> getAdminDeclarationListByStatus(
        @PathVariable String status,
        HttpServletRequest request
    ) {
        
        String authHeader = request.getHeader("Authorization");
        String token = null;
        
        if (authHeader != null && authHeader.startsWith("Bearer ")) {
            token = authHeader.substring(7);
        }

        return declarationService.getAdminDeclarationList(status, token);
    }

    @GetMapping("/attachment/{declarationId}")
    public List<Attachment> getAttachmentListByDeclaration(
        @PathVariable Long declarationId,
        HttpServletRequest request
    ) {
        
        String authHeader = request.getHeader("Authorization");
        String token = null;
        
        if (authHeader != null && authHeader.startsWith("Bearer ")) {
            token = authHeader.substring(7);
        }

        return declarationService.getAttachmentListByDeclaration(declarationId, token);
    }

    @GetMapping("/attachment/user")
    public List<Attachment> getAttachmentListByUser(
        HttpServletRequest request
    ) {
        
        String authHeader = request.getHeader("Authorization");
        String token = null;
        
        if (authHeader != null && authHeader.startsWith("Bearer ")) {
            token = authHeader.substring(7);
        }

        return declarationService.getAttachmentListByUser(token);
    }

    @GetMapping("/attachment/admin")
    public List<Attachment> getAttachmentListByAdmin(
        HttpServletRequest request
    ) {
        
        String authHeader = request.getHeader("Authorization");
        String token = null;
        
        if (authHeader != null && authHeader.startsWith("Bearer ")) {
            token = authHeader.substring(7);
        }

        return declarationService.getAttachmentListByAdmin(token);
    }

    @GetMapping("/{declarationId}/xml")
    public ResponseEntity<byte[]> downloadKcsXml(
            @PathVariable Long declarationId,
            @RequestParam(value="docType", required = false) String docType,
            HttpServletRequest request
    ) {
        String authHeader = request.getHeader("Authorization");
        String token = (authHeader != null && authHeader.startsWith("Bearer "))
                ? authHeader.substring(7) : null;

        byte[] xml = declarationService.generateKcsXml(declarationId, docType, token);

        String fileName = (docType == null ? "declaration" : docType) + "-" + declarationId + ".xml";
        return ResponseEntity.ok()
                .contentType(MediaType.APPLICATION_XML)
                .header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=" + fileName)
                .body(xml);
    }

    /**
     * 대시보드용 통계 데이터 조회
     */
    @GetMapping("/stats")
    public DeclarationStatsDto getDeclarationStats(HttpServletRequest request) {
        String authHeader = request.getHeader("Authorization");
        String token = null;
        
        if (authHeader != null && authHeader.startsWith("Bearer ")) {
            token = authHeader.substring(7);
        }

        return declarationService.getDeclarationStats(token);
    }

    /**
     * 대시보드용 최근 신고서 목록 조회
     */
    @GetMapping("/recent")
    public List<Declaration> getRecentDeclarations(
            @RequestParam(value = "limit", defaultValue = "5") int limit,
            HttpServletRequest request) {
        String authHeader = request.getHeader("Authorization");
        String token = null;
        
        if (authHeader != null && authHeader.startsWith("Bearer ")) {
            token = authHeader.substring(7);
        }

        return declarationService.getRecentDeclarations(limit, token);
    }

    /**
     * 대시보드용 차트 데이터 조회
     */
    @GetMapping("/chart-data")
    public Map<String, Object> getDashboardChartData(HttpServletRequest request) {
        String authHeader = request.getHeader("Authorization");
        String token = null;
        
        if (authHeader != null && authHeader.startsWith("Bearer ")) {
            token = authHeader.substring(7);
        }

        return declarationService.getDashboardChartData(token);
    }

    /**
     * 대시보드용 처리 시간 통계 조회
     */
    @GetMapping("/processing-time")
    public Map<String, Object> getProcessingTimeStats(HttpServletRequest request) {
        String authHeader = request.getHeader("Authorization");
        String token = null;
        
        if (authHeader != null && authHeader.startsWith("Bearer ")) {
            token = authHeader.substring(7);
        }

        Map<String, Object> result = new HashMap<>();
        // 임시 데이터 (실제 구현시 서비스에서 계산)
        result.put("thisMonth", 2.3);
        result.put("lastMonth", 2.8);
        result.put("improvement", 18);
        result.put("trend", "down");
        
        return result;
    }
}
