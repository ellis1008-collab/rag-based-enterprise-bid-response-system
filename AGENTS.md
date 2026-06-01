# AGENTS.md

本文件用于约束后续所有 Codex 任务。除非用户明确给出新的、更具体的指令，否则在本项目内进行分析、编码、测试、重构和文档工作时，都必须遵守本文件。

## 项目名称

BidPilot AI：基于 RAG + Agent 的企业招投标智能响应系统。

## 项目目标

构建一个面向企业售前 / 招投标场景的大模型应用系统，支持上传客户 RFP 文件，自动抽取客户需求，基于企业产品资料库进行 RAG 检索，生成技术响应矩阵、满足性判断、风险等级和引用来源。

## 技术栈

1. 前端：React + Vite + TypeScript + Tailwind CSS。
2. 后端：FastAPI + SQLAlchemy + Pydantic。
3. 数据库：PostgreSQL，开发环境允许 SQLite fallback。
4. AI 层：统一 LLM Provider 抽象，支持 Mock Provider 和 OpenAI-compatible API。
5. Agent：后续使用 LangGraph 或可替换的工作流结构。
6. RAG：先实现简单 chunk + 检索抽象，后续可替换 Chroma / FAISS。
7. 部署：Docker Compose。

## 核心约束

1. 不要一次性实现所有功能。
2. 每次只完成当前任务范围。
3. 不要自动进入下一阶段，完成后停下来汇报。
4. 不要删除已有文件，除非明确说明原因并获得用户认可。
5. 不要在业务代码里写死任何 API Key、Base URL、模型名。
6. 所有模型调用必须通过 `LLMService`。
7. 没有真实 API Key 时，项目必须能通过 Mock Provider 跑完整演示流程。
8. 所有大模型结构化输出必须使用 Pydantic Schema 校验。
9. 每次 Agent / LLM / RAG 调用要保留日志扩展点。
10. 前端不能使用假数据，除非任务明确要求；最终必须调用后端 API。
11. 每个阶段完成后必须运行对应测试或构建命令。

## 后端约束

1. FastAPI 路由应保持清晰的模块边界，避免把业务逻辑直接堆在路由函数中。
2. 数据模型、请求响应 Schema、服务层逻辑应尽量分离。
3. SQLAlchemy 模型变更必须考虑 PostgreSQL，并保证开发环境 SQLite fallback 可用。
4. Pydantic Schema 是外部输入输出和 LLM 结构化输出的校验边界。
5. 新增配置项必须通过环境变量或配置层注入，不能硬编码在业务逻辑中。

## AI / Agent / RAG 约束

1. 所有 LLM 调用必须经过 `LLMService`，不能在业务代码中直接调用具体模型 SDK。
2. Provider 必须可替换，至少保留 Mock Provider 和 OpenAI-compatible Provider 的边界。
3. Agent 工作流应先保持简单、可测试、可替换，后续再引入 LangGraph 或其他编排方案。
4. RAG 初期可以使用简单 chunk 与检索抽象，但代码结构应允许替换为 Chroma / FAISS。
5. 技术响应矩阵、满足性判断、风险等级、引用来源等结构化结果必须经过 Pydantic 校验。
6. Agent / LLM / RAG 调用路径应预留日志、追踪、调试和审计扩展点。

## 前端约束

1. 前端使用 React + Vite + TypeScript + Tailwind CSS。
2. 前端页面和组件最终必须调用后端 API 获取数据。
3. 除非任务明确要求，不得使用假数据替代后端接口。
4. UI 实现应优先满足招投标响应工作流的清晰性、可读性和可操作性。
5. 新增前端功能后，应运行对应的构建、类型检查或测试命令。

## 工作方式

1. 开始任务前先理解当前代码结构和已有实现，不要凭空重写。
2. 优先延续项目已有目录结构、命名风格和抽象方式。
3. 只修改与当前任务直接相关的文件。
4. 对存在风险的设计选择，应先说明取舍，再实施。
5. 完成任务后汇报修改内容、验证命令和结果。
6. 如果测试或构建无法运行，必须说明原因和剩余风险。
