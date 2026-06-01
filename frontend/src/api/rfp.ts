import { API_BASE_URL, apiRequest, uploadFile } from "./client";
import type {
  BidResponse,
  BidResponseUpdatePayload,
  CreateProjectPayload,
  RiskReport,
  RfpDocument,
  RfpProject,
  RfpRequirement,
} from "../types/rfp";

export function listProjects() {
  return apiRequest<RfpProject[]>("/api/rfp/projects");
}

export function createProject(payload: CreateProjectPayload) {
  return apiRequest<RfpProject>("/api/rfp/projects", {
    method: "POST",
    body: payload,
  });
}

export function getProject(projectId: number) {
  return apiRequest<RfpProject>(`/api/rfp/projects/${projectId}`);
}

export function uploadRfpDocument(projectId: number, file: File) {
  return uploadFile<RfpDocument>(`/api/rfp/projects/${projectId}/documents/upload`, file);
}

export function listProjectDocuments(projectId: number) {
  return apiRequest<RfpDocument[]>(`/api/rfp/projects/${projectId}/documents`);
}

export function extractRequirements(projectId: number) {
  return apiRequest<RfpRequirement[]>(`/api/rfp/projects/${projectId}/extract-requirements`, {
    method: "POST",
  });
}

export function listRequirements(projectId: number) {
  return apiRequest<RfpRequirement[]>(`/api/rfp/projects/${projectId}/requirements`);
}

export function generateResponses(projectId: number) {
  return apiRequest<BidResponse[]>(`/api/rfp/projects/${projectId}/generate-responses`, {
    method: "POST",
  });
}

export function listResponses(projectId: number) {
  return apiRequest<BidResponse[]>(`/api/rfp/projects/${projectId}/responses`);
}

export function updateResponse(projectId: number, responseId: number, payload: BidResponseUpdatePayload) {
  return apiRequest<BidResponse>(`/api/rfp/projects/${projectId}/responses/${responseId}`, {
    method: "PATCH",
    body: payload,
  });
}

export function getRiskReport(projectId: number) {
  return apiRequest<RiskReport>(`/api/rfp/projects/${projectId}/risk-report`);
}

export async function downloadResponsesCsv(projectId: number) {
  return downloadProjectFile(`/api/rfp/projects/${projectId}/responses/export-csv`, `bidpilot_${projectId}_responses.csv`);
}

export async function downloadResponsesXlsx(projectId: number) {
  return downloadProjectFile(`/api/rfp/projects/${projectId}/responses/export-xlsx`, `bidpilot_${projectId}_responses.xlsx`);
}

export async function downloadProposalDocx(projectId: number) {
  return downloadProjectFile(`/api/rfp/projects/${projectId}/proposal/export-docx`, `bidpilot_${projectId}_proposal.docx`);
}

async function downloadProjectFile(path: string, fallbackFilename: string) {
  const response = await fetch(`${API_BASE_URL}${path}`);
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`);
  }
  const blob = await response.blob();
  const filename = parseFilename(response.headers.get("content-disposition")) ?? fallbackFilename;
  return { blob, filename };
}

function parseFilename(contentDisposition: string | null) {
  if (!contentDisposition) return null;
  const encodedMatch = contentDisposition.match(/filename\*=UTF-8''([^;]+)/);
  if (encodedMatch) {
    return decodeURIComponent(encodedMatch[1]);
  }
  const plainMatch = contentDisposition.match(/filename="?([^";]+)"?/);
  return plainMatch?.[1] ?? null;
}
