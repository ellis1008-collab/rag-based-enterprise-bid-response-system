import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";

import {
  downloadProposalDocx,
  downloadResponsesCsv,
  downloadResponsesXlsx,
  generateResponses,
  getProject,
  getRiskReport,
  listRequirements,
  listResponses,
  updateResponse,
} from "../api/rfp";
import { HumanStatusBadge, MatchBadge, RiskBadge } from "../components/Badges";
import { PageHeader } from "../components/PageHeader";
import { EmptyBlock, ErrorBlock, LoadingBlock } from "../components/StateBlock";
import type { BidResponse, HumanReviewStatus, MatchStatus, RiskLevel, RiskReport, RfpProject, RfpRequirement } from "../types/rfp";

type ResponseMatrixPageProps = {
  projectId: number;
  navigate: (path: string) => void;
};

type EditForm = {
  match_status: MatchStatus;
  risk_level: RiskLevel;
  response_text: string;
  human_status: HumanReviewStatus;
  human_note: string;
};

type ExportKind = "csv" | "xlsx" | "docx";

export function ResponseMatrixPage({ projectId, navigate }: ResponseMatrixPageProps) {
  const [project, setProject] = useState<RfpProject | null>(null);
  const [requirements, setRequirements] = useState<RfpRequirement[]>([]);
  const [responses, setResponses] = useState<BidResponse[]>([]);
  const [riskReport, setRiskReport] = useState<RiskReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [exporting, setExporting] = useState<ExportKind | null>(null);
  const [editingResponse, setEditingResponse] = useState<BidResponse | null>(null);
  const [editForm, setEditForm] = useState<EditForm | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const requirementById = useMemo(() => new Map(requirements.map((item) => [item.id, item])), [requirements]);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const [projectData, requirementData, responseData, reportData] = await Promise.all([
        getProject(projectId),
        listRequirements(projectId),
        listResponses(projectId),
        getRiskReport(projectId),
      ]);
      setProject(projectData);
      setRequirements(requirementData);
      setResponses(responseData);
      setRiskReport(reportData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "响应矩阵加载失败");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [projectId]);

  async function handleGenerate() {
    setGenerating(true);
    setError(null);
    try {
      setResponses(await generateResponses(projectId));
      setRiskReport(await getRiskReport(projectId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "响应矩阵生成失败");
    } finally {
      setGenerating(false);
    }
  }

  async function handleExport(kind: ExportKind) {
    setExporting(kind);
    setError(null);
    try {
      const { blob, filename } =
        kind === "csv"
          ? await downloadResponsesCsv(projectId)
          : kind === "xlsx"
            ? await downloadResponsesXlsx(projectId)
            : await downloadProposalDocx(projectId);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "文件导出失败");
    } finally {
      setExporting(null);
    }
  }

  function openEdit(response: BidResponse) {
    setEditingResponse(response);
    setEditForm({
      match_status: response.match_status,
      risk_level: response.risk_level,
      response_text: response.response_text,
      human_status: response.human_status,
      human_note: response.human_note,
    });
  }

  async function handleSaveEdit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!editingResponse || !editForm) return;

    setSaving(true);
    setError(null);
    try {
      const updated = await updateResponse(projectId, editingResponse.id, editForm);
      setResponses((current) => current.map((item) => (item.id === updated.id ? updated : item)));
      setRiskReport(await getRiskReport(projectId));
      setEditingResponse(null);
      setEditForm(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "响应复核保存失败");
    } finally {
      setSaving(false);
    }
  }

  const hasPendingConfirmation = (riskReport?.pending_confirmation_items.length ?? 0) > 0;

  return (
    <>
      <PageHeader
        title={project ? `${formatProjectName(project.name)} · 响应矩阵` : "响应矩阵"}
        actions={
          <>
            <button className="btn-secondary" type="button" onClick={() => navigate(`/projects/${projectId}`)}>
              项目详情
            </button>
            <button className="btn-secondary" type="button" onClick={() => navigate(`/projects/${projectId}/runs`)}>
              运行记录
            </button>
            <button className="btn-secondary" type="button" disabled={responses.length === 0 || exporting !== null} onClick={() => handleExport("csv")}>
              {exporting === "csv" ? "导出中..." : "导出 CSV"}
            </button>
            <button className="btn-secondary" type="button" disabled={responses.length === 0 || exporting !== null} onClick={() => handleExport("xlsx")}>
              {exporting === "xlsx" ? "导出中..." : "导出 Excel"}
            </button>
            <button className="btn-secondary" type="button" disabled={responses.length === 0 || exporting !== null} onClick={() => handleExport("docx")}>
              {exporting === "docx" ? "导出中..." : "导出 Word 初稿"}
            </button>
            <button className="btn-primary" type="button" disabled={generating} onClick={handleGenerate}>
              {generating ? "生成中..." : "生成响应矩阵"}
            </button>
          </>
        }
      />
      {loading ? <LoadingBlock title="加载响应矩阵" /> : null}
      {error ? <ErrorBlock title="响应矩阵操作失败" body={error} /> : null}
      {!loading ? (
        <div className="space-y-6">
          {riskReport ? <RiskSummaryCards report={riskReport} /> : null}
          {hasPendingConfirmation ? (
            <div className="rounded-md border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
              需要售前人工确认：{riskReport?.pending_confirmation_items.length} 项响应缺少引用来源。
            </div>
          ) : null}
          {riskReport && riskReport.risk_items.length > 0 ? (
            <section className="rounded-md border border-amber-200 bg-white">
              <div className="border-b border-amber-200 bg-amber-50 px-5 py-4 text-sm font-semibold text-amber-900">
                风险项
              </div>
              <div className="grid gap-3 p-5 lg:grid-cols-2">
                {riskReport.risk_items.map((item) => (
                  <div key={item.requirement_id} className="rounded-md border border-amber-200 bg-amber-50 p-4">
                    <div className="mb-2 flex flex-wrap items-center gap-2">
                      <span className="font-medium text-amber-950">{item.requirement_code}</span>
                      <MatchBadge value={item.match_status} />
                      <RiskBadge value={item.risk_level} />
                    </div>
                    <p className="text-sm leading-6 text-amber-900">{item.requirement_content}</p>
                  </div>
                ))}
              </div>
            </section>
          ) : null}
          <section className="rounded-md border border-bidpilot-line bg-white">
            <div className="border-b border-bidpilot-line px-5 py-4 text-sm font-semibold">响应矩阵表格</div>
            <div className="p-5">
              {responses.length === 0 ? (
                <EmptyBlock title="暂无响应矩阵" body="抽取需求并维护知识库后可生成。" />
              ) : (
                <div className="overflow-x-auto rounded-md border border-bidpilot-line">
                  <table className="data-table min-w-[1320px]">
                    <thead>
                      <tr>
                        <th>需求编号</th>
                        <th>客户要求</th>
                        <th>是否满足</th>
                        <th>响应说明</th>
                        <th>风险等级</th>
                        <th>人工复核</th>
                        <th>人工备注</th>
                        <th>引用来源</th>
                        <th>操作</th>
                      </tr>
                    </thead>
                    <tbody>
                      {responses.map((response) => {
                        const requirement = requirementById.get(response.requirement_id);
                        const isRisk = response.match_status !== "satisfied" || response.risk_level !== "low";
                        return (
                          <tr key={response.id} className={isRisk ? "bg-amber-50/60" : undefined}>
                            <td className="font-medium text-slate-900">
                              {requirement?.requirement_code ?? response.requirement_id}
                            </td>
                            <td className="max-w-xs">{requirement?.content ?? "-"}</td>
                            <td>
                              <MatchBadge value={response.match_status} />
                            </td>
                            <td className="max-w-md">{response.response_text}</td>
                            <td>
                              <RiskBadge value={response.risk_level} />
                            </td>
                            <td>
                              <HumanStatusBadge value={response.human_status} />
                            </td>
                            <td className="max-w-xs">{response.human_note || "-"}</td>
                            <td className="max-w-sm">
                              {response.source_chunks.length === 0 ? (
                                <span className="text-xs font-medium text-amber-700">需要售前人工确认</span>
                              ) : (
                                <div className="space-y-2">
                                  {response.source_chunks.map((chunk) => (
                                    <div key={chunk.chunk_id} className="rounded border border-bidpilot-line bg-slate-50 p-2 text-xs">
                                      <div className="mb-1 font-semibold text-slate-600">
                                        片段 #{chunk.chunk_id} · 匹配分 {chunk.score}
                                      </div>
                                      <div>{chunk.content}</div>
                                    </div>
                                  ))}
                                </div>
                              )}
                            </td>
                            <td>
                              <button className="btn-secondary px-3 py-1.5" type="button" onClick={() => openEdit(response)}>
                                编辑
                              </button>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </section>
        </div>
      ) : null}
      {editingResponse && editForm ? (
        <ResponseEditDialog
          form={editForm}
          saving={saving}
          onChange={setEditForm}
          onClose={() => {
            setEditingResponse(null);
            setEditForm(null);
          }}
          onSubmit={handleSaveEdit}
        />
      ) : null}
    </>
  );
}

function RiskSummaryCards({ report }: { report: RiskReport }) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
      <SummaryCard label="需求总数" value={report.total_requirements} />
      <SummaryCard label="满足 / 部分 / 不支持" value={`${report.satisfied_count} / ${report.partial_count} / ${report.unsupported_count}`} />
      <SummaryCard label="低 / 中 / 高风险" value={`${report.low_risk_count} / ${report.medium_risk_count} / ${report.high_risk_count}`} />
      <SummaryCard
        label="待确认 / 已确认 / 已驳回"
        value={`${report.pending_review_count} / ${report.confirmed_count} / ${report.rejected_count}`}
        tone={report.pending_review_count > 0 || report.rejected_count > 0 ? "warning" : "normal"}
      />
      <SummaryCard label="风险项" value={report.risk_items.length} tone={report.risk_items.length > 0 ? "warning" : "normal"} />
    </div>
  );
}

function ResponseEditDialog({
  form,
  saving,
  onChange,
  onClose,
  onSubmit,
}: {
  form: EditForm;
  saving: boolean;
  onChange: (form: EditForm) => void;
  onClose: () => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/40 p-4">
      <form className="w-full max-w-2xl rounded-md bg-white shadow-xl" onSubmit={onSubmit}>
        <div className="border-b border-bidpilot-line px-5 py-4">
          <div className="text-base font-semibold text-slate-950">编辑响应复核</div>
        </div>
        <div className="grid gap-4 p-5 sm:grid-cols-2">
          <label className="field-label">
            是否满足
            <select
              className="input"
              value={form.match_status}
              onChange={(event) => onChange({ ...form, match_status: event.target.value as MatchStatus })}
            >
              <option value="satisfied">满足</option>
              <option value="partial">部分满足</option>
              <option value="unsupported">不支持</option>
            </select>
          </label>
          <label className="field-label">
            风险等级
            <select
              className="input"
              value={form.risk_level}
              onChange={(event) => onChange({ ...form, risk_level: event.target.value as RiskLevel })}
            >
              <option value="low">低风险</option>
              <option value="medium">中风险</option>
              <option value="high">高风险</option>
            </select>
          </label>
          <label className="field-label">
            人工复核状态
            <select
              className="input"
              value={form.human_status}
              onChange={(event) => onChange({ ...form, human_status: event.target.value as HumanReviewStatus })}
            >
              <option value="pending">待确认</option>
              <option value="confirmed">已确认</option>
              <option value="rejected">已驳回</option>
            </select>
          </label>
          <label className="field-label">
            人工备注
            <input className="input" value={form.human_note} onChange={(event) => onChange({ ...form, human_note: event.target.value })} />
          </label>
          <label className="field-label sm:col-span-2">
            响应说明
            <textarea
              className="input min-h-32 resize-y"
              required
              value={form.response_text}
              onChange={(event) => onChange({ ...form, response_text: event.target.value })}
            />
          </label>
        </div>
        <div className="flex justify-end gap-3 border-t border-bidpilot-line px-5 py-4">
          <button className="btn-secondary" type="button" disabled={saving} onClick={onClose}>
            取消
          </button>
          <button className="btn-primary" type="submit" disabled={saving}>
            {saving ? "保存中..." : "保存"}
          </button>
        </div>
      </form>
    </div>
  );
}

function SummaryCard({ label, value, tone = "normal" }: { label: string; value: number | string; tone?: "normal" | "warning" }) {
  return (
    <div className={`rounded-md border bg-white p-5 ${tone === "warning" ? "border-amber-200" : "border-bidpilot-line"}`}>
      <div className="text-sm text-slate-500">{label}</div>
      <div className={`mt-3 text-2xl font-semibold ${tone === "warning" ? "text-amber-700" : "text-slate-950"}`}>{value}</div>
    </div>
  );
}

function formatProjectName(name: string) {
  return name
    .replace(/^Prompt template e2e/i, "提示词模板端到端测试")
    .replace(/^Deliverable e2e/i, "交付物端到端测试")
    .replace(/^Human review e2e/i, "人工复核端到端测试");
}
