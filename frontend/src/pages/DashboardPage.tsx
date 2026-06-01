import { useEffect, useState } from "react";

import { listKnowledgeFiles } from "../api/knowledge";
import { listProjects, listResponses } from "../api/rfp";
import { EmptyBlock, ErrorBlock, LoadingBlock } from "../components/StateBlock";
import { PageHeader } from "../components/PageHeader";
import type { RfpProject } from "../types/rfp";

type DashboardPageProps = {
  navigate: (path: string) => void;
};

type DashboardStats = {
  projectCount: number;
  knowledgeFileCount: number;
  responseCount: number;
  riskCount: number;
  projects: RfpProject[];
};

export function DashboardPage({ navigate }: DashboardPageProps) {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [projects, knowledgeFiles] = await Promise.all([listProjects(), listKnowledgeFiles()]);
        const responseGroups = await Promise.all(projects.map((project) => listResponses(project.id)));
        const responses = responseGroups.flat();
        if (mounted) {
          setStats({
            projectCount: projects.length,
            knowledgeFileCount: knowledgeFiles.length,
            responseCount: responses.length,
            riskCount: responses.filter((item) => item.risk_level === "medium" || item.risk_level === "high").length,
            projects,
          });
        }
      } catch (err) {
        if (mounted) {
          setError(err instanceof Error ? err.message : "加载失败");
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
  }, []);

  return (
    <>
      <PageHeader
        title="仪表盘"
        actions={
          <>
            <button className="btn-primary" type="button" onClick={() => navigate("/projects")}>
              新建项目
            </button>
            <button className="btn-secondary" type="button" onClick={() => navigate("/knowledge")}>
              维护知识库
            </button>
          </>
        }
      />
      {loading ? <LoadingBlock title="加载仪表盘" /> : null}
      {error ? <ErrorBlock title="仪表盘加载失败" body={error} /> : null}
      {!loading && !error && stats ? (
        <div className="space-y-6">
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <MetricCard label="项目数量" value={stats.projectCount} />
            <MetricCard label="知识库文件数量" value={stats.knowledgeFileCount} />
            <MetricCard label="已生成响应数量" value={stats.responseCount} />
            <MetricCard label="中高风险项数量" value={stats.riskCount} tone={stats.riskCount > 0 ? "warning" : "normal"} />
          </div>
          <section className="rounded-md border border-bidpilot-line bg-white">
            <div className="border-b border-bidpilot-line px-5 py-4 text-sm font-semibold">最近项目</div>
            <div className="p-5">
              {stats.projects.length === 0 ? (
                <EmptyBlock title="暂无项目" body="创建项目后会在这里展示。" />
              ) : (
                <div className="divide-y divide-bidpilot-line">
                  {stats.projects.slice(0, 5).map((project) => (
                    <button
                      key={project.id}
                      className="flex w-full items-center justify-between py-3 text-left hover:bg-slate-50"
                      type="button"
                      onClick={() => navigate(`/projects/${project.id}`)}
                    >
                      <span>
                        <span className="block text-sm font-medium text-slate-900">{formatProjectName(project.name)}</span>
                        <span className="text-xs text-slate-500">{formatCustomerName(project.customer_name)}</span>
                      </span>
                      <span className="text-xs text-slate-400">{formatDate(project.created_at)}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </section>
        </div>
      ) : null}
    </>
  );
}

function MetricCard({ label, value, tone = "normal" }: { label: string; value: number; tone?: "normal" | "warning" }) {
  return (
    <div className="rounded-md border border-bidpilot-line bg-white p-5">
      <div className="text-sm text-slate-500">{label}</div>
      <div className={`mt-3 text-3xl font-semibold ${tone === "warning" ? "text-amber-700" : "text-slate-950"}`}>
        {value}
      </div>
    </div>
  );
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("zh-CN", { month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" }).format(
    new Date(value),
  );
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
