import { ChangeEvent, FormEvent, useEffect, useState } from "react";

import { listKnowledgeChunks, listKnowledgeFiles, retrieveKnowledge, uploadKnowledgeFile } from "../api/knowledge";
import { StatusBadge } from "../components/Badges";
import { PageHeader } from "../components/PageHeader";
import { EmptyBlock, ErrorBlock, LoadingBlock } from "../components/StateBlock";
import type { KnowledgeChunk, KnowledgeFile, RetrievedChunk } from "../types/knowledge";

export function KnowledgeBasePage() {
  const [files, setFiles] = useState<KnowledgeFile[]>([]);
  const [selectedFileId, setSelectedFileId] = useState<number | null>(null);
  const [chunks, setChunks] = useState<KnowledgeChunk[]>([]);
  const [retrieved, setRetrieved] = useState<RetrievedChunk[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function loadFiles(nextSelectedId?: number) {
    setLoading(true);
    setError(null);
    try {
      const data = await listKnowledgeFiles();
      setFiles(data);
      const activeId = nextSelectedId ?? selectedFileId ?? data[0]?.id ?? null;
      setSelectedFileId(activeId);
      setChunks(activeId ? await listKnowledgeChunks(activeId) : []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "知识库加载失败");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadFiles();
  }, []);

  async function handleUpload() {
    if (!file) return;
    setBusy("upload");
    setError(null);
    try {
      const uploaded = await uploadKnowledgeFile(file);
      setFile(null);
      await loadFiles(uploaded.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "知识库文件上传失败");
    } finally {
      setBusy(null);
    }
  }

  async function handleSelect(fileId: number) {
    setSelectedFileId(fileId);
    setBusy("chunks");
    try {
      setChunks(await listKnowledgeChunks(fileId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "片段加载失败");
    } finally {
      setBusy(null);
    }
  }

  async function handleRetrieve(event: FormEvent) {
    event.preventDefault();
    setBusy("retrieve");
    setError(null);
    try {
      setRetrieved(await retrieveKnowledge(query, 5));
    } catch (err) {
      setError(err instanceof Error ? err.message : "检索失败");
    } finally {
      setBusy(null);
    }
  }

  return (
    <>
      <PageHeader title="知识库" />
      {loading ? <LoadingBlock title="加载知识库" /> : null}
      {error ? <ErrorBlock title="知识库操作失败" body={error} /> : null}
      {!loading ? (
        <div className="grid gap-6 xl:grid-cols-[360px_1fr]">
          <section className="space-y-6">
            <div className="rounded-md border border-bidpilot-line bg-white p-5">
              <h2 className="text-sm font-semibold text-slate-900">上传企业产品资料</h2>
              <div className="mt-4 space-y-4">
                <input
                  className="input"
                  type="file"
                  accept=".txt,.md,.pdf,.docx,.xlsx"
                  onChange={(event: ChangeEvent<HTMLInputElement>) => setFile(event.target.files?.[0] ?? null)}
                />
                <button className="btn-primary w-full" type="button" disabled={!file || busy === "upload"} onClick={handleUpload}>
                  {busy === "upload" ? "上传中..." : "上传资料"}
                </button>
              </div>
            </div>
            <div className="rounded-md border border-bidpilot-line bg-white">
              <div className="border-b border-bidpilot-line px-5 py-4 text-sm font-semibold">文件列表</div>
              <div className="p-3">
                {files.length === 0 ? (
                  <EmptyBlock title="暂无知识库文件" body="上传后会生成文本片段。" />
                ) : (
                  <div className="space-y-2">
                    {files.map((item) => (
                      <button
                        key={item.id}
                        className={`w-full rounded-md border px-3 py-3 text-left text-sm ${
                          selectedFileId === item.id ? "border-teal-300 bg-teal-50" : "border-bidpilot-line bg-white hover:bg-slate-50"
                        }`}
                        type="button"
                        onClick={() => handleSelect(item.id)}
                      >
                        <div className="flex items-center justify-between gap-2">
                          <span className="font-medium text-slate-900">{item.filename}</span>
                          <StatusBadge value={item.status} />
                        </div>
                        <div className="mt-1 text-xs text-slate-500">{formatDate(item.created_at)}</div>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </section>
          <section className="space-y-6">
            <div className="rounded-md border border-bidpilot-line bg-white">
              <div className="border-b border-bidpilot-line px-5 py-4 text-sm font-semibold">文本片段列表</div>
              <div className="p-5">
                {busy === "chunks" ? <LoadingBlock title="加载文本片段" /> : null}
                {chunks.length === 0 && busy !== "chunks" ? (
                  <EmptyBlock title="暂无文本片段" body="选择或上传知识库文件。" />
                ) : (
                  <div className="space-y-3">
                    {chunks.map((chunk) => (
                      <div key={chunk.id} className="rounded-md border border-bidpilot-line p-4 text-sm">
                        <div className="mb-2 text-xs font-medium text-slate-500">#{chunk.chunk_index}</div>
                        <p className="leading-6 text-slate-700">{chunk.content}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
            <div className="rounded-md border border-bidpilot-line bg-white">
              <div className="border-b border-bidpilot-line px-5 py-4 text-sm font-semibold">检索测试</div>
              <div className="p-5">
                <form className="flex gap-3" onSubmit={handleRetrieve}>
                  <input className="input" value={query} required onChange={(event) => setQuery(event.target.value)} />
                  <button className="btn-primary shrink-0" type="submit" disabled={busy === "retrieve"}>
                    {busy === "retrieve" ? "检索中..." : "检索"}
                  </button>
                </form>
                <div className="mt-5 space-y-3">
                  {retrieved.length === 0 ? <EmptyBlock title="暂无召回结果" body="输入关键词后查看召回片段。" /> : null}
                  {retrieved.map((item) => (
                    <div key={item.chunk_id} className="rounded-md border border-bidpilot-line p-4">
                      <div className="mb-2 text-xs font-semibold text-teal-700">匹配分 {item.score}</div>
                      <p className="text-sm leading-6 text-slate-700">{item.content}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </section>
        </div>
      ) : null}
    </>
  );
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("zh-CN", { dateStyle: "short", timeStyle: "short" }).format(new Date(value));
}
