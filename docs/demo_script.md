# 5 分钟演示脚本

本脚本用于面试、答辩或项目展示。默认使用 Docker Compose、Mock Provider 和 Chroma + MockEmbeddingProvider，不需要真实 API Key。

## 0:00 - 0:30 启动项目

```bash
docker compose up --build -d
curl http://localhost:8000/api/health
```

打开：

- 前端：http://localhost:5173
- API 文档：http://localhost:8000/docs

讲解重点：

- 前端、后端、PostgreSQL 通过 Docker Compose 一键启动。
- `.env` 可配置 `RAG_RETRIEVER_TYPE=chroma`、`EMBEDDING_PROVIDER=mock`。
- 无真实模型配置时，Mock Provider 保证演示可跑通。

## 0:30 - 1:00 创建项目并上传 RFP

1. 进入“RFP 项目”。
2. 创建项目，例如“智慧平台招标响应”。
3. 进入项目详情。
4. 上传 `sample-data/sample_rfp.txt`。

讲解重点：

- 上传接口已支持 `.txt`、`.md`、文本型 `.pdf`、`.docx`、`.xlsx`。
- 当前 demo 用 `.txt` 是为了让 Mock 流程稳定复现。
- 文件解析结果保存到 `RfpDocument.content_text`。

## 1:00 - 1:30 上传产品资料

1. 进入“知识库”。
2. 上传 `sample-data/product_docs.txt`。
3. 查看文件和 chunks。
4. 可测试检索 query：`私有化部署`、`操作日志`、`500 并发`。

讲解重点：

- 知识库文件先保存到数据库，再切分为 `KnowledgeChunk`。
- Chroma 模式下 chunks 同步写入 Chroma。
- 如果 Chroma 或 embedding 不可用，会 fallback simple。

## 1:30 - 2:00 抽取客户需求

1. 回到项目详情页。
2. 点击“抽取客户需求”。
3. 查看 8 条结构化需求。

预期结果：

- RBAC 多角色权限。
- 操作日志审计。
- 私有化部署。
- API 集成。
- 数据加密传输。
- 实施培训和上线支持。
- 500 名用户同时在线。
- 数据备份和灾难恢复。

讲解重点：

- LangGraph 执行 `load_project_context -> extract_requirements_node -> save_results_node`。
- Prompt 已抽离到 `backend/app/prompts/extract_requirements.md`。
- 输出经过 `RequirementExtractionResult` 校验。

## 2:00 - 2:45 生成响应矩阵

1. 进入“响应矩阵”页面。
2. 点击“生成响应矩阵”。
3. 查看满足性、响应说明、风险等级和引用来源。

预期风险统计：

- 6 条 `satisfied / low`。
- 2 条 `partial / medium`。

讲解重点：

- 每条需求先检索知识库，再生成响应。
- LangGraph 执行 `load_project_context -> retrieve_knowledge_node -> generate_responses_node -> assess_risk_node -> save_results_node`。
- Prompt 已抽离到 `backend/app/prompts/generate_response.md`。
- AgentRun 可看到 `retriever_type=["chroma"]`。

## 2:45 - 3:30 人工复核

1. 在响应矩阵表格中点击某一行“编辑”。
2. 修改响应说明、风险等级或人工复核状态。
3. 填写人工备注。
4. 保存后刷新页面。

讲解重点：

- AI 生成结果不是最终投标承诺。
- `human_status` 支持 `pending / confirmed / rejected`。
- `human_note` 支持售前人员记录判断依据。
- 风险统计区域会展示待确认、已确认、已驳回数量。

## 3:30 - 4:15 导出 Excel / Word

1. 点击“导出 Excel”。
2. 点击“导出 Word 初稿”。

讲解重点：

- Excel 技术响应矩阵包含需求、分类、优先级、客户要求、满足性、风险、响应说明、引用来源、人工复核状态和备注。
- Word 投标响应初稿包含标题、客户名称、生成时间、响应摘要、技术响应矩阵、风险与待确认事项和说明。
- 文档是初稿，正式投标前仍需人工最终确认。

## 4:15 - 4:45 查看 Agent 日志

1. 进入“AgentRun”页面。
2. 查看抽取需求 run 和生成响应 run。
3. 展开节点信息和 steps。

讲解重点：

- `AgentRun.steps_json.langgraph_nodes` 记录节点级输入摘要、输出摘要、耗时和错误。
- 响应生成日志包含检索 query、召回 chunk 摘要和 retriever_type。
- 这让系统不是黑盒模型调用。

## 4:45 - 5:00 查看模型配置

1. 进入“模型设置”。
2. 展示 Mock / OpenAI-compatible 的配置方式。

讲解重点：

- API Key 加密存储，不明文返回前端。
- 可配置 DeepSeek、Qwen、Ollama 或其他 OpenAI-compatible API。
- 真实模型输出仍经过 Pydantic Schema 校验。

## 结束总结

一句话总结：

BidPilot AI 把 RFP 上传、需求抽取、知识库检索、响应矩阵生成、人工复核、风险统计、Excel/Word 交付物和 Agent 可观测性串成了一个可运行的招投标智能响应闭环。

