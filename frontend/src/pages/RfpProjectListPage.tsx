import { FormEvent, useEffect, useState } from "react";

import { createProject, listProjects } from "../api/rfp";
import { StatusBadge } from "../components/Badges";
import { EmptyBlock, ErrorBlock, LoadingBlock } from "../components/StateBlock";
import { PageHeader } from "../components/PageHeader";
import type { RfpProject } from "../types/rfp";

type RfpProjectListPageProps = {
  navigate: (path: string) => void;
};

export function RfpProjectListPage({ navigate }: RfpProjectListPageProps) {
  const [projects, setProjects] = useState<RfpProject[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [customerName, setCustomerName] = useState("");

  async function loadProjects() {
    setLoading(true);
    setError(null);
    try {
      setProjects(await listProjects());
    } catch (err) {
      setError(err instanceof Error ? err.message : "项目加载失败");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadProjects();
  }, []);

  async function handleCreate(event: FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const project = await createProject({ name, customer_name: customerName });
      setName("");
      setCustomerName("");
      navigate(`/projects/${project.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "创建项目失败");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <>
      <PageHeader title="招标项目" />
      <div className="grid gap-6 xl:grid-cols-[360px_1fr]">
        <section className="rounded-md border border-bidpilot-line bg-white p-5">
          <h2 className="text-sm font-semibold text-slate-900">创建项目</h2>
          <form className="mt-4 space-y-4" onSubmit={handleCreate}>
            <label className="field-label">
              项目名称
              <input className="input" value={name} required onChange={(event) => setName(event.target.value)} />
            </label>
            <label className="field-label">
              客户名称
              <input
                className="input"
                value={customerName}
                required
                onChange={(event) => setCustomerName(event.target.value)}
              />
            </label>
            <button className="btn-primary w-full" type="submit" disabled={submitting}>
              {submitting ? "创建中..." : "创建项目"}
            </button>
          </form>
        </section>
        <section className="rounded-md border border-bidpilot-line bg-white">
          <div className="border-b border-bidpilot-line px-5 py-4 text-sm font-semibold">项目列表</div>
          <div className="p-5">
            {loading ? <LoadingBlock title="加载项目" /> : null}
            {error ? <ErrorBlock title="项目操作失败" body={error} /> : null}
            {!loading && !error && projects.length === 0 ? <EmptyBlock title="暂无项目" body="创建后可进入详情上传招标文件。" /> : null}
            {!loading && projects.length > 0 ? (
              <div className="overflow-hidden rounded-md border border-bidpilot-line">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>项目名称</th>
                      <th>客户</th>
                      <th>状态</th>
                      <th>创建时间</th>
                    </tr>
                  </thead>
                  <tbody>
                    {projects.map((project) => (
                      <tr key={project.id} className="cursor-pointer hover:bg-slate-50" onClick={() => navigate(`/projects/${project.id}`)}>
                        <td className="font-medium text-slate-900">{formatProjectName(project.name)}</td>
                        <td>{formatCustomerName(project.customer_name)}</td>
                        <td>
                          <StatusBadge value={project.status} />
                        </td>
                        <td>{formatDate(project.created_at)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : null}
          </div>
        </section>
      </div>
    </>
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

function formatCustomerName(name: string) {
  return name === "Mock Customer" ? "模拟客户" : name;
}
