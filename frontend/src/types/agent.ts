export type AgentRun = {
  id: number;
  project_id: number;
  run_type: string;
  status: string;
  steps_json: Record<string, unknown>;
  error_message: string | null;
  created_at: string;
  finished_at: string | null;
};
