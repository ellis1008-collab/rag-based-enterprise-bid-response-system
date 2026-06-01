import { apiRequest, uploadFile } from "./client";
import type { KnowledgeChunk, KnowledgeFile, RetrievedChunk } from "../types/knowledge";

export function uploadKnowledgeFile(file: File) {
  return uploadFile<KnowledgeFile>("/api/knowledge/upload", file);
}

export function listKnowledgeFiles() {
  return apiRequest<KnowledgeFile[]>("/api/knowledge/files");
}

export function listKnowledgeChunks(fileId: number) {
  return apiRequest<KnowledgeChunk[]>(`/api/knowledge/files/${fileId}/chunks`);
}

export function retrieveKnowledge(query: string, topK = 5) {
  return apiRequest<RetrievedChunk[]>("/api/knowledge/retrieve", {
    method: "POST",
    body: { query, top_k: topK },
  });
}
