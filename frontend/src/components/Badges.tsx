export function MatchBadge({ value }: { value: string }) {
  const className =
    value === "satisfied"
      ? "border-emerald-200 bg-emerald-50 text-emerald-700"
      : value === "partial"
        ? "border-amber-200 bg-amber-50 text-amber-700"
        : "border-red-200 bg-red-50 text-red-700";

  const label = value === "satisfied" ? "满足" : value === "partial" ? "部分满足" : "不支持";
  return <span className={`inline-flex rounded border px-2 py-0.5 text-xs font-medium ${className}`}>{label}</span>;
}

export function RiskBadge({ value }: { value: string }) {
  const className =
    value === "low"
      ? "border-emerald-200 bg-emerald-50 text-emerald-700"
      : value === "medium"
        ? "border-amber-200 bg-amber-50 text-amber-700"
        : "border-red-200 bg-red-50 text-red-700";

  const label = value === "low" ? "低风险" : value === "medium" ? "中风险" : "高风险";
  return <span className={`inline-flex rounded border px-2 py-0.5 text-xs font-medium ${className}`}>{label}</span>;
}

export function HumanStatusBadge({ value }: { value: string }) {
  const className =
    value === "confirmed"
      ? "border-emerald-200 bg-emerald-50 text-emerald-700"
      : value === "rejected"
        ? "border-red-200 bg-red-50 text-red-700"
        : "border-amber-200 bg-amber-50 text-amber-700";

  const label = value === "confirmed" ? "已确认" : value === "rejected" ? "已驳回" : "待确认";
  return <span className={`inline-flex rounded border px-2 py-0.5 text-xs font-medium ${className}`}>{label}</span>;
}

export function StatusBadge({ value }: { value: string }) {
  const className =
    value === "succeeded" || value === "completed" || value === "uploaded" || value === "ok" || value === "enabled" || value === "default"
      ? "border-emerald-200 bg-emerald-50 text-emerald-700"
      : value === "running"
        ? "border-sky-200 bg-sky-50 text-sky-700"
        : value === "failed"
          ? "border-red-200 bg-red-50 text-red-700"
          : "border-slate-200 bg-slate-50 text-slate-700";

  const labels: Record<string, string> = {
    succeeded: "成功",
    completed: "已完成",
    uploaded: "已上传",
    ok: "正常",
    running: "运行中",
    failed: "失败",
    default: "默认",
    enabled: "已启用",
    disabled: "已停用",
    draft: "草稿",
    deleted: "已删除",
  };

  return <span className={`inline-flex rounded border px-2 py-0.5 text-xs font-medium ${className}`}>{labels[value] ?? value}</span>;
}

export function PriorityBadge({ value }: { value: string }) {
  const className =
    value === "high"
      ? "border-red-200 bg-red-50 text-red-700"
      : value === "medium"
        ? "border-amber-200 bg-amber-50 text-amber-700"
        : "border-slate-200 bg-slate-50 text-slate-700";

  const label = value === "high" ? "高" : value === "medium" ? "中" : value === "low" ? "低" : value;
  return <span className={`inline-flex rounded border px-2 py-0.5 text-xs font-medium ${className}`}>{label}</span>;
}
