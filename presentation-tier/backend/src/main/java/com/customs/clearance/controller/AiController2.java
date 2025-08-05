package com.customs.clearance.controller;

import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import com.customs.clearance.entity.Declaration;
import com.customs.clearance.service.AiService2;

import lombok.RequiredArgsConstructor;

import java.io.IOException;

@RestController
@RequestMapping("/ai")
@RequiredArgsConstructor
public class AiController2 {

    private final AiService2 aiService;

    @PostMapping("/analyze-documents")
    public Declaration insertDeclaration(
            @ModelAttribute Declaration declaration,
            @RequestPart("invoice_file") MultipartFile invoiceFile,
            @RequestPart("packing_list_file") MultipartFile packingListFile,
            @RequestPart("bill_of_lading_file") MultipartFile billOfLadingFile,
            @RequestPart("certificate_of_origin_file") MultipartFile certificateOfOriginFile
    ) throws IOException {

        Declaration result = aiService.analyzeDocuments(declaration, invoiceFile, packingListFile, billOfLadingFile, certificateOfOriginFile);

        return result;
    }

}
