# BidPilot AI

BidPilot AI 是一个基于 RAG + Agent 的企业招投标智能响应系统。系统面向售前、解决方案和投标团队，支持上传客户 RFP 文件，抽取客户需求，检索企业产品资料库，并生成技术响应矩阵、满足性判断、风险等级、引用来源和可导出的业务报告。

## 项目简介

本项目是一个完整的大模型应用工程样例，覆盖前端交互、后端 API、数据库建模、模型配置中心、Mock LLM fallback、可切换 RAG 检索、Agent 执行日志、CSV/Excel/Word 导出和 Docker Compose 部署。

没有真实 API Key 时，系统仍可通过 Mock Provider 跑通完整演示流程；配置 DeepSeek、Qwen、Ollama 或其他 OpenAI-compatible API 后，可切换为真实模型调用。

## 业务背景

企业售前和招投标团队常见痛点：

- RFP 文档内容长、要求分散，人工提取需求耗时。
- 产品能力、实施服务和安全合规材料分散在不同资料中。
- 投标响应需要同时给出是否满足、响应说明、风险点和引用依据。
- 生成过程需要可追溯，不能是不可解释的黑盒模型调用。

BidPilot AI 用 RAG 检索企业知识库，用 Agent 串联需求抽取和响应生成，用日志记录关键步骤，帮助团队快速得到可复核、可交付的响应矩阵。

## 核心功能

- RFP 项目管理：创建、查看、删除项目。
- RFP 文件上传：支持 `.txt`、`.md`、`.pdf`、`.docx`、`.xlsx`。
- 需求抽取：通过 `LLMService.invoke_json` 抽取结构化客户需求并落库。
- 知识库管理：上传企业产品资料，解析为文本后按 chunk 入库。
- RAG 检索：通过可替换 Retriever 接口支持 `simple` 关键词检索和 `chroma` 向量检索。
- 响应矩阵：逐条需求检索知识库并生成满足状态、技术响应、风险等级和引用来源。
- 风险报告：统计 satisfied、partial、unsupported 和 low、medium、high 风险项。
- CSV / Excel / Word 导出：导出售前可交付的响应矩阵和投标响应初稿。
- 模型配置中心：支持 OpenAI-compatible API，API Key 脱敏返回。
- Mock 演示：无真实模型配置时自动 fallback，保证端到端演示可用。
- Agent 可观测性：记录每次抽取和响应生成的 steps、耗时、检索摘要和错误信息。

## 技术栈

- 前端：React、Vite、TypeScript、Tailwind CSS。
- 后端：FastAPI、SQLAlchemy、Pydantic。
- 数据库：PostgreSQL，开发环境支持 SQLite fallback。
- AI 层：统一 `LLMService`，支持 Mock Provider 和 OpenAI-compatible Provider。
- Agent：使用 LangGraph 工作流编排需求抽取、知识检索、响应生成、风险汇总和结果保存，并通过 `AgentRun.steps_json` 记录执行链路。
- RAG：TextSplitter + Retriever Factory，支持 SimpleKeywordRetriever fallback 与 ChromaVectorRetriever 向量检索。
- 部署：Docker Compose，包含 backend、frontend、postgres 三个服务。

## 系统架构

```mermaid
flowchart LR
    U["用户"] --> F["React 前端"]
    F --> B["FastAPI 后端"]
    B --> DB["PostgreSQL / SQLite"]
    B --> RAG["RAG Retriever"]
    RAG --> DB
    RAG --> CHROMA["Chroma Vector Store"]
    B --> LLM["LLMService"]
    LLM --> MOCK["Mock Provider"]
    LLM --> COMPAT["OpenAI-compatible API"]
    B --> LOG["AgentRun / LLMCallLog"]
    LOG --> DB
```

核心约束：

- 业务代码不直接 import OpenAI 客户端。
- 所有模型调用统一通过 `LLMService`。
- 所有结构化模型输出必须通过 Pydantic Schema 校验。
- API Key、Base URL、模型名不写死在业务代码中。

## 项目文档

项目补充文档位于 `docs/`：

- `docs/architecture.md`：整体架构、LLMService、RetrieverFactory、fallback 和可观测性设计。
- `docs/business_flow.md`：招投标业务流程、AI 角色、人工复核和交付物价值。
- `docs/database_design.md`：核心数据表、字段和表关系。
- `docs/agent_workflow.md`：LangGraph 节点输入输出和 `AgentRun.steps_json`。
- `docs/rag_design.md`：文件解析、chunk、embedding、Chroma 与 simple fallback。
- `docs/demo_script.md`：5 分钟演示脚本。
- `docs/interview_qa.md`：面试常见问题和回答要点。

