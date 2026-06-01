export type RfpProject = {
  id: number;
  name: string;
  customer_name: string;
  status: string;
  created_at: string;
  updated_at: string;
};

export type CreateProjectPayload = {
  name: string;
  customer_name: string;
  status?: string;
};

export type RfpDocument = {
  id: number;
  project_id: number;
  filename: string;
  content_text: string;
  created_at: string;
};

export type RfpRequirement = {
  id: number;
  project_id: number;
  requirement_code: string;
  category: string;
  content: string;
  priority: string;
  source_page: number | null;
  created_at: string;
};

export type SourceChunk = {
  chunk_id: number;
  content: string;
  score: number;
};

export type MatchStatus = "satisfied" | "partial" | "unsupported";
export type RiskLevel = "low" | "medium" | "high";
export type HumanReviewStatus = "pending" | "confirmed" | "rejected";

export type BidResponse = {
  id: number;
  project_id: number;
  requirement_id: number;
  match_status: MatchStatus;
  response_text: string;
  risk_level: RiskLevel;
  source_chunks: SourceChunk[];
  human_status: HumanReviewStatus;
  human_note: string;
  created_at: string;
  updated_at: string;
};

export type BidResponseUpdatePayload = {
  match_status?: MatchStatus;
  response_text?: string;
  risk_level?: RiskLevel;
  human_status?: HumanReviewStatus;
  human_note?: string;
};

export type RiskReportItem = {
  requirement_id: number;
  requirement_code: string;
  category: string;
  requirement_content: string;
  match_status: MatchStatus;
  risk_level: RiskLevel;
  response_text: string;
  source_chunks: SourceChunk[];
  human_status: HumanReviewStatus;
  human_note: string;
};

export type RiskReport = {
  total_requirements: number;
  satisfied_count: number;
  partial_count: number;
  unsupported_count: number;
  low_risk_count: number;
  medium_risk_count: number;
  high_risk_count: number;
  pending_review_count: number;
  confirmed_count: number;
  rejected_count: number;
  risk_items: RiskReportItem[];
  pending_confirmation_items: RiskReportItem[];
};
