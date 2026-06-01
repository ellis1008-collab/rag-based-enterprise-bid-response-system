# 面试问答准备

## 为什么做这个项目？

企业招投标响应是一个高频、复杂、强流程的业务场景。它既需要理解客户 RFP，又需要检索企业产品资料，还需要输出结构化响应矩阵和可交付文档。这个项目能体现 RAG、Agent、LLM Provider 抽象、人工复核、文件解析、导出和 Docker 部署等工程能力。

## 为什么用 LangGraph？

RFP 响应不是一次简单模型调用，而是多个步骤组成的流程：

- 加载项目上下文。
- 抽取需求。
- 检索知识库。
- 生成响应。
- 统计风险。
- 保存结果。

LangGraph 能把这些节点显式建模，并保留状态传递和节点级日志。当前项目没有做复杂分支和循环，但已经为后续加入人工审批节点、重试节点或多 Agent 协作预留结构。

## 为什么用 RAG？

招投标响应必须基于企业已有产品能力和服务承诺，不能只依赖模型通用知识。RAG 的作用是：

- 从企业知识库召回相关产品资料。
- 让响应说明引用具体来源 chunk。
- 降低模型编造能力边界的风险。
- 支持企业知识随资料上传而更新。

## 为什么要 Chroma + Simple fallback？

Chroma 提供向量检索能力，适合真实 RAG 场景；Simple fallback 保证系统在没有向量库、没有 embedding 服务或配置异常时仍能演示和测试。

这个设计的工程价值：

- 降低本地启动门槛。
- 保证 Mock 演示稳定。
- 避免外部依赖故障导致整个业务链路不可用。
- 让 Retriever 抽象具备可替换性。

## 为什么要 Mock Provider？

真实模型 API 依赖 API Key、网络和模型稳定性。Mock Provider 的作用是：

- 无真实 API Key 也能跑完整业务闭环。
- 测试结果 deterministic。
- 面试或演示时降低外部依赖风险。
- 保证 8 条需求、8 条响应、6 low / 2 medium 的基线稳定。

Mock Provider 不是生产模型，只用于 fallback、测试和演示。

## 为什么要 Prompt 模板抽离？

把 Prompt 写在 Python 业务逻辑里会导致：

- 提示词难以维护。
- 业务代码和提示词耦合。
- 调整 Prompt 需要改代码。

当前项目把模板放在 `backend/app/prompts/`，通过 `PromptTemplateService` 加载和渲染。这样可以在不改 Agent 节点结构的情况下调整需求抽取和响应生成提示词。

## 为什么要人工复核？

投标响应属于高责任场景，AI 生成内容不能直接作为最终承诺。人工复核提供：

- 对满足性判断的确认。
- 对中高风险项的人工把关。
- 对响应说明的业务修订。
- 对最终导出交付物的状态标记。

系统中 `human_status` 支持 `pending / confirmed / rejected`，`human_note` 支持记录人工意见。

## 如何保证模型输出稳定？

当前项目通过多层机制提高稳定性：

- 所有模型调用统一经过 `LLMService`。
- 结构化输出使用 Pydantic Schema 校验。
- `LLMService.invoke_json` 要求返回符合 JSON Schema 的 JSON。
- Mock Provider 提供稳定回归基线。
- AgentRun 和 LLMCallLog 记录调用链路和失败信息。

仍需说明：真实模型输出无法 100% 保证稳定，生产场景可以继续增加重试、纠错 prompt、人工审批和更严格的校验策略。

## 如何保证 API Key 安全？

当前项目的 ModelConfig：

- API Key 加密后存储在 `api_key_encrypted`。
- 前端读取配置时不返回明文 API Key。
- 业务代码不硬编码 API Key、Base URL 或模型名。
- 模型调用由配置中心和 `LLMService` 注入。

后续规划可以加入更完整的密钥轮换、审计和权限控制。

## 如果接真实大模型如何配置？

在前端“模型设置”页面新增配置：

- provider：`openai-compatible`
- base_url：兼容 Chat Completions API 的地址
- api_key：真实 API Key
- model_name：模型名
- temperature
- max_tokens
- is_default：设为默认
- enabled：启用

保存后点击“测试连接”。如果后端在 Docker 内访问本机 Ollama，通常要使用：

```text
http://host.docker.internal:11434/v1
```

真实模型配置成功后，需求抽取和响应矩阵生成会使用真实模型；输出仍通过 Pydantic Schema 校验。

## 文件解析支持哪些格式？

当前支持：

- `.txt`
- `.md`
- `.pdf`
- `.docx`
- `.xlsx`

PDF 只支持可复制文本型 PDF，不支持 OCR。扫描版 PDF OCR 是后续规划。

## 如何解释可观测性？

系统有两类日志：

- `AgentRun`：记录工作流节点、输入摘要、输出摘要、耗时、错误和检索器类型。
- `LLMCallLog`：记录模型调用 provider、model_name、prompt_type、耗时、成功状态和错误。

这样可以排查问题来自文件解析、检索、模型调用、Schema 校验还是保存环节。

## Excel / Word 导出的定位是什么？

Excel 是技术响应矩阵，适合内部逐项评审和协作。Word 是投标响应初稿，适合交给方案经理继续编辑。两者都是 AI + 人工复核后的初稿，不是无需审查的最终标书。

## 项目还有哪些后续规划？

明确的后续规划包括：

- OCR 支持扫描版 PDF。
- 更精细的 chunk 切分策略。
- 使用真实 embedding 模型替代 MockEmbeddingProvider。
- 项目级或租户级知识库隔离。
- 更完整的权限系统和审计策略。
- 更复杂的 Agent 分支、重试和人工审批节点。

这些能力当前没有实现，不能在演示中描述为已完成。