## LangGraph 工作流

后端在 `backend/app/agents/` 中定义 BidPilot RFP 响应工作流。API 路由仍然调用 service 层，service 层再调用 LangGraph，避免把复杂业务逻辑堆在路由函数中。

当前节点包括：

- `load_project_context`：加载项目、RFP 文档、已有需求和知识库状态。
- `extract_requirements_node`：通过 `LLMService.invoke_json` 抽取结构化需求。
- `retrieve_knowledge_node`：对每条需求调用统一 Retriever Factory，可按配置使用 simple 或 chroma，并在 AgentRun 中记录 `retriever_type`。
- `generate_responses_node`：通过 `LLMService.invoke_json` 生成响应矩阵项。
- `assess_risk_node`：汇总满足性和风险等级计数。
- `save_results_node`：保存需求或响应结果。

`POST /api/rfp/projects/{project_id}/extract-requirements` 会执行 `load_project_context -> extract_requirements_node -> save_results_node`。
`POST /api/rfp/projects/{project_id}/generate-responses` 会执行 `load_project_context -> retrieve_knowledge_node -> generate_responses_node -> assess_risk_node -> save_results_node`。

每次运行会在 `AgentRun.steps_json.langgraph_nodes` 中记录节点名、输入摘要、输出摘要、耗时、状态和错误信息；同时保留旧版 `steps` 字段，便于现有前端页面继续展示。

## Prompt 模板

业务 Prompt 已从 Python 代码中抽离到 `backend/app/prompts/`：

- `extract_requirements.md`：需求抽取模板，使用 `{rfp_text}` 和 `{output_schema}`。
- `generate_response.md`：响应矩阵生成模板，使用 `{requirement}`、`{retrieved_chunks}` 和 `{output_schema}`。
- `assess_risk.md`：风险评估预留模板，使用 `{response_matrix}` 和 `{output_schema}`。
- `build_proposal.md`：投标初稿预留模板，使用 `{project_name}`、`{customer_name}`、`{response_matrix}` 和 `{risk_summary}`。

后端通过 `PromptTemplateService` 按模板名称加载并渲染变量；模板不存在或变量缺失时会返回清晰错误。调整需求抽取或响应生成提示词时，优先修改对应 `.md` 模板文件，不需要改 Agent 节点结构或业务路由。

## 启动方式

### Docker Compose

推荐演示方式：

```bash
cp .env.example .env
docker compose up --build
```

Compose 会使用正式 Dockerfile 构建镜像：

- `backend/Dockerfile` 在镜像构建阶段安装 Python 依赖，启动容器时直接运行 FastAPI。
- `frontend/Dockerfile` 在镜像构建阶段执行 `npm ci` 和 `npm run build`，再由轻量 Node 静态服务在 5173 端口提供构建后的 `dist`。
- `docker compose up --build` 启动阶段不再执行 `pip install` 或 `npm install`。

默认访问地址：

- 前端：http://localhost:5173
- 后端：http://localhost:8000
- API 文档：http://localhost:8000/docs
- PostgreSQL：localhost:5432

### 后端本地启动

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

不配置 `DATABASE_URL` 时，后端默认使用本地 SQLite 数据库。

健康检查：

```bash
curl http://localhost:8000/api/health
```

预期返回：

```json
{"status":"ok"}
```

### 前端本地启动

```bash
cd frontend
npm install
npm run dev
```

构建验证：

```bash
npm run build
```

本地开发如果需要指定后端地址，可设置 Vite 环境变量：

```bash
VITE_API_BASE_URL=http://localhost:8000 npm run dev
```

## 环境变量说明

`.env.example` 提供了可直接复制的占位配置：

| 变量 | 说明 | 示例 |
| --- | --- | --- |
| `POSTGRES_DB` | PostgreSQL 数据库名 | `bidpilot` |
| `POSTGRES_USER` | PostgreSQL 用户名 | `bidpilot` |
| `POSTGRES_PASSWORD` | PostgreSQL 密码 | `bidpilot` |
| `DATABASE_URL` | 后端数据库连接串 | `postgresql+psycopg://bidpilot:bidpilot@postgres:5432/bidpilot` |
| `MODEL_CONFIG_SECRET_KEY` | 模型 API Key 简单加密密钥，开发阶段使用，后续可替换 KMS | `change-me-model-config-secret` |
| `DEFAULT_PROVIDER` | 默认 Provider 标识，当前建议为 `mock` | `mock` |
| `RAG_RETRIEVER_TYPE` | 知识库检索模式，可选 `simple` 或 `chroma` | `chroma` |
| `CHROMA_PERSIST_DIR` | Chroma 向量库持久化目录 | `/app/.chroma` |
| `EMBEDDING_PROVIDER` | Embedding Provider，可选 `mock` 或 `openai-compatible` | `mock` |
| `EMBEDDING_BASE_URL` | OpenAI-compatible embedding API Base URL，mock 模式留空 |  |
| `EMBEDDING_API_KEY` | OpenAI-compatible embedding API Key，mock 模式留空 |  |
| `EMBEDDING_MODEL_NAME` | OpenAI-compatible embedding 模型名，mock 模式留空 |  |
| `CORS_ALLOW_ORIGINS` | 允许访问后端 API 的前端来源，多个值用英文逗号分隔 | `http://localhost:5173,http://127.0.0.1:5173` |
| `FRONTEND_API_BASE_URL` | Docker Compose 中注入给前端的后端 API 地址 | `http://localhost:8000` |
| `BACKEND_PORT` | 后端映射到宿主机的端口 | `8000` |
| `FRONTEND_PORT` | 前端映射到宿主机的端口 | `5173` |
| `POSTGRES_PORT` | PostgreSQL 映射到宿主机的端口 | `5432` |

不要把真实 API Key 写入 `.env.example`、README 或代码仓库。

## RAG 检索模式

当前知识库检索通过 `backend/app/rag/retriever_factory.py` 创建统一 Retriever：

- `RAG_RETRIEVER_TYPE=simple`：使用 `SimpleKeywordRetriever`，只依赖数据库中的 `KnowledgeChunk`，适合作为开发和故障 fallback。
- `RAG_RETRIEVER_TYPE=chroma`：上传知识库文件后会先保存 `KnowledgeFile` 和 `KnowledgeChunk` 到数据库，再写入 Chroma；检索时使用 `ChromaVectorRetriever` 返回 `retriever_type=chroma`。
- 如果 Chroma 初始化失败、embedding provider 不可用，或配置为 `simple`，系统会自动 fallback 到 `SimpleKeywordRetriever`。

`EMBEDDING_PROVIDER=mock` 使用 `MockEmbeddingProvider` 生成 deterministic embedding，不需要真实 API Key，可保证测试和 Mock 演示流程可运行。它只是演示和 fallback 用的轻量实现，不代表真实语义效果；生产环境可以将 `EMBEDDING_PROVIDER` 切换为 `openai-compatible`，并通过环境变量提供 embedding API 的 Base URL、API Key 和模型名。

## 文件解析能力

RFP 文件上传和知识库文件上传统一通过 `FileParserService` 解析，当前支持 `.txt`、`.md`、`.pdf`、`.docx`、`.xlsx`：

- `.txt` / `.md`：按文本读取，优先 UTF-8，并兼容常见中文编码。
- `.pdf`：使用 `pypdf` 提取可复制文本；不做 OCR，扫描版 PDF 需要先在外部完成文字识别。
- `.docx`：提取段落文本和表格文本。
- `.xlsx`：逐个 sheet 提取表格内容，并在文本中保留 `Sheet: <sheet_name>` 信息。

## 模型配置说明

进入前端 `/models` 页面可以新增、测试、设为默认和删除模型配置。后端也提供模型配置 API：

- `GET /api/models/configs`
- `POST /api/models/configs`
- `PATCH /api/models/configs/{config_id}`
- `DELETE /api/models/configs/{config_id}`
- `POST /api/models/configs/{config_id}/test`
- `POST /api/models/configs/{config_id}/set-default`

API Key 保存后只返回 `masked_api_key`，不会明文返回前端。

### DeepSeek 示例

```json
{
  "name": "DeepSeek",
  "provider": "openai-compatible",
  "base_url": "https://api.deepseek.com/v1",
  "api_key": "<YOUR_DEEPSEEK_API_KEY>",
  "model_name": "<DEEPSEEK_MODEL_NAME>",
  "temperature": 0.2,
  "max_tokens": 2048,
  "is_default": true,
  "enabled": true
}
```

### Ollama OpenAI-compatible 示例

本机运行 Ollama 时，如果后端也在本机直接启动：

```json
{
  "name": "Local Ollama",
  "provider": "openai-compatible",
  "base_url": "http://localhost:11434/v1",
  "api_key": "",
  "model_name": "<OLLAMA_MODEL_NAME>",
  "temperature": 0.2,
  "max_tokens": 2048,
  "is_default": true,
  "enabled": true
}
```

如果后端运行在 Docker 容器中，Docker Desktop 环境通常需要把 `base_url` 写成：

