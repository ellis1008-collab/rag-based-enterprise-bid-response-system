import { useEffect, useState } from "react";

import { listAgentRuns } from "../api/agentRuns";
import { getProject } from "../api/rfp";
import { StatusBadge } from "../components/Badges";
import { PageHeader } from "../components/PageHeader";
import { EmptyBlock, ErrorBlock, LoadingBlock } from "../components/StateBlock";
import type { AgentRun, RfpProject } from "../types";

type AgentRunsPageProps = {
  projectId: number;
  navigate: (path: string) => void;
};

type TimelineStep = {
  name: string;
  status: string;
  [key: string]: unknown;
};

type RetrievalDetail = {
  requirement_id?: number;
  requirement_code?: string;
  query?: string;
  retrieved_chunks?: RetrievedChunkSummary[];
};

type RetrievedChunkSummary = {
  chunk_id?: number;
  file_id?: number;
  score?: number;
  content_summary?: string;
};

const RUN_TYPE_LABELS: Record<string, string> = {
  extract_requirements: "抽取客户需求",
  generate_responses: "生成响应矩阵",
};

const STEP_NAME_LABELS: Record<string, string> = {
  load_project_context: "加载项目上下文",
  load_rfp_document: "加载招标文件",
  load_requirements: "加载客户需求",
  build_prompt: "构建提示词",
  call_llm: "调用大模型",
  retrieve_knowledge: "检索知识库",
  call_llm_for_each_requirement: "逐条生成技术响应",
  validate_schema: "校验结构化结果",
  save_requirements: "保存客户需求",
  save_bid_responses: "保存响应矩阵",
  build_risk_summary: "生成风险汇总",
  extract_requirements_node: "抽取客户需求节点",
  retrieve_knowledge_node: "知识库检索节点",
  generate_responses_node: "响应生成节点",
  assess_risk_node: "风险评估节点",
  save_results_node: "结果保存节点",
};

const FIELD_LABELS: Record<string, string> = {
  node_name: "节点",
  input_summary: "输入摘要",
  output_summary: "输出摘要",
  latency_ms: "耗时",
  error_message: "错误信息",
  requirement_count: "需求数",
  document_count: "文档数",
  knowledge_file_count: "知识库文件数",
  rfp_chars: "招标文件字符数",
  total_chars: "总字符数",
  prompt_chars: "提示词字符数",
  prompt_type: "提示词类型",
  schema: "结构化结果",
  call_count: "调用次数",
  generated_response_count: "生成响应数",
  response_count: "响应数",
  saved_requirements: "保存需求数",
  saved_responses: "保存响应数",
  retrieved_chunk_count: "召回片段数",
  retrieval_count: "检索次数",
  retriever_types: "检索方式",
  risk_summary: "风险统计",
  risk_level_counts: "风险等级统计",
  low: "低风险",
  medium: "中风险",
  high: "高风险",
  project_id: "项目 ID",
  run_type: "运行类型",
  top_k: "召回数量",
  filenames: "文件名",
};

const VALUE_LABELS: Record<string, string> = {
  ...RUN_TYPE_LABELS,
  ...STEP_NAME_LABELS,
  completed: "已完成",
  succeeded: "成功",
  running: "运行中",
  failed: "失败",
  "-": "无",
  simple: "简单检索",
  chroma: "向量检索（Chroma）",
  generate_response: "生成单条响应",
  RequirementExtractionResult: "需求抽取结构",
  BidResponseGenerationResult: "响应矩阵结构",
};

