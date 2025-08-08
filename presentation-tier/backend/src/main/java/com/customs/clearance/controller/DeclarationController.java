package com.customs.clearance.controller;

import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import com.customs.clearance.entity.Declaration;
import com.customs.clearance.service.DeclarationService;

import jakarta.servlet.http.HttpServletRequest;
import lombok.RequiredArgsConstructor;

import java.io.IOException;
import java.util.List;
import java.util.Map;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.PathVariable;


@RestController
@RequestMapping("/declaration")
@RequiredArgsConstructor
public class DeclarationController {

    private final DeclarationService declarationService;

    @PostMapping
    public Declaration postDeclaration(
        @ModelAttribute Declaration declaration,
        @RequestPart(value = "invoice_file", required = false) MultipartFile invoiceFile,
        @RequestPart(value = "packing_list_file", required = false) MultipartFile packingListFile,
        @RequestPart(value = "bill_of_lading_file", required = false) MultipartFile billOfLadingFile,
        @RequestPart(value = "certificate_of_origin_file", required = false) MultipartFile certificateOfOriginFile,
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

    @GetMapping("/user/{userId}")
    public List<Declaration> getUserDeclarationList(
        @PathVariable Long userId,
        HttpServletRequest request
    ) {
        
        String authHeader = request.getHeader("Authorization");
        String token = null;
        
        if (authHeader != null && authHeader.startsWith("Bearer ")) {
            token = authHeader.substring(7);
        }

        return declarationService.getDeclarationList(userId, null, token);
    }

    @GetMapping("/user/{userId}/{status}")
    public List<Declaration> getUserDeclarationListByStatus(
        @PathVariable Long userId,
        @PathVariable String status,
        HttpServletRequest request
    ) {
        
        String authHeader = request.getHeader("Authorization");
        String token = null;
        
        if (authHeader != null && authHeader.startsWith("Bearer ")) {
            token = authHeader.substring(7);
        }

        return declarationService.getDeclarationList(userId, status, token);
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

        return declarationService.getDeclarationList(null, null, token);
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

        return declarationService.getDeclarationList(null, status, token);
    }

}
