# RAG 设计说明

## 文件解析流程

RFP 文件上传和知识库文件上传都统一通过 `FileParserService`：

- `.txt` / `.md`：按 UTF-8 优先读取，并兼容 `gb18030`、`gbk` 等常见编码。
- `.pdf`：使用 `pypdf` 提取可复制文本，不做 OCR。
- `.docx`：提取段落文本和表格文本。
- `.xlsx`：逐 sheet 提取表格内容，并保留 `Sheet: <sheet_name>` 信息。

空文件、解析后无文本、不支持格式、PDF/DOCX/XLSX 解析失败都会返回清晰错误。

## 文本切分

知识库上传流程：

1. `FileParserService` 解析文件。
2. 保存 `KnowledgeFile.content_text`。
3. 使用 `split_text_by_length` 按配置的 `knowledge_chunk_size` 切分。
4. 保存 `KnowledgeChunk`，写入 chunk_index、content 和 metadata。
5. 如果当前为 Chroma 模式，则额外写入 Chroma。

当前切分策略是按固定长度切分，后续规划可以替换为按标题、段落、表格结构或 token 长度切分。

## EmbeddingProvider 抽象

`backend/app/rag/embeddings.py` 定义：

- `BaseEmbeddingProvider`
- `MockEmbeddingProvider`
- `OpenAICompatibleEmbeddingProvider`

`MockEmbeddingProvider`：

- 不依赖真实 API Key。
- 使用 deterministic hashing 生成稳定向量。
- 适合测试和 Mock 演示。
- 不追求真实语义效果。

`OpenAICompatibleEmbeddingProvider`：

- 调用 OpenAI-compatible `/embeddings` 接口。
- 通过环境变量注入 base_url、api_key 和 model_name。
- 当前作为生产替换边界保留，实际效果取决于外部 embedding 服务。

## ChromaVectorRetriever

`ChromaVectorRetriever` 使用 Chroma 持久化知识库向量：

- `add_chunks(chunks)`：把数据库中的 `KnowledgeChunk` 写入 Chroma。
- `retrieve(query, top_k)`：对 query 生成 embedding，并从 Chroma 召回 top_k chunks。
- 返回字段包含 `chunk_id`、`file_id`、`content`、`score`、`metadata`、`retriever_type`。

Chroma 持久化目录由 `CHROMA_PERSIST_DIR` 控制。

## SimpleKeywordRetriever Fallback

`SimpleKeywordRetriever` 使用数据库中的 `KnowledgeChunk` 做关键词检索。

它的作用不是替代向量检索，而是保证系统在以下场景仍可用：

- Chroma 初始化失败。
- embedding 配置不可用。
- 显式配置 `RAG_RETRIEVER_TYPE=simple`。
- 本地测试和最小演示环境。

## RetrieverFactory

`RetrieverFactory` 是统一入口：

- `RAG_RETRIEVER_TYPE=simple`：创建 `SimpleKeywordRetriever`。
- `RAG_RETRIEVER_TYPE=chroma`：创建 `ChromaVectorRetriever`。
- 未知配置：记录 warning 并 fallback simple。
- Chroma 初始化异常：记录 warning 并 fallback simple。

业务代码通过 `retrieve_knowledge` 服务调用统一 Retriever，不直接依赖 simple 或 chroma。

## 为什么需要 fallback

招投标演示和开发环境经常没有完整向量数据库或真实 embedding 服务。fallback 可以保证：

- 无真实 API Key 时，Mock 流程仍可跑通。
- Docker Compose 演示不会因为向量库问题完全失败。
- 测试可以覆盖业务闭环，而不是卡在外部依赖。
- 真实生产部署可以逐步切换到 Chroma 和真实 embedding。

## 如何切换 simple/chroma

环境变量：

```env
RAG_RETRIEVER_TYPE=chroma
EMBEDDING_PROVIDER=mock
CHROMA_PERSIST_DIR=/app/.chroma
```

可选值：

- `RAG_RETRIEVER_TYPE=simple`
- `RAG_RETRIEVER_TYPE=chroma`
- `EMBEDDING_PROVIDER=mock`
- `EMBEDDING_PROVIDER=openai-compatible`

Docker Compose 会把这些变量传入 backend。

## 后续如何替换真实 embedding

后续接真实 embedding 的方式：

1. 配置 `EMBEDDING_PROVIDER=openai-compatible`。
2. 设置 `EMBEDDING_BASE_URL`。
3. 设置 `EMBEDDING_API_KEY`。
4. 设置 `EMBEDDING_MODEL_NAME`。
5. 重新上传或重建知识库向量索引。

后续规划：

- 支持更多向量库，例如 FAISS、pgvector。
- 支持更细粒度的 chunk metadata。
- 支持按项目、租户或知识库集合隔离向量索引。
- 支持 OCR，但当前没有实现 OCR。

