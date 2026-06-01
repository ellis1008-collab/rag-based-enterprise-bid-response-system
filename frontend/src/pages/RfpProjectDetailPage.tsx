import { ChangeEvent, useEffect, useState } from "react";

import {
  extractRequirements,
  getProject,
  listProjectDocuments,
  listRequirements,
  uploadRfpDocument,
} from "../api/rfp";
import { PriorityBadge } from "../components/Badges";
import { PageHeader } from "../components/PageHeader";
import { EmptyBlock, ErrorBlock, LoadingBlock } from "../components/StateBlock";
import type { RfpDocument, RfpProject, RfpRequirement } from "../types/rfp";

type RfpProjectDetailPageProps = {
  projectId: number;
  navigate: (path: string) => void;
};

export function RfpProjectDetailPage({ projectId, navigate }: RfpProjectDetailPageProps) {
  const [project, setProject] = useState<RfpProject | null>(null);
  const [documents, setDocuments] = useState<RfpDocument[]>([]);
  const [requirements, setRequirements] = useState<RfpRequirement[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const [projectData, documentData, requirementData] = await Promise.all([
        getProject(projectId),
        listProjectDocuments(projectId),
        listRequirements(projectId),
      ]);
      setProject(projectData);
      setDocuments(documentData);
      setRequirements(requirementData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "项目详情加载失败");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [projectId]);

  async function handleUpload() {
    if (!file) return;
    setBusy("upload");
    setError(null);
    try {
      await uploadRfpDocument(projectId, file);
      setFile(null);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "招标文件上传失败");
    } finally {
      setBusy(null);
    }
  }

  async function handleExtract() {
    setBusy("extract");
    setError(null);
    try {
      setRequirements(await extractRequirements(projectId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "需求抽取失败");
    } finally {
      setBusy(null);
    }
  }

  return (
    <>
      <PageHeader
        title={project ? formatProjectName(project.name) : "项目详情"}
        actions={
          <>
            <button className="btn-secondary" type="button" onClick={() => navigate(`/projects/${projectId}/runs`)}>
              运行记录
            </button>
            <button className="btn-primary" type="button" onClick={() => navigate(`/projects/${projectId}/responses`)}>
              响应矩阵
            </button>
          </>
        }
      />
      {loading ? <LoadingBlock title="加载项目详情" /> : null}
      {error ? <ErrorBlock title="项目操作失败" body={error} /> : null}
      {!loading && project ? (
        <div className="space-y-6">
          <section className="rounded-md border border-bidpilot-line bg-white p-5">
            <div className="grid gap-4 text-sm sm:grid-cols-3">
              <Info label="项目 ID" value={String(project.id)} />
              <Info label="客户名称" value={project.customer_name} />
              <Info label="更新时间" value={formatDate(project.updated_at)} />
            </div>
          </section>
          <section className="grid gap-6 xl:grid-cols-[360px_1fr]">
            <div className="rounded-md border border-bidpilot-line bg-white p-5">
              <h2 className="text-sm font-semibold text-slate-900">上传招标文件</h2>
              <div className="mt-4 space-y-4">
                <input
                  className="input"
                  type="file"
                  accept=".txt,.md,.pdf,.docx,.xlsx"
                  onChange={(event: ChangeEvent<HTMLInputElement>) => setFile(event.target.files?.[0] ?? null)}
                />
                <button className="btn-primary w-full" type="button" disabled={!file || busy === "upload"} onClick={handleUpload}>
                  {busy === "upload" ? "上传中..." : "上传文件"}
                </button>
              </div>
              <div className="mt-5 border-t border-bidpilot-line pt-4">
                <h3 className="text-xs font-semibold uppercase text-slate-500">已上传文件</h3>
                {documents.length === 0 ? (
                  <div className="mt-3 text-sm text-slate-500">暂无招标文件</div>
                ) : (
                  <ul className="mt-3 space-y-2 text-sm">
                    {documents.map((document) => (
                      <li key={document.id} className="rounded border border-bidpilot-line px-3 py-2">
                        {document.filename}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
            <div className="rounded-md border border-bidpilot-line bg-white">
              <div className="flex items-center justify-between border-b border-bidpilot-line px-5 py-4">
                <h2 className="text-sm font-semibold text-slate-900">客户需求</h2>
                <button className="btn-primary" type="button" disabled={busy === "extract"} onClick={handleExtract}>
                  {busy === "extract" ? "抽取中..." : "抽取客户需求"}
                </button>
              </div>
              <div className="p-5">
                {requirements.length === 0 ? (
                  <EmptyBlock title="暂无需求" body="上传招标文件后可触发抽取。" />
                ) : (
                  <div className="overflow-hidden rounded-md border border-bidpilot-line">
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>编号</th>
                          <th>分类</th>
                          <th>优先级</th>
                          <th>内容</th>
                        </tr>
                      </thead>
                      <tbody>
                        {requirements.map((item) => (
                          <tr key={item.id}>
                            <td className="font-medium text-slate-900">{item.requirement_code}</td>
                            <td>{item.category}</td>
                            <td>
                              <PriorityBadge value={item.priority} />
                            </td>
                            <td className="max-w-xl">{item.content}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          </section>
        </div>
      ) : null}
    </>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-xs text-slate-500">{label}</div>
      <div className="mt-1 font-medium text-slate-900">{value}</div>
    </div>
  );
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("zh-CN", { dateStyle: "short", timeStyle: "short" }).format(new Date(value));
}

function formatProjectName(name: string) {
  return name
    .replace(/^Prompt template e2e/i, "提示词模板端到端测试")
    .replace(/^Deliverable e2e/i, "交付物端到端测试")
    .replace(/^Human review e2e/i, "人工复核端到端测试");
}
