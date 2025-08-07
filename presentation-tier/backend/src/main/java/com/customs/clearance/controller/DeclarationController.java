package com.customs.clearance.controller;

import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import com.customs.clearance.entity.Declaration;
import com.customs.clearance.service.DeclarationService;

import jakarta.servlet.http.HttpServletRequest;
import lombok.RequiredArgsConstructor;

import java.io.IOException;

@RestController
@RequestMapping("/declaration")
@RequiredArgsConstructor
public class DeclarationController {

    private final DeclarationService aiService;

    @PostMapping
    public Declaration insertDeclaration(
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

        return aiService.insertDeclaration(declaration, invoiceFile, packingListFile, billOfLadingFile, certificateOfOriginFile, token);
    }

}
