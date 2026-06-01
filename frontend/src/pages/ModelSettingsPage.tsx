import { FormEvent, useEffect, useState } from "react";

import {
  createModelConfig,
  deleteModelConfig,
  listModelConfigs,
  setDefaultModelConfig,
  testModelConfig,
} from "../api/models";
import { StatusBadge } from "../components/Badges";
import { PageHeader } from "../components/PageHeader";
import { EmptyBlock, ErrorBlock, LoadingBlock } from "../components/StateBlock";
import type { ModelConfig, ModelConfigTestResult } from "../types/models";

type ModelForm = {
  name: string;
  provider: string;
  base_url: string;
  api_key: string;
  model_name: string;
  temperature: string;
  max_tokens: string;
  is_default: boolean;
  enabled: boolean;
};

const initialForm: ModelForm = {
  name: "",
  provider: "openai-compatible",
  base_url: "",
  api_key: "",
  model_name: "",
  temperature: "0.2",
  max_tokens: "1024",
  is_default: false,
  enabled: true,
};

const PROVIDER_LABELS: Record<string, string> = {
  "openai-compatible": "通用兼容接口",
  mock: "模拟模型服务",
};

export function ModelSettingsPage() {
  const [configs, setConfigs] = useState<ModelConfig[]>([]);
  const [form, setForm] = useState<ModelForm>(initialForm);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [testResults, setTestResults] = useState<Record<number, ModelConfigTestResult>>({});

  async function load() {
    setLoading(true);
    setError(null);
    try {
      setConfigs(await listModelConfigs());
    } catch (err) {
      setError(err instanceof Error ? err.message : "模型配置加载失败");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function handleCreate(event: FormEvent) {
    event.preventDefault();
    setBusy("create");
    setError(null);
    try {
      await createModelConfig({
        name: form.name,
        provider: form.provider,
        base_url: form.base_url || null,
        api_key: form.api_key || null,
        model_name: form.model_name,
        temperature: Number(form.temperature),
        max_tokens: Number(form.max_tokens),
        is_default: form.is_default,
        enabled: form.enabled,
      });
      setForm(initialForm);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "创建模型配置失败");
    } finally {
      setBusy(null);
    }
  }

  async function handleTest(configId: number) {
    setBusy(`test-${configId}`);
    setError(null);
    try {
      const result = await testModelConfig(configId);
      setTestResults((current) => ({ ...current, [configId]: result }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "测试连接失败");
    } finally {
      setBusy(null);
    }
  }

  async function handleSetDefault(configId: number) {
    setBusy(`default-${configId}`);
    setError(null);
    try {
      await setDefaultModelConfig(configId);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "设为默认失败");
    } finally {
      setBusy(null);
    }
  }

  async function handleDelete(configId: number) {
    setBusy(`delete-${configId}`);
    setError(null);
    try {
      await deleteModelConfig(configId);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "删除配置失败");
    } finally {
      setBusy(null);
    }
  }

  return (
    <>
      <PageHeader title="模型配置" />
      <div className="grid gap-6 xl:grid-cols-[420px_1fr]">
        <section className="rounded-md border border-bidpilot-line bg-white p-5">
          <h2 className="text-sm font-semibold text-slate-900">新增模型配置</h2>
          <form className="mt-4 space-y-4" onSubmit={handleCreate}>
            <label className="field-label">
              名称
              <input className="input" required value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} />
            </label>
            <label className="field-label">
              服务类型
              <select className="input" value={form.provider} onChange={(event) => setForm({ ...form, provider: event.target.value })}>
                <option value="openai-compatible">通用兼容接口</option>
                <option value="mock">模拟模型服务</option>
              </select>
            </label>
            <label className="field-label">
              接口地址
              <input
                className="input"
                value={form.base_url}
                placeholder="https://api.example.com/v1"
                onChange={(event) => setForm({ ...form, base_url: event.target.value })}
              />
            </label>
            <label className="field-label">
              接口密钥
              <input
                className="input"
                type="password"
                value={form.api_key}
                onChange={(event) => setForm({ ...form, api_key: event.target.value })}
              />
            </label>
            <label className="field-label">
              模型名
              <input
                className="input"
                required
                value={form.model_name}
                onChange={(event) => setForm({ ...form, model_name: event.target.value })}
              />
            </label>
            <div className="grid grid-cols-2 gap-3">
              <label className="field-label">
                输出随机性
                <input
                  className="input"
                  type="number"
                  min="0"
                  max="2"
                  step="0.1"
                  value={form.temperature}
                  onChange={(event) => setForm({ ...form, temperature: event.target.value })}
                />
              </label>
              <label className="field-label">
                最大输出长度
                <input
                  className="input"
                  type="number"
                  min="1"
                  value={form.max_tokens}
                  onChange={(event) => setForm({ ...form, max_tokens: event.target.value })}
                />
              </label>
            </div>
            <label className="flex items-center gap-2 text-sm text-slate-700">
              <input
                type="checkbox"
                checked={form.is_default}
                onChange={(event) => setForm({ ...form, is_default: event.target.checked })}
              />
              设为默认
            </label>
            <label className="flex items-center gap-2 text-sm text-slate-700">
              <input
                type="checkbox"
                checked={form.enabled}
                onChange={(event) => setForm({ ...form, enabled: event.target.checked })}
              />
              启用
            </label>
            <button className="btn-primary w-full" type="submit" disabled={busy === "create"}>
              {busy === "create" ? "保存中..." : "保存配置"}
            </button>
          </form>
        </section>
        <section className="rounded-md border border-bidpilot-line bg-white">
          <div className="border-b border-bidpilot-line px-5 py-4 text-sm font-semibold">配置列表</div>
          <div className="p-5">
            {loading ? <LoadingBlock title="加载模型配置" /> : null}
            {error ? <ErrorBlock title="模型配置操作失败" body={error} /> : null}
            {!loading && configs.length === 0 ? <EmptyBlock title="暂无模型配置" body="无配置时后端会自动使用模拟模型服务。" /> : null}
            {!loading && configs.length > 0 ? (
              <div className="space-y-4">
                {configs.map((config) => {
                  const result = testResults[config.id];
                  return (
                    <div key={config.id} className="rounded-md border border-bidpilot-line p-4">
                      <div className="flex flex-wrap items-start justify-between gap-3">
                        <div>
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="font-medium text-slate-900">{config.name}</span>
                            {config.is_default ? <StatusBadge value="default" /> : null}
                            <StatusBadge value={config.enabled ? "enabled" : "disabled"} />
                          </div>
                          <div className="mt-2 grid gap-1 text-sm text-slate-600 sm:grid-cols-2">
                            <div>服务类型：{formatProvider(config.provider)}</div>
                            <div>模型名：{config.model_name}</div>
                            <div>接口地址：{config.base_url ?? "-"}</div>
                            <div>接口密钥：{config.masked_api_key ?? "-"}</div>
                          </div>
                        </div>
                        <div className="flex flex-wrap gap-2">
                          <button className="btn-secondary" type="button" disabled={busy === `test-${config.id}`} onClick={() => handleTest(config.id)}>
                            {busy === `test-${config.id}` ? "测试中..." : "测试连接"}
                          </button>
                          <button
                            className="btn-secondary"
                            type="button"
                            disabled={config.is_default || busy === `default-${config.id}`}
                            onClick={() => handleSetDefault(config.id)}
                          >
                            设为默认
                          </button>
                          <button className="btn-danger" type="button" disabled={busy === `delete-${config.id}`} onClick={() => handleDelete(config.id)}>
                            删除
                          </button>
                        </div>
                      </div>
                      {result ? (
                        <div className={`mt-3 rounded-md p-3 text-sm ${result.success ? "bg-emerald-50 text-emerald-700" : "bg-red-50 text-red-700"}`}>
                          {result.success ? "连接成功" : "连接失败"} · 模型返回：{formatTestMessage(result.message)} · 耗时 {result.latency_ms}ms
                        </div>
                      ) : null}
                    </div>
                  );
                })}
              </div>
            ) : null}
          </div>
        </section>
      </div>
    </>
  );
}

function formatProvider(provider: string) {
  return PROVIDER_LABELS[provider] ?? provider;
}

function formatTestMessage(message: string) {
  return message.trim().toUpperCase() === "OK" ? "OK（正常）" : message;
}
