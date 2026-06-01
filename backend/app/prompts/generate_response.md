请根据 RFP 需求和检索到的企业产品知识库内容生成技术响应矩阵项。

match_status 只能是 satisfied、partial、unsupported。
risk_level 只能是 low、medium、high。
source_chunks 只能引用提供的 retrieved_chunks。

输出必须符合以下 JSON Schema：

```json
{output_schema}
```

RFP 需求：

检索到的知识库片段与需求上下文：

```json
{{
  "requirement": {requirement},
  "retrieved_chunks": {retrieved_chunks}
}}
```
