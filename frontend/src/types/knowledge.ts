export type KnowledgeFile = {
  id: number;
  filename: string;
  content_text: string;
  status: string;
  created_at: string;
};

export type KnowledgeChunk = {
  id: number;
  file_id: number;
  chunk_index: number;
  content: string;
  metadata_json: Record<string, unknown>;
  created_at: string;
};

export type RetrievedChunk = {
  chunk_id: number;
  file_id: number;
  content: string;
  score: number;
  metadata: Record<string, unknown>;
  retriever_type: string;
};
