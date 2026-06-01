export type ModelConfig = {
  id: number;
  name: string;
  provider: string;
  base_url: string | null;
  masked_api_key: string | null;
  model_name: string;
  temperature: number;
  max_tokens: number;
  is_default: boolean;
  enabled: boolean;
  created_at: string;
  updated_at: string;
};

export type CreateModelConfigPayload = {
  name: string;
  provider: string;
  base_url?: string | null;
  api_key?: string | null;
  model_name: string;
  temperature: number;
  max_tokens: number;
  is_default: boolean;
  enabled: boolean;
};

export type ModelConfigTestResult = {
  success: boolean;
  message: string;
  latency_ms: number;
};
