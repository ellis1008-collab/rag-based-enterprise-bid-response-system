import { apiRequest } from "./client";
import type { AgentRun } from "../types/agent";

export function listAgentRuns(projectId: number) {
  return apiRequest<AgentRun[]>(`/api/rfp/projects/${projectId}/runs`);
}
