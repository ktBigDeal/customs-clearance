package com.customs.clearance.util;

import com.customs.clearance.entity.Attachment;
import com.customs.clearance.entity.Declaration;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;

import org.springframework.core.io.ByteArrayResource;
import org.springframework.core.io.Resource;
import org.springframework.web.multipart.MultipartFile;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.util.List;
import java.util.Map;

public class DeclarationServiceUtils {

    public static String saveFile(MultipartFile file, String newFilename, String uploadDir) throws IOException {
        
        File dir = new File(uploadDir);
        if (!dir.exists()) {
            dir.mkdirs();
        }

        String originalExtension = getExtension(file);

        String finalFilename = newFilename + originalExtension;
        File destination = new File(dir, finalFilename);

        try (var input = file.getInputStream(); var output = Files.newOutputStream(destination.toPath())) {
            byte[] buffer = new byte[8192];
            int bytesRead;
            while ((bytesRead = input.read(buffer)) != -1) {
                output.write(buffer, 0, bytesRead);
            }
        }

        return uploadDir + "/" + finalFilename;
    }

    public static String getExtension(MultipartFile file) {
        
        String name = file.getOriginalFilename();

        if (name != null && name.contains(".")) {
            return name.substring(name.lastIndexOf("."));
        }

        return "";
    }

    public static Resource convertToResource(MultipartFile file) throws IOException {

        if (file == null || file.isEmpty()) {
            // 빈 PNG 바이트 배열 (1x1 투명 PNG)
            byte[] emptyPngBytes = new byte[]{
                (byte)0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,
                0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,
                0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
                0x08, 0x06, 0x00, 0x00, 0x00, 0x1F, 0x15, (byte)0xC4,
                (byte)0x89, 0x00, 0x00, 0x00, 0x0A, 0x49, 0x44, 0x41,
                0x54, 0x78, (byte)0x9C, 0x63, 0x00, 0x01, 0x00, 0x00,
                0x05, 0x00, 0x01, (byte)0x0D, 0x0A, 0x2D, (byte)0xB4,
                0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E, 0x44,
                (byte)0xAE, 0x42, 0x60, (byte)0x82
            };

            return new ByteArrayResource(emptyPngBytes) {
                @Override
                public String getFilename() {
                    return "empty.png";
                }

                @Override
                public long contentLength() {
                    return emptyPngBytes.length;
                }
            };
        }

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

    public static void deleteFiles(List<Attachment> attachments, String uploadDir) {
        if (attachments == null || attachments.isEmpty()) {
            return;
        }

        for (Attachment attachment : attachments) {
            // 파일 경로는 상대 경로로 저장돼있으니 절대경로로 변환
            File file = new File(uploadDir, new File(attachment.getFilePath()).getName());

            if (file.exists()) {
                boolean deleted = file.delete();
                if (!deleted) {
                    System.err.println("파일 삭제 실패: " + file.getAbsolutePath());
                }
            }

        }
    }

    public static Map<String, Object> convertDeclarationToMap(Object declaration) {
        
        ObjectMapper mapper = new ObjectMapper();
        mapper.registerModule(new JavaTimeModule());
        mapper.disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS);

        try {
            // 전체 엔티티를 Map으로 변환
            Map<String, Object> declarationMap = mapper.convertValue(declaration, new TypeReference<Map<String, Object>>() {});

            // declarationDetails가 JSON 문자열일 경우 Map으로 변환해서 덮어쓰기
            if (declarationMap.containsKey("declarationDetails")) {

                Object declarationDetails = declarationMap.get("declarationDetails");
                
                Map<String, Object> declarationDetailsMap = mapper.readValue((String) declarationDetails, new TypeReference<Map<String, Object>>() {});
                declarationMap.put("declarationDetails", declarationDetailsMap);
            }

            return declarationMap;

        } catch (JsonProcessingException e) {
            throw new RuntimeException("declaration -> json 파싱 오류", e);
        }
    }

    public static Declaration convertMapToDeclaration(Map<String, Object> map, Declaration declaration) {
        
        ObjectMapper mapper = new ObjectMapper();

        if (map.containsKey("declarationDetails")) {

            Object declarationDetails = map.get("declarationDetails");

            try {
                
                String json = mapper.writeValueAsString(declarationDetails);

                declaration.setDeclarationDetails(json);

            } catch (JsonProcessingException e) {
                throw new RuntimeException("json -> declarationDetails 파싱 오류", e);
            }
        }

        return declaration;
    }

}
