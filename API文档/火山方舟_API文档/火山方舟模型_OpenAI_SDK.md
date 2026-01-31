火山方舟模型 API 大部分兼容 OpenAI SDK。您通过少量代码更改，很方便地方舟的模型服务集成至已有的代码中。
:::tip
社区第三方 SDK 不由火山引擎团队维护，本文仅供参考。
:::
<span id="509924d1"></span>
# 前提条件
* [获取 API Key](https://console.volcengine.com/ark/region:ark+cn-beijing/apiKey) 
* [开通模型服务](https://console.volcengine.com/ark/openManagement)
* 在 [模型列表](/docs/82379/1330310) 获取所需 Model ID 
   * 通过 Endpoint ID 调用模型服务，请参考 [获取 Endpoint ID（创建自定义推理接入点）](/docs/82379/1099522)。

<span id="fe0e81ca"></span>
# OpenAI SDK

* Python版本：3.7及以上。
* OpenAI SDK：1.0版本及以上，安装命令：

```Python
pip install --upgrade "openai>=1.0"
```

<span id="0569f4fe"></span>
## 快速开始示例
```Python
from openai import OpenAI
import os

client = OpenAI(   
    # The base URL for model invocation . 
    base_url="https://ark.cn-beijing.volces.com/api/v3",   
    # 环境变量中配置您的API Key 
    api_key=os.environ.get("ARK_API_KEY"), 
)

completion = client.chat.completions.create(
    # Replace with Model ID . 
    model="doubao-seed-1-6-251015", 
    messages = [
        {"role": "user", "content": "Hello"},
    ],
)
print(completion.choices[0].message.content)
```

<span id="922db236"></span>
## 设置额外字段
传入OpenAI SDK中不支持的字段，可以通过 **extra_body** 字典传入，如开关模型是否深度思考的 **thinking** 字段。
```Python
from openai import OpenAI
import os

client = OpenAI(   
    # The base URL for model invocation . 
    base_url="https://ark.cn-beijing.volces.com/api/v3",  
    # 环境变量中配置您的API Key 
    api_key=os.environ.get("ARK_API_KEY"), 
)

completion = client.chat.completions.create(
    # Replace with Model ID .
    model="doubao-seed-1-6-251015", 
    messages = [
        {"role": "user", "content": "Hello"},
    ],
    extra_body={
         "thinking": {
             "type": "disabled", # 不使用深度思考能力
             # "type": "enabled", # 使用深度思考能力
         }
     }
)
print(completion.choices[0].message.content)
```

<span id="1cd60a34"></span>
## 设置自定义header
可以用于传递额外信息，如配置 ID来串联日志，使能数据加密能力。
```Python
from openai import OpenAI
import os

client = OpenAI(   
    # The base URL for model invocation . 
    base_url="https://ark.cn-beijing.volces.com/api/v3",  
    # 环境变量中配置您的API Key 
    api_key=os.environ.get("ARK_API_KEY"), 
)

completion = client.chat.completions.create(
    # Replace with Model ID .
    model="doubao-seed-1-6-251015", 
    messages = [
        {"role": "user", "content": "Hello"},
    ],
    # 自定义request id
    extra_headers={"X-Client-Request-Id": "202406251728190000B7EA7A9648AC08D9"}
)
print(completion.choices[0].message.content)
```

<span id="ab87fab7"></span>
## 文本向量化 Embedding
:::warning
 [多模态向量化能力](/docs/82379/1330310#ee5ec35c)模型不支持 OpenAI API ，如需使用请使用 方舟 SDK，详情请参考[多模态向量化](/docs/82379/1409291)。
:::
```Python
from openai import OpenAI
import os

client = OpenAI(   
    # The base URL for model invocation . 
    base_url="https://ark.cn-beijing.volces.com/api/v3",  
    # 环境变量中配置您的API Key 
    api_key=os.environ.get("ARK_API_KEY"), 
)

resp = client.embeddings.create(
    # Replace with Model ID .
    model="doubao-embedding-large-text-240915", 
    input=["Nice day."]
)
print(resp)
```

<span id="697a06ce"></span>
# LangChain OpenAI SDK
安装 LangChain OpenAI SDK：
```Python
pip install langchain-openai
```

<span id="2bcdd714"></span>
## 示例代码
```Python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
import os

llm = ChatOpenAI(
    # 环境变量中配置您的API Key       
    openai_api_key=os.environ.get("ARK_API_KEY"), 
    # The base URL for model invocation
    openai_api_base="https://ark.cn-beijing.volces.com/api/v3",   
    # Replace with Model ID
    model="doubao-seed-1-6-251015", 
)

template = """Question: {question}

Answer: Let's think step by step."""

prompt = PromptTemplate.from_template(template)

question = "What NFL team won the Super Bowl in the year Justin Beiber was born?"

llm_chain = prompt | llm

print(llm_chain.invoke(question))
```

