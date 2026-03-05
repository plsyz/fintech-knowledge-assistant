package com.fka.ingestion;

import org.springframework.ai.document.Document;
import org.springframework.ai.reader.pdf.PagePdfDocumentReader;
import org.springframework.ai.transformer.splitter.TokenTextSplitter;
import org.springframework.ai.vectorstore.VectorStore;
import org.springframework.core.io.Resource;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.List;

@Service
public class DocumentIngestionService {

    private final VectorStore vectorStore;

    public DocumentIngestionService(VectorStore vectorStore) {
        this.vectorStore = vectorStore;
    }

    public int ingestPdf(Resource pdfResource, String regulationName) {
        // Step 1: Read PDF - each page becomes a Document
        PagePdfDocumentReader pdfReader = new PagePdfDocumentReader(pdfResource);
        List<Document> documents = pdfReader.get();

        // Step 2: Split into ~300-token chunks
        TokenTextSplitter splitter = new TokenTextSplitter(300, 50, 20, 5000, true);
        List<Document> chunks = splitter.apply(documents);

        // Step 3: Sanitize text (remove null bytes that break PostgreSQL) + tag metadata
        List<Document> sanitizedChunks = new java.util.ArrayList<>();
        for (Document chunk : chunks) {
            String cleanText = chunk.getText().replace("\u0000", "");
            Document sanitized = new Document(cleanText, chunk.getMetadata());
            sanitized.getMetadata().put("regulation", regulationName);
            sanitized.getMetadata().put("source_type", "pdf");
            sanitized.getMetadata().put("ingested_at", Instant.now().toString());
            sanitizedChunks.add(sanitized);
        }

        // Step 4: Store in vector DB (Spring AI auto-embeds via nomic-embed-text)
        vectorStore.add(sanitizedChunks);

        return sanitizedChunks.size();
    }
}
