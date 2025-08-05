package com.customs.clearance.controller;

import com.customs.clearance.dto.DeclarationRequestDto;
import com.customs.clearance.dto.DeclarationResponseDto;
import com.customs.clearance.entity.DeclarationEx;
import com.customs.clearance.service.DeclarationServiceEx;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@WebMvcTest(DeclarationControllerEx.class)
@ActiveProfiles("test")
class DeclarationControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private DeclarationServiceEx declarationService;

    @Autowired
    private ObjectMapper objectMapper;

    private DeclarationRequestDto requestDto;
    private DeclarationResponseDto responseDto;

    @BeforeEach
    void setUp() {
        requestDto = new DeclarationRequestDto();
        requestDto.setDeclarationNumber("TEST001");
        requestDto.setImporterName("Test Importer");
        requestDto.setExporterName("Test Exporter");
        requestDto.setDeclarationDate(LocalDate.now());
        requestDto.setTotalValue(new BigDecimal("1000.00"));
        requestDto.setCurrency("USD");
        requestDto.setDescription("Test declaration");
        requestDto.setCountryOfOrigin("USA");
        requestDto.setPortOfEntry("New York");

        responseDto = new DeclarationResponseDto();
        responseDto.setId(1L);
        responseDto.setDeclarationNumber("TEST001");
        responseDto.setImporterName("Test Importer");
        responseDto.setExporterName("Test Exporter");
        responseDto.setDeclarationDate(LocalDate.now());
        responseDto.setTotalValue(new BigDecimal("1000.00"));
        responseDto.setCurrency("USD");
        responseDto.setStatus(DeclarationEx.DeclarationStatus.PENDING);
        responseDto.setDescription("Test declaration");
        responseDto.setCountryOfOrigin("USA");
        responseDto.setPortOfEntry("New York");
        responseDto.setCreatedAt(LocalDateTime.now());
        responseDto.setUpdatedAt(LocalDateTime.now());
    }

    @Test
    void createDeclaration_ValidRequest_ReturnsCreated() throws Exception {
        when(declarationService.createDeclaration(any(DeclarationRequestDto.class)))
                .thenReturn(responseDto);

        mockMvc.perform(post("/api/v1/declarations")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(requestDto)))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.id").value(1L))
                .andExpect(jsonPath("$.declaration_number").value("TEST001"))
                .andExpect(jsonPath("$.importer_name").value("Test Importer"));
    }

    @Test
    void getDeclarationById_ExistingId_ReturnsDeclaration() throws Exception {
        when(declarationService.getDeclarationById(1L)).thenReturn(responseDto);

        mockMvc.perform(get("/api/v1/declarations/1"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.id").value(1L))
                .andExpect(jsonPath("$.declaration_number").value("TEST001"));
    }

    @Test
    void updateDeclarationStatus_ValidRequest_ReturnsUpdated() throws Exception {
        responseDto.setStatus(DeclarationEx.DeclarationStatus.APPROVED);
        when(declarationService.updateDeclarationStatus(eq(1L), eq(DeclarationEx.DeclarationStatus.APPROVED)))
                .thenReturn(responseDto);

        mockMvc.perform(patch("/api/v1/declarations/1/status")
                        .param("status", "APPROVED"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("APPROVED"));
    }

    @Test
    void createDeclaration_InvalidRequest_ReturnsBadRequest() throws Exception {
        requestDto.setDeclarationNumber(""); // Invalid empty declaration number

        mockMvc.perform(post("/api/v1/declarations")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(requestDto)))
                .andExpect(status().isBadRequest());
    }
}