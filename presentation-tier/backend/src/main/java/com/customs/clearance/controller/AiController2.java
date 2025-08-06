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

    @PostMapping("/insertDeclaration")
    public Declaration insertDeclaration(
        @ModelAttribute Declaration declaration,
        @RequestPart(value = "invoice_file", required = false) MultipartFile invoiceFile,
        @RequestPart(value = "packing_list_file", required = false) MultipartFile packingListFile,
        @RequestPart(value = "bill_of_lading_file", required = false) MultipartFile billOfLadingFile,
        @RequestPart(value = "certificate_of_origin_file", required = false) MultipartFile certificateOfOriginFile
    ) throws IOException {

        return aiService.insertDeclaration(declaration, invoiceFile, packingListFile, billOfLadingFile, certificateOfOriginFile);

    }

}
