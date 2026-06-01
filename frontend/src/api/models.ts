import { apiRequest } from "./client";
import type { CreateModelConfigPayload, ModelConfig, ModelConfigTestResult } from "../types/models";

export function listModelConfigs() {
  return apiRequest<ModelConfig[]>("/api/models/configs");
}

export function createModelConfig(payload: CreateModelConfigPayload) {
  return apiRequest<ModelConfig>("/api/models/configs", {
    method: "POST",
    body: payload,
  });
}

export function deleteModelConfig(configId: number) {
  return apiRequest<{ status: string }>(`/api/models/configs/${configId}`, {
    method: "DELETE",
  });
}

export function testModelConfig(configId: number) {
  return apiRequest<ModelConfigTestResult>(`/api/models/configs/${configId}/test`, {
    method: "POST",
  });
}

export function setDefaultModelConfig(configId: number) {
  return apiRequest<ModelConfig>(`/api/models/configs/${configId}/set-default`, {
    method: "POST",
  });
}