export function AgentRunsPage({ projectId, navigate }: AgentRunsPageProps) {
  const [project, setProject] = useState<RfpProject | null>(null);
  const [runs, setRuns] = useState<AgentRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [projectData, runData] = await Promise.all([getProject(projectId), listAgentRuns(projectId)]);
        if (mounted) {
          setProject(projectData);
          setRuns(runData);
        }
      } catch (err) {
        if (mounted) {
          setError(err instanceof Error ? err.message : "运行记录加载失败");
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }
    load();
    return () => {
      mounted = false;
    };
  }, [projectId]);

  return (
    <>
      <PageHeader
        title={project ? `${formatProjectName(project.name)} · 智能体运行记录` : "智能体运行记录"}
        actions={
          <>
            <button className="btn-secondary" type="button" onClick={() => navigate(`/projects/${projectId}`)}>
              项目详情
            </button>
            <button className="btn-primary" type="button" onClick={() => navigate(`/projects/${projectId}/responses`)}>
              响应矩阵
            </button>
          </>
        }
      />
      {loading ? <LoadingBlock title="加载运行记录" /> : null}
      {error ? <ErrorBlock title="运行记录加载失败" body={error} /> : null}
      {!loading && !error ? (
        <section className="rounded-md border border-bidpilot-line bg-white">
          <div className="border-b border-bidpilot-line px-5 py-4 text-sm font-semibold">运行记录</div>
          <div className="p-5">
            {runs.length === 0 ? (
              <EmptyBlock title="暂无运行记录" body="执行需求抽取或生成响应矩阵后会产生记录。" />
            ) : (
              <div className="space-y-5">
                {runs.map((run) => (
                  <RunCard key={run.id} run={run} />
                ))}
              </div>
            )}
          </div>
        </section>
      ) : null}
    </>
  );
}

function RunCard({ run }: { run: AgentRun }) {
  const steps = getSteps(run);
  return (
    <article className="rounded-md border border-bidpilot-line p-4">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-3">
          <span className="font-medium text-slate-900">{formatRunType(run.run_type)}</span>
          <StatusBadge value={run.status} />
          <span className="text-xs text-slate-500">{formatDate(run.created_at)}</span>
        </div>
        <span className="rounded bg-slate-100 px-2 py-1 text-xs font-medium text-slate-600">
          耗时 {formatDuration(run.created_at, run.finished_at)}
        </span>
      </div>

      <ol className="relative space-y-4 border-l border-bidpilot-line pl-5">
        {steps.map((step, index) => (
          <li key={`${step.name}-${index}`} className="relative">
            <span className={`absolute -left-[29px] mt-1 h-3 w-3 rounded-full border-2 ${stepDotClass(step.status)}`} />
            <div className="rounded-md border border-bidpilot-line bg-slate-50 p-3">
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-sm font-semibold text-slate-900">{formatStepName(step.name)}</span>
                <span className={`rounded px-2 py-0.5 text-xs font-medium ${stepStatusClass(step.status)}`}>
                  {formatStatusLabel(step.status)}
                </span>
              </div>
              <StepMeta step={step} />
              {step.name === "retrieve_knowledge" ? <RetrievalDetails step={step} /> : null}
            </div>
          </li>
        ))}
      </ol>

      {run.error_message ? <div className="mt-4 rounded bg-red-50 p-3 text-sm text-red-700">{run.error_message}</div> : null}

      <details className="mt-4">
        <summary className="cursor-pointer text-sm font-medium text-slate-600">查看原始调试数据</summary>
        <pre className="mt-3 max-h-64 overflow-auto rounded bg-slate-950 p-3 text-xs leading-5 text-slate-100">
          {JSON.stringify(run.steps_json, null, 2)}
        </pre>
      </details>
    </article>
  );
}

function StepMeta({ step }: { step: TimelineStep }) {
  const hiddenKeys = new Set(["name", "status", "retrievals"]);
  const entries = Object.entries(step).filter(([key]) => !hiddenKeys.has(key));
  if (entries.length === 0) return null;

  return (
    <div className="mt-2 flex flex-wrap gap-2">
      {entries.map(([key, value]) => (
        <span key={key} className="rounded border border-bidpilot-line bg-white px-2 py-1 text-xs text-slate-600">
          {formatFieldLabel(key)}: {formatMetaValue(key, value)}
        </span>
      ))}
    </div>
  );
}

