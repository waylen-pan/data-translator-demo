Gemini SDK 调用指南
快速开始

1. 安装与配置

pip install google-genai

from google import genai
from google.genai import types

# 配置客户端
client = genai.Client(
    http_options=types.HttpOptions(
        base_url="https://litellm-staging-global.nicebuild.click"
    ),
    api_key="your-api-key"
)

2. 基本调用

# 简单调用（使用默认思考）
response = client.models.generate_content(
    model="gemini-2.5-flash",  # 或 "gemini-2.5-pro"
    contents="你的问题"
)

print(response.text)

3. 设置思考预算

# 配置思考预算
config = types.GenerateContentConfig(
    thinking_config=types.ThinkingConfig(
        thinking_budget=8192  # 思考token数量
    )
)

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="你的问题",
    config=config
)

思考预算建议：
- 0 - 关闭思考（仅Flash支持）
- 128 - 最小思考
- 1024 - 小预算
- 8192 - 大预算
  
4. 获取Token消耗

# 获取使用统计
usage = response.usage_metadata

tokens = {
    "输入Token": usage.prompt_token_count,           # 用户输入消耗
    "输出Token": usage.candidates_token_count,       # 模型回答消耗
    "思考Token": usage.thoughts_token_count,         # 模型思考消耗（可能为None）
    "总Token": usage.total_token_count               # 总消耗
}

print(f"总Token: {tokens['总Token']}")
print(f"输入: {tokens['输入Token']}, 输出: {tokens['输出Token']}, 思考: {tokens['思考Token']}")

5. 完整示例

from google import genai
from google.genai import types

client = genai.Client(
    http_options=types.HttpOptions(base_url="https://litellm-staging-global.nicebuild.click"),
    api_key="your-api-key"
)

# 调用并获取token统计
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="解释什么是人工智能",
    config=types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_budget=1024)
    )
)

# 输出结果和统计
print("回答:", response.text)
print(f"Token消耗 - 输入:{response.usage_metadata.prompt_token_count}, "
      f"输出:{response.usage_metadata.candidates_token_count}, "
      f"思考:{response.usage_metadata.thoughts_token_count}, "
      f"总计:{response.usage_metadata.total_token_count}")

模型选择

- gemini-2.5-flash: 快速响应，支持关闭思考（budget=0）
- gemini-2.5-pro: 更强性能，最小思考预算128
  
注意事项

1. thoughts_token_count 可能为 None（未使用思考时）
2. total_token_count = prompt_token_count + candidates_token_count + thoughts_token_count（如有）
3. Base URL 末尾不需要 /v1beta，SDK会自动添加

Claude SDK 调用指南（litellm）

快速开始

1. 安装与配置（要求 `anthropic>=0.75.0`）

pip install anthropic

import os
from anthropic import AsyncAnthropic

# 配置客户端（默认直连官方 https://api.anthropic.com，可按需改成 litellm 代理）
client = AsyncAnthropic(
    api_key="your-api-key",
    base_url=os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
)

2. 基本调用

# 简单调用（关闭思考）
response = await client.messages.create(
    model="claude-haiku-4-5@20251001",  # 或 "claude-sonnet-4-5@20250929"
    max_tokens=2048,
    messages=[{"role": "user", "content": "你的问题"}]
)

# 提取文本
text = ""
for block in response.content:
    if hasattr(block, 'text'):
        text += block.text

3. 设置思考预算

# 启用思考
response = await client.messages.create(
    model="claude-haiku-4-5@20251001",
    max_tokens=4096,
    thinking={
        "type": "enabled",
        "budget_tokens": 1024  # 思考token预算
    },
    messages=[{"role": "user", "content": "你的问题"}]
)

思考预算说明：
- 关闭思考：不传 thinking 参数
- 启用思考：设置 budget_tokens（推荐 1024、2048、4096 等）
  
4. 获取Token消耗

# 获取使用统计
usage = response.usage

tokens = {
    "输入Token": usage.input_tokens,      # 用户输入消耗
    "输出Token": usage.output_tokens,     # 模型回答消耗（包含思考+回答）
    "总Token": usage.input_tokens + usage.output_tokens
}

print(f"总Token: {tokens['总Token']}")
print(f"输入: {tokens['输入Token']}, 输出: {tokens['输出Token']}")

重要说明：
- output_tokens **统一包含**思考token和正式回答token，不单独计算
- 即使有 ThinkingBlock，也只有一个 output_tokens 字段
  
5. 完整示例

from anthropic import AsyncAnthropic

client = AsyncAnthropic(
    api_key="your-api-key",
    base_url="https://litellm-staging-global.nicebuild.click"
)

# 调用并获取token统计
response = await client.messages.create(
    model="claude-sonnet-4-5@20250929",
    max_tokens=4096,
    thinking={"type": "enabled", "budget_tokens": 1024},
    messages=[{"role": "user", "content": "解释什么是AI"}]
)

# 提取文本
text = "".join(block.text for block in response.content if hasattr(block, 'text'))

# 输出统计
print(f"回答: {text}")
print(f"Token消耗 - 输入:{response.usage.input_tokens}, "
      f"输出:{response.usage.output_tokens}, "
      f"总计:{response.usage.input_tokens + response.usage.output_tokens}")

模型选择

- claude-haiku-4-5@20251001: 快速响应，成本低
- claude-sonnet-4-5@20250929: 更强性能，适合复杂任务
  
注意事项

1. Base URL 不需要 /v1 后缀，SDK会自动处理
2. output_tokens 包含所有输出（思考+回答），不单独计费
3. max_tokens 需要足够大以容纳思考预算+回答长度
4. 使用异步客户端 AsyncAnthropic 支持并发调用

