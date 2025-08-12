package com.customs.clearance.controller;

import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import com.customs.clearance.entity.Attachment;
import com.customs.clearance.entity.Declaration;
import com.customs.clearance.service.DeclarationService;

import jakarta.servlet.http.HttpServletRequest;
import lombok.RequiredArgsConstructor;

import java.io.IOException;
import java.util.List;
import java.util.Map;


@RestController
@RequestMapping("/declaration")
@RequiredArgsConstructor
public class DeclarationController {

    private final DeclarationService declarationService;

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
    public List<Declaration> getAdminDeclarationList(
        HttpServletRequest request
    ) {
        
        String authHeader = request.getHeader("Authorization");
        String token = null;
        
        if (authHeader != null && authHeader.startsWith("Bearer ")) {
            token = authHeader.substring(7);
        }

        return declarationService.getDeclarationList(null, token);
    }

    @GetMapping("/admin/{status}")
    public List<Declaration> getAdminDeclarationListByStatus(
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
}