function RetrievalDetails({ step }: { step: TimelineStep }) {
  const retrievals = Array.isArray(step.retrievals) ? (step.retrievals as RetrievalDetail[]) : [];
  if (retrievals.length === 0) return null;

  return (
    <details className="mt-3">
      <summary className="cursor-pointer text-sm font-medium text-teal-700">查看检索词与召回片段</summary>
      <div className="mt-3 space-y-3">
        {retrievals.map((item, index) => (
          <div key={`${item.requirement_id ?? index}-${index}`} className="rounded border border-teal-100 bg-white p-3">
            <div className="text-xs font-semibold text-teal-700">
              {item.requirement_code ?? `需求 ${item.requirement_id ?? index + 1}`}
            </div>
            <div className="mt-1 text-sm text-slate-700">检索词：{item.query ?? "-"}</div>
            <div className="mt-2 space-y-2">
              {(item.retrieved_chunks ?? []).map((chunk, chunkIndex) => (
                <div key={`${chunk.chunk_id ?? chunkIndex}-${chunkIndex}`} className="rounded bg-slate-50 p-2 text-xs text-slate-600">
                  <div className="font-semibold">
                    片段 #{chunk.chunk_id ?? "-"} · 匹配分 {chunk.score ?? "-"}
                  </div>
                  <div className="mt-1 leading-5">{chunk.content_summary ?? "-"}</div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </details>
  );
}

function getSteps(run: AgentRun): TimelineStep[] {
  const steps = run.steps_json.steps;
  if (!Array.isArray(steps)) return [];
  return steps.filter(isTimelineStep);
}

function isTimelineStep(value: unknown): value is TimelineStep {
  if (!value || typeof value !== "object") return false;
  const candidate = value as Record<string, unknown>;
  return typeof candidate.name === "string" && typeof candidate.status === "string";
}

function stepDotClass(status: string) {
  if (status === "completed") return "border-emerald-600 bg-emerald-100";
  if (status === "failed") return "border-red-600 bg-red-100";
  if (status === "running") return "border-sky-600 bg-sky-100";
  return "border-slate-300 bg-white";
}

function stepStatusClass(status: string) {
  if (status === "completed") return "bg-emerald-50 text-emerald-700";
  if (status === "failed") return "bg-red-50 text-red-700";
  if (status === "running") return "bg-sky-50 text-sky-700";
  return "bg-slate-100 text-slate-600";
}

function formatStepName(name: string) {
  return STEP_NAME_LABELS[name] ?? name.replace(/_/g, " ");
}

function formatRunType(value: string) {
  return RUN_TYPE_LABELS[value] ?? value;
}

function formatStatusLabel(status: string) {
  return VALUE_LABELS[status] ?? status;
}

function formatFieldLabel(key: string) {
  return FIELD_LABELS[key] ?? key.replace(/_/g, " ");
}

function formatMetaValue(key: string, value: unknown): string {
  if (key === "latency_ms" && typeof value === "number") return `${value}ms`;
  return formatValue(value);
}

function formatValue(value: unknown): string {
  if (value === null || value === undefined) return "无";
  if (typeof value === "string") return VALUE_LABELS[value] ?? value;
  if (typeof value === "number") return String(value);
  if (typeof value === "boolean") return value ? "是" : "否";
  if (Array.isArray(value)) return value.length > 0 ? value.map(formatValue).join("、") : "无";
  if (typeof value === "object") {
    return Object.entries(value as Record<string, unknown>)
      .map(([key, nestedValue]) => `${formatFieldLabel(key)}: ${formatValue(nestedValue)}`)
      .join("，");
  }
  return String(value);
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("zh-CN", { dateStyle: "short", timeStyle: "short" }).format(new Date(value));
}

function formatDuration(start: string, end: string | null) {
  if (!end) return "进行中";
  const durationMs = Math.max(0, new Date(end).getTime() - new Date(start).getTime());
  if (durationMs < 1000) return `${durationMs}ms`;
  return `${(durationMs / 1000).toFixed(1)}s`;
}

function formatProjectName(name: string) {
  return name
    .replace(/^Prompt template e2e/i, "提示词模板端到端测试")
    .replace(/^Deliverable e2e/i, "交付物端到端测试")
    .replace(/^Human review e2e/i, "人工复核端到端测试");
}
