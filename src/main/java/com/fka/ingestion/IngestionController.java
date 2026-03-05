package com.fka.ingestion;

import org.springframework.core.io.ByteArrayResource;
import org.springframework.core.io.Resource;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.util.Map;

@RestController
@RequestMapping("/api/ingest")
public class IngestionController {

    private final DocumentIngestionService ingestionService;

    public IngestionController(DocumentIngestionService ingestionService) {
        this.ingestionService = ingestionService;
    }

    @PostMapping("/pdf")
    public Map<String, Object> ingestPdf(
            @RequestParam("file") MultipartFile file,
            @RequestParam("regulation") String regulation) throws IOException {

        Resource resource = new ByteArrayResource(file.getBytes());
        int chunksCreated = ingestionService.ingestPdf(resource, regulation);

        return Map.of(
                "status", "success",
                "chunks_created", chunksCreated,
                "regulation", regulation
        );
    }
}