Claude Agent SDK 调用指南（litellm）

快速开始

1. 安装与配置（要求 `claude-agent-sdk` 已安装）

pip install claude-agent-sdk

# 建议使用环境变量，避免硬编码密钥
export ANTHROPIC_API_KEY="your-api-key"
export ANTHROPIC_BASE_URL="https://litellm-staging-global.nicebuild.click"

2. 基本调用（最小权限）

import os
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, TextBlock, ResultMessage

async def main():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("请先设置 ANTHROPIC_API_KEY")
    base_url = os.getenv("ANTHROPIC_BASE_URL", "https://litellm-staging-global.nicebuild.click")

    options = ClaudeAgentOptions(
        model="claude-opus-4-5@20251101",
        env={
            "ANTHROPIC_API_KEY": api_key,
            "ANTHROPIC_BASE_URL": base_url
        },
        allowed_tools=[],  # 最小权限，避免读写文件/执行命令
        max_turns=1        # 限制对话轮数，控制成本
    )

    async for message in query(prompt="只回复 OK", options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text)
        if isinstance(message, ResultMessage):
            print(f"result={message.subtype} error={message.is_error} cost={message.total_cost_usd}")

asyncio.run(main())

模型选择

- 模型名与 Claude SDK 一致，例如：claude-haiku-4-5@20251001 / claude-sonnet-4-5@20250929 / claude-opus-4-5@20251101

注意事项

1. Agent SDK 没有 base_url 参数，必须通过 ClaudeAgentOptions.env 传入
2. Base URL 不要带 /v1 后缀（否则会形成 /v1/v1/... 导致 404）
3. 默认不加载本地设置，保证可复现；如需读取 CLAUDE.md，请设置 setting_sources=["project"] 并使用系统预设
4. 需要分析中间产物时再开启工具权限，并限定 cwd/add_dirs 范围

OpenAI SDK 调用指南（litellm）

快速开始

1. 安装与配置

pip install openai

from openai import OpenAI

# 配置客户端
client = OpenAI(
    api_key="your-api-key",
    base_url="https://litellm-staging-global.nicebuild.click",
    default_query={"api-version": "2025-03-01-preview"}
)

2. 两种API方式

方式一：Chat Completions API（传统）

# 调用模型
completion = client.chat.completions.create(
    model="gpt-5",  # 或 "gpt-5-mini"
    messages=[
        {"role": "user", "content": "你的问题"}
    ],
    reasoning_effort="low"  # 思考力度: "low", "medium", "high"
)

# 获取结果
text = completion.choices[0].message.content

方式二：Responses API（推荐）

# 调用模型
response = client.responses.create(
    model="gpt-5",  # 或 "gpt-5-mini"
    input="你的问题",
    reasoning={
        "effort": "low"  # 思考力度: "minimal", "low", "medium", "high"
    }
)

# 获取结果
text = response.output_text

3. 设置思考力度

Chat Completions API:
reasoning_effort="minimal"     # 最小
reasoning_effort="low"     # 低
reasoning_effort="medium"  # 中
reasoning_effort="high"    # 高

Responses API:
reasoning={"effort": "minimal"}  # 最小
reasoning={"effort": "low"}      # 低
reasoning={"effort": "medium"}   # 中
reasoning={"effort": "high"}     # 高

4. 获取Token消耗

Chat Completions API

usage = completion.usage

tokens = {
    "输入Token": usage.prompt_tokens,           # 用户输入
    "输出Token": usage.completion_tokens,       # 模型输出（包含reasoning+text）
    "总Token": usage.total_tokens,
    "思考Token": usage.completion_tokens_details.reasoning_tokens  # 思考部分
}

print(f"总Token: {tokens['总Token']}")
print(f"输入: {tokens['输入Token']}, 输出: {tokens['输出Token']}, 其中思考: {tokens['思考Token']}")

Responses API

usage = response.usage

tokens = {
    "输入Token": usage.input_tokens,                    # 用户输入
    "输出Token": usage.output_tokens,                   # 模型输出（包含reasoning+text）
    "总Token": usage.total_tokens,
    "思考Token": usage.output_tokens_details.reasoning_tokens  # 思考部分
}

print(f"总Token: {tokens['总Token']}")
print(f"输入: {tokens['输入Token']}, 输出: {tokens['输出Token']}, 其中思考: {tokens['思考Token']}")

重要说明：
- output_tokens/completion_tokens **包含**所有输出（reasoning + text）
- reasoning_tokens 在 details 中单独统计，但**已包含**在总输出token中
- 计费按总的 output_tokens/completion_tokens 计算
  
5. 完整示例

from openai import OpenAI

client = OpenAI(
    api_key="your-api-key",
    base_url="https://litellm-staging-global.nicebuild.click",
    default_query={"api-version": "2025-03-01-preview"}
)

# 使用 Responses API（推荐）
response = client.responses.create(
    model="gpt-5",
    input="解释什么是人工智能",
    reasoning={"effort": "medium"}
)

# 输出结果和统计
print(f"回答: {response.output_text}")
print(f"Token消耗 - 输入:{response.usage.input_tokens}, "
      f"输出:{response.usage.output_tokens}, "
      f"思考:{response.usage.output_tokens_details.reasoning_tokens}, "
      f"总计:{response.usage.total_tokens}")

模型选择

- gpt-5: 最强性能
- gpt-5-mini: 快速响应，成本低
  
注意事项

1. 推荐使用 **Responses API**，功能更强大
2. reasoning_tokens 包含在 output_tokens 中，不是额外计费
3. Base URL 不需要 /v1 后缀
4. 必须设置 default_query={"api-version": "2025-03-01-preview"}