```text
http://host.docker.internal:11434/v1
```

### 任意 OpenAI-compatible API 示例

```json
{
  "name": "Compatible API",
  "provider": "openai-compatible",
  "base_url": "<OPENAI_COMPATIBLE_BASE_URL>",
  "api_key": "<YOUR_API_KEY>",
  "model_name": "<MODEL_NAME>",
  "temperature": 0.2,
  "max_tokens": 2048,
  "is_default": true,
  "enabled": true
}
```

保存后点击“测试连接”，后端会使用该配置真实调用 Chat Completions API，并发送“请只回复 OK”。失败时接口返回可读错误，不会让后端崩溃。

## Mock 演示流程

无需配置真实模型，直接启动系统后按以下流程演示：

1. 打开前端首页。
2. 进入“RFP 项目”，创建一个项目。
3. 进入项目详情，上传 `sample-data/sample_rfp.txt`。
4. 进入“知识库”，上传 `sample-data/product_docs.txt`。
5. 回到项目详情，点击“抽取客户需求”。
6. 进入“响应矩阵”，点击“生成响应矩阵”。
7. 查看风险统计、中高风险项和引用来源。
8. 点击“导出 CSV”“导出 Excel”或“导出 Word 初稿”下载交付物。
9. 进入“Agent 日志”查看执行步骤、耗时和检索摘要。

示例流程仍然使用 `.txt` 文件，便于 Mock 演示稳定复现；实际上传接口也支持文本型 PDF、DOCX 和 XLSX。

Mock Provider 会稳定返回 8 条样例需求，并生成预期响应矩阵：

- RBAC、操作日志、私有化部署、API 集成、数据加密、培训支持：`satisfied / low`
- 500 并发、灾难恢复：`partial / medium`

## 真实模型配置流程

1. 打开 `/models`。
2. 新增模型配置，选择 `openai-compatible`。
3. 填写 Base URL、API Key、模型名、temperature 和 max tokens。
4. 点击“测试连接”。
5. 测试成功后设为默认模型。
6. 重新执行需求抽取或响应矩阵生成。
7. 在 Agent 日志和 LLM 调用日志中检查执行链路。

真实模型输出仍会经过 Pydantic Schema 校验；如果模型返回无法解析的 JSON，后端会记录失败日志并返回清晰错误。

## API 文档入口

启动后访问：

- Swagger UI：http://localhost:8000/docs
- OpenAPI JSON：http://localhost:8000/openapi.json

主要 API 分组：

- `/api/health`
- `/api/rfp/projects`
- `/api/rfp/projects/{project_id}/documents`
- `/api/rfp/projects/{project_id}/requirements`
- `/api/rfp/projects/{project_id}/responses`
- `/api/rfp/projects/{project_id}/runs`
- `/api/knowledge`
- `/api/models/configs`

## 示例数据说明

示例数据位于 `sample-data/`：

- `sample_rfp.txt`：客户 RFP 样例，包含权限、日志、私有化部署、API 集成、加密传输、培训支持、500 并发和灾备要求。
- `product_docs.txt`：企业产品能力样例，包含 RBAC、日志审计、私有化部署、REST API、HTTPS 加密、实施服务、并发限制和灾备说明。

这两份 `.txt` 文件配合 Mock Provider 可完整演示需求抽取、知识库检索、响应矩阵、人工复核、风险报告和 CSV/Excel/Word 导出；同一上传流程也可处理 `.pdf`、`.docx`、`.xlsx` 业务文件。

## 测试与构建

后端测试：

```bash
cd backend
pytest
```

前端构建：

```bash
cd frontend
npm run build
```

Compose 配置检查：

```bash
docker compose config
```

## 简历亮点说明

- 从 0 到 1 搭建面向招投标场景的 RAG + Agent 大模型应用。
- 设计统一 LLM Provider 抽象，支持 Mock fallback 与 OpenAI-compatible 真实模型切换。
- 使用 Pydantic Schema 约束大模型结构化输出，降低幻觉和脏数据入库风险。
- 实现可替换 Retriever 抽象，支持 SimpleKeywordRetriever fallback 与 Chroma 向量检索切换。
- 构建 LangGraph Agent 工作流与 AgentRun / LLMCallLog 可观测性链路，展示抽取、检索、模型调用、风险汇总和保存步骤。
- 完成从 RFP 上传到响应矩阵、人工复核、风险报告、CSV/Excel/Word 导出的端到端业务闭环。
- 使用 FastAPI、SQLAlchemy、React、TypeScript、Tailwind CSS 和 Docker Compose 完成全栈工程化交付。
