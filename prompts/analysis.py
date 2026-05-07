"""Prompt 模板：需求分析

用于从原始需求文本中提取结构化信息，为后续测试用例生成提供输入。
"""

# 提取项目名称的简短 prompt
PROJECT_NAME_PROMPT = """请从以下需求文档中提取一个简短的项目名称（不超过10个字），用于文件命名。
只输出名称，不要输出其他内容。

需求文档：
{content}"""

# 深度分析需求的 prompt，输出结构化 JSON
ANALYSIS_PROMPT = """你是一位资深需求分析师。请对以下需求文档进行深度分析，逐项提取关键信息。

## 需求文档内容
{content}

## 请按以下维度分析，以 JSON 格式输出：

```json
{{
  "project_name": "需求名称（简短，用于文件命名）",
  "modules": [
    {{
      "name": "功能模块名称",
      "description": "模块功能简述",
      "fields": [
        {{
          "name": "字段名",
          "type": "字段类型（下拉/输入框/单选等）",
          "required": true,
          "enum_values": ["枚举值1", "枚举值2"],
          "default": "默认值"
        }}
      ],
      "linkage_rules": ["联动规则描述"],
      "data_flow": "数据流向描述"
    }}
  ],
  "sync_mappings": [
    {{
      "source_field": "源系统字段",
      "target_field": "目标系统字段",
      "mapping_values": {{"源值": "目标值"}}
    }}
  ],
  "regression_points": ["需要回归验证的原有功能点"],
  "constraints": ["业务约束条件"]
}}
```

请确保分析全面、准确，不要遗漏任何字段或规则。"""
