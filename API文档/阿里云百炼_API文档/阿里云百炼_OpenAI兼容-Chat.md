# OpenAI兼容-Chat

- 原文链接：https://help.aliyun.com/document_detail/2833609.html
- 文档ID：2833609
- 抓取时间：2025-11-21T13:40:01+08:00

阿里云百炼的通义千问模型支持 OpenAI 兼容接口，您只需调整 API Key、BASE_URL 和模型名称，即可将原有 OpenAI 代码迁移至阿里云百炼服务使用。兼容 OpenAI 需要信息BASE_URLBASE_URL 表示模型服务的网络访问点或地址。通过该地址，您可以访问服务提供的功能或数据。在 Web 服务或 API 的使用中，BASE_URL 通常对应于服务的具体操作或资源的 URL。当您使用 OpenAI 兼容接口来使用阿里云百炼模型服务时，需要配置 BASE_URL。当您通过 OpenAI SDK 或其他 OpenAI 兼容的 SDK 调用时，需要配置的 BASE_URL 如下：北京：https://dashscope.aliyuncs.com/compatible-mode/v1
新加坡：https://dashscope-intl.aliyuncs.com/compatible-mode/v1当您通过 HTTP 请求调用时，需要配置的完整访问 endpoint 如下：北京：POST https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions
新加坡：POST https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions支持的模型列表当前 OpenAI 兼容接口支持的通义千问系列模型如下表所示。

模型分类模型名称通义千问qwen-longqwq-plusqwq-plus-latestqwq-plus-2025-03-05qwen-maxqwen-max-latestqwen-max-2025-01-25qwen-max-2024-09-19qwen-max-2024-04-28qwen-max-2024-04-03qwen-plusqwen-plus-latestqwen-plus-2025-04-28qwen-plus-2025-01-25qwen-plus-2025-01-12qwen-plus-2024-11-27qwen-plus-2024-11-25qwen-plus-2024-09-19qwen-plus-2024-08-06qwen-plus-2024-07-23qwen-turboqwen-turbo-latestqwen-turbo-2025-04-28qwen-turbo-2025-02-11qwen-turbo-2024-11-01qwen-turbo-2024-09-19qwen-turbo-2024-06-24qwen-math-plusqwen-math-plus-latestqwen-math-plus-2024-09-19qwen-math-plus-2024-08-16qwen-math-turboqwen-math-turbo-latestqwen-math-turbo-2024-09-19qwen-coder-plusqwen-coder-plus-latestqwen-coder-plus-2024-11-06qwen-coder-turboqwen-coder-turbo-latestqwen-coder-turbo-2024-09-19通义千问开源系列qwq-32bqwq-32b-previewqwen3-235b-a22bqwen3-32bqwen3-30b-a3bqwen3-14bqwen3-8bqwen3-4bqwen3-1.7bqwen3-0.6bqwen2.5-14b-instruct-1mqwen2.5-7b-instruct-1mqwen2.5-72b-instructqwen2.5-32b-instructqwen2.5-14b-instructqwen2.5-7b-instructqwen2.5-3b-instructqwen2.5-1.5b-instructqwen2.5-0.5b-instructqwen2.5-math-72b-instructqwen2.5-math-7b-instructqwen2.5-math-1.5b-instructqwen2.5-coder-32b-instructqwen2.5-coder-14b-instructqwen2.5-coder-7b-instructqwen2.5-coder-3b-instructqwen2.5-coder-1.5b-instructqwen2.5-coder-0.5b-instructqwen2-57b-a14b-instructqwen2-72b-instructqwen2-7b-instructqwen2-1.5b-instructqwen2-0.5b-instructqwen1.5-110b-chatqwen1.5-72b-chatqwen1.5-32b-chatqwen1.5-14b-chatqwen1.5-7b-chatqwen1.5-1.8b-chatqwen1.5-0.5b-chatcodeqwen1.5-7b-chat

通过 OpenAI SDK 调用前提条件请确保您的计算机上安装了 Python 环境。请安装最新版 OpenAI SDK。# 如果下述命令报错，请将 pip 替换为 pip3
pip install -U openai您需要开通阿里云百炼模型服务并获得 API-KEY，详情请参考：获取 API Key。我们推荐您将 API-KEY 配置到环境变量中以降低 API-KEY 的泄露风险，配置方法可参考配置 API Key 到环境变量。您也可以在代码中配置 API-KEY，但是泄露风险会提高。请选择您需要使用的模型：支持的模型列表。使用方式您可以参考以下示例来使用 OpenAI SDK 访问百炼服务上的通义千问模型。非流式调用示例from openai import OpenAI
import os

def get_response():
    client = OpenAI(
        # 若没有配置环境变量，请用阿里云百炼API Key将下行替换为：api_key="sk-xxx",
        # 新加坡和北京地域的API Key不同。获取API Key：https://help.aliyun.com/zh/model-studio/get-api-key
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        # 以下是北京地域base_url，如果使用新加坡地域的模型，需要将base_url替换为：https://dashscope-intl.aliyuncs.com/compatible-mode/v1
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    completion = client.chat.completions.create(
        model="qwen-plus",  # 此处以qwen-plus为例，可按需更换模型名称。模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
        messages=[{'role': 'system', 'content': 'You are a helpful assistant.'},
                  {'role': 'user', 'content': '你是谁？'}]
        )
    print(completion.model_dump_json())

if __name__ == '__main__':
    get_response()运行代码可以获得以下结果：{
    "id": "chatcmpl-xxx",
    "choices": [
        {
            "finish_reason": "stop",
            "index": 0,
            "logprobs": null,
            "message": {
                "content": "我是来自阿里云的超大规模预训练模型，我叫通义千问。",
                "role": "assistant",
                "function_call": null,
                "tool_calls": null
            }
        }
    ],
    "created": 1716430652,
    "model": "qwen-plus",
    "object": "chat.completion",
    "system_fingerprint": null,
    "usage": {
        "completion_tokens": 18,
        "prompt_tokens": 22,
        "total_tokens": 40
    }
}流式调用示例from openai import OpenAI
import os


def get_response():
    client = OpenAI(
        # 如果您没有配置环境变量，请用阿里云百炼API Key将下行替换为：api_key="sk-xxx"
        # 新加坡和北京地域的API Key不同。获取API Key：https://help.aliyun.com/zh/model-studio/get-api-key
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        # 以下是北京地域base_url，如果使用新加坡地域的模型，需要将base_url替换为：https://dashscope-intl.aliyuncs.com/compatible-mode/v1
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    completion = client.chat.completions.create(
        model="qwen-plus",  # 此处以qwen-plus为例，可按需更换模型名称。模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
        messages=[{'role': 'system', 'content': 'You are a helpful assistant.'},
                  {'role': 'user', 'content': '你是谁？'}],
        stream=True,
        # 通过以下设置，在流式输出的最后一行展示token使用信息
        stream_options={"include_usage": True}
        )
    for chunk in completion:
        print(chunk.model_dump_json())


if __name__ == '__main__':
    get_response()
运行代码可以获得以下结果：{"id":"chatcmpl-xxx","choices":[{"delta":{"content":"","function_call":null,"role":"assistant","tool_calls":null},"finish_reason":null,"index":0,"logprobs":null}],"created":1719286190,"model":"qwen-plus","object":"chat.completion.chunk","system_fingerprint":null,"usage":null}
{"id":"chatcmpl-xxx","choices":[{"delta":{"content":"我是","function_call":null,"role":null,"tool_calls":null},"finish_reason":null,"index":0,"logprobs":null}],"created":1719286190,"model":"qwen-plus","object":"chat.completion.chunk","system_fingerprint":null,"usage":null}
{"id":"chatcmpl-xxx","choices":[{"delta":{"content":"来自","function_call":null,"role":null,"tool_calls":null},"finish_reason":null,"index":0,"logprobs":null}],"created":1719286190,"model":"qwen-plus","object":"chat.completion.chunk","system_fingerprint":null,"usage":null}
{"id":"chatcmpl-xxx","choices":[{"delta":{"content":"阿里","function_call":null,"role":null,"tool_calls":null},"finish_reason":null,"index":0,"logprobs":null}],"created":1719286190,"model":"qwen-plus","object":"chat.completion.chunk","system_fingerprint":null,"usage":null}
{"id":"chatcmpl-xxx","choices":[{"delta":{"content":"云的大规模语言模型","function_call":null,"role":null,"tool_calls":null},"finish_reason":null,"index":0,"logprobs":null}],"created":1719286190,"model":"qwen-plus","object":"chat.completion.chunk","system_fingerprint":null,"usage":null}
{"id":"chatcmpl-xxx","choices":[{"delta":{"content":"，我叫通义千问。","function_call":null,"role":null,"tool_calls":null},"finish_reason":null,"index":0,"logprobs":null}],"created":1719286190,"model":"qwen-plus","object":"chat.completion.chunk","system_fingerprint":null,"usage":null}
{"id":"chatcmpl-xxx","choices":[{"delta":{"content":"","function_call":null,"role":null,"tool_calls":null},"finish_reason":"stop","index":0,"logprobs":null}],"created":1719286190,"model":"qwen-plus","object":"chat.completion.chunk","system_fingerprint":null,"usage":null}
{"id":"chatcmpl-xxx","choices":[],"created":1719286190,"model":"qwen-plus","object":"chat.completion.chunk","system_fingerprint":null,"usage":{"completion_tokens":16,"prompt_tokens":22,"total_tokens":38}}function call 示例此处以天气查询工具与时间查询工具为例，向您展示通过 OpenAI 接口兼容实现 function call 的功能。示例代码可以实现多轮工具调用。from openai import OpenAI
from datetime import datetime
import json
import os

client = OpenAI(
    # 若没有配置环境变量，请用阿里云百炼API Key将下行替换为：api_key="sk-xxx",
    # 新加坡和北京地域的API Key不同。获取API Key：https://help.aliyun.com/zh/model-studio/get-api-key
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    # 以下是北京地域base_url，如果使用新加坡地域的模型，需要将base_url替换为：https://dashscope-intl.aliyuncs.com/compatible-mode/v1
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",  # 填写DashScope SDK的base_url
)

# 定义工具列表，模型在选择使用哪个工具时会参考工具的name和description
tools = [
    # 工具1 获取当前时刻的时间
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "当你想知道现在的时间时非常有用。",
            # 因为获取当前时间无需输入参数，因此parameters为空字典
            "parameters": {}
        }
    },
    # 工具2 获取指定城市的天气
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "当你想查询指定城市的天气时非常有用。",
            "parameters": { 
                "type": "object",
                "properties": {
                    # 查询天气时需要提供位置，因此参数设置为location
                    "location": {
                        "type": "string",
                        "description": "城市或县区，比如北京市、杭州市、余杭区等。"
                    }
                }
            },
            "required": [
                "location"
            ]
        }
    }
]

# 模拟天气查询工具。返回结果示例：“北京今天是雨天。”
def get_current_weather(location):
    return f"{location}今天是雨天。 "

# 查询当前时间的工具。返回结果示例：“当前时间：2024-04-15 17:15:18。“
def get_current_time():
    # 获取当前日期和时间
    current_datetime = datetime.now()
    # 格式化当前日期和时间
    formatted_time = current_datetime.strftime('%Y-%m-%d %H:%M:%S')
    # 返回格式化后的当前时间
    return f"当前时间：{formatted_time}。"

# 封装模型响应函数
def get_response(messages):
    completion = client.chat.completions.create(
        model="qwen-plus",  # 此处以qwen-plus为例，可按需更换模型名称。模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
        messages=messages,
        tools=tools
        )
    return completion.model_dump()

def call_with_messages():
    print('\n')
    messages = [
            {
                "content": input('请输入：'),  # 提问示例："现在几点了？" "一个小时后几点" "北京天气如何？"
                "role": "user"
            }
    ]
    print("-"*60)
    # 模型的第一轮调用
    i = 1
    first_response = get_response(messages)
    assistant_output = first_response['choices'][0]['message']
    print(f"\n第{i}轮大模型输出信息：{first_response}\n")
    if  assistant_output['content'] is None:
        assistant_output['content'] = ""
    messages.append(assistant_output)
    # 如果不需要调用工具，则直接返回最终答案
    if assistant_output['tool_calls'] == None:  # 如果模型判断无需调用工具，则将assistant的回复直接打印出来，无需进行模型的第二轮调用
        print(f"无需调用工具，我可以直接回复：{assistant_output['content']}")
        return
    # 如果需要调用工具，则进行模型的多轮调用，直到模型判断无需调用工具
    while assistant_output['tool_calls'] != None:
        # 如果判断需要调用查询天气工具，则运行查询天气工具
        if assistant_output['tool_calls'][0]['function']['name'] == 'get_current_weather':
            tool_info = {"name": "get_current_weather", "role":"tool"}
            # 提取位置参数信息
            location = json.loads(assistant_output['tool_calls'][0]['function']['arguments'])['location']
            tool_info['content'] = get_current_weather(location)
        # 如果判断需要调用查询时间工具，则运行查询时间工具
        elif assistant_output['tool_calls'][0]['function']['name'] == 'get_current_time':
            tool_info = {"name": "get_current_time", "role":"tool"}
            tool_info['content'] = get_current_time()
        print(f"工具输出信息：{tool_info['content']}\n")
        print("-"*60)
        messages.append(tool_info)
        assistant_output = get_response(messages)['choices'][0]['message']
        if  assistant_output['content'] is None:
            assistant_output['content'] = ""
        messages.append(assistant_output)
        i += 1
        print(f"第{i}轮大模型输出信息：{assistant_output}\n")
    print(f"最终答案：{assistant_output['content']}")

if __name__ == '__main__':
    call_with_messages()当输入：杭州和北京天气怎么样？现在几点了？时，程序会进行如下输出：输入参数配置输入参数与 OpenAI 的接口参数对齐，当前已支持的参数如下：

参数类型默认值说明modelstring-用户使用 model 参数指明对应的模型，可选的模型请见支持的模型列表。messagesarray-用户与模型的对话历史。array 中的每个元素形式为{"role":角色, "content": 内容}。角色当前可选值：system、user、assistant，其中，仅messages[0]中支持 role 为 system，一般情况下，user 和 assistant 需要交替出现，且 messages 中最后一个元素的 role 必须为 user。top_p（可选）float-生成过程中的核采样方法概率阈值，例如，取值为 0.8 时，仅保留概率加起来大于等于 0.8 的最可能 token 的最小集合作为候选集。取值范围为（0,1.0)，取值越大，生成的随机性越高；取值越小，生成的确定性越高。temperature（可选）float-用于控制模型回复的随机性和多样性。具体来说，temperature 值控制了生成文本时对每个候选词的概率分布进行平滑的程度。较高的 temperature 值会降低概率分布的峰值，使得更多的低概率词被选择，生成结果更加多样化；而较低的 temperature 值则会增强概率分布的峰值，使得高概率词更容易被选择，生成结果更加确定。取值范围： [0, 2)，不建议取值为 0，无意义。presence_penalty（可选）float-用户控制模型生成时整个序列中的重复度。提高 presence_penalty 时可以降低模型生成的重复度，取值范围[-2.0, 2.0]。说明 目前仅在千问商业模型和 qwen1.5 及以后的开源模型上支持该参数。n（可选）integer1生成响应的个数，取值范围是1-4。对于需要生成多个响应的场景（如创意写作、广告文案等），可以设置较大的 n 值。设置较大的 n 值不会增加输入 Token 消耗，会增加输出 Token 的消耗。当前仅支持 qwen-plus 模型，且在传入 tools 参数时固定为 1。max_tokens（可选）integer-指定模型可生成的最大 token 个数。例如模型最大输出长度为 2k，您可以设置为 1k，防止模型输出过长的内容。不同的模型有不同的输出上限，具体请参见模型列表。seed（可选）integer-生成时使用的随机数种子，用于控制模型生成内容的随机性。seed 支持无符号 64 位整数。stream（可选）booleanFalse用于控制是否使用流式输出。当以 stream 模式输出结果时，接口返回结果为 generator，需要通过迭代获取结果，每次输出为当前生成的增量序列。stop（可选）string or arrayNonestop 参数用于实现内容生成过程的精确控制，在模型生成的内容即将包含指定的字符串或 token_id 时自动停止。stop 可以为 string 类型或 array 类型。string 类型当模型将要生成指定的 stop 词语时停止。例如将 stop 指定为"你好"，则模型将要生成“你好”时停止。array 类型array 中的元素可以为 token_id 或者字符串，或者元素为 token_id 的 array。当模型将要生成的 token 或其对应的 token_id 在 stop 中时，模型生成将会停止。以下为 stop 为 array 时的示例（tokenizer 对应模型为 qwen-turbo）：1.元素为 token_id：token_id 为 108386 和 104307 分别对应 token 为“你好”和“天气”，设定 stop 为[108386,104307]，则模型将要生成“你好”或者“天气”时停止。2.元素为字符串：设定 stop 为["你好","天气"]，则模型将要生成“你好”或者“天气”时停止。3.元素为 array：token_id 为 108386 和 103924 分别对应 token 为“你好”和“啊”，token_id 为 35946 和 101243 分别对应 token 为“我”和“很好”。设定 stop 为[[108386, 103924],[35946, 101243]]，则模型将要生成“你好啊”或者“我很好”时停止。说明 stop 为 array 类型时，不可以将 token_id 和字符串同时作为元素输入，比如不可以指定 stop 为["你好",104307]。tools（可选）arrayNone用于指定可供模型调用的工具库，一次 function call 流程模型会从中选择其中一个工具。tools 中每一个 tool 的结构如下：type，类型为 string，表示 tools 的类型，当前仅支持 function。function，类型为 object，键值包括 name，description 和 parameters：name：类型为 string，表示工具函数的名称，必须是字母、数字，可以包含下划线和短划线，最大长度为 64。description：类型为 string，表示工具函数的描述，供模型选择何时以及如何调用工具函数。parameters：类型为 object，表示工具的参数描述，需要是一个合法的 JSON Schema。JSON Schema 的描述可以见链接。如果 parameters 参数为空，表示 function 没有入参。在 function call 流程中，无论是发起 function call 的轮次，还是向模型提交工具函数的执行结果，均需设置 tools 参数。当前支持的模型包括 qwen-turbo、qwen-plus 和 qwen-max。说明 tools 暂时无法与 stream=True 同时使用。stream_options（可选）objectNone该参数用于配置在流式输出时是否展示使用的 token 数目。只有当 stream 为 True 的时候该参数才会激活生效。若您需要统计流式输出模式下的 token 数目，可将该参数配置为stream_options={"include_usage":True}。enable_searchbooleanFalse用于控制模型在生成文本时是否使用互联网搜索结果进行参考。取值如下：True：启用互联网搜索，模型会将搜索结果作为文本生成过程中的参考信息，但模型会基于其内部逻辑判断是否使用互联网搜索结果。如果模型没有搜索互联网，建议优化 Prompt，或设置search_options中的forced_search参数开启强制搜索。False（默认）：关闭互联网搜索。qwen-long 暂不支持此参数。配置方式为：extra_body={"enable_search": True}。

返回参数说明

返回参数数据类型说明备注idstring系统生成的标识本次调用的 id。无modelstring本次调用的模型名。无system_fingerprintstring模型运行时使用的配置版本，当前暂时不支持，返回为空字符串“”。无choicesarray模型生成内容的详情。无choices[i].finish_reasonstring有三种情况：正在生成时为 null；因触发输入参数中的 stop 条件而结束为 stop；因生成长度过长而结束为 length。choices[i].messageobject模型输出的消息。choices[i].message.rolestring模型的角色，固定为 assistant。choices[i].message.contentstring模型生成的文本。choices[i].indexinteger生成的结果序列编号，默认为 0。createdinteger当前生成结果的时间戳（s）。无usageobject计量信息，表示本次请求所消耗的 token 数据。无usage.prompt_tokensinteger用户输入文本转换成 token 后的长度。无usage.completion_tokensinteger模型生成回复转换为 token 后的长度。无usage.total_tokensintegerusage.prompt_tokens 与 usage.completion_tokens 的总和。无

通过 langchain_openai SDK 调用前提条件请确保您的计算机上安装了 Python 环境。通过运行以下命令安装 langchain_openai SDK。# 如果下述命令报错，请将 pip 替换为 pip3
pip install -U langchain_openai您需要开通阿里云百炼模型服务并获得 API-KEY，详情请参考：获取 API Key。我们推荐您将 API-KEY 配置到环境变量中以降低 API-KEY 的泄露风险，详情可参考配置 API Key 到环境变量。您也可以在代码中配置 API-KEY，但是泄露风险会提高。请选择您需要使用的模型：支持的模型列表。使用方式您可以参考以下示例来通过 langchain_openai SDK 使用阿里云百炼的千问模型。非流式输出非流式输出使用 invoke 方法实现，请参考以下示例代码：from langchain_openai import ChatOpenAI
import os

def get_response():
    llm = ChatOpenAI(
        # 若没有配置环境变量，请用阿里云百炼API Key将下行替换为：api_key="sk-xxx",
        # 新加坡和北京地域的API Key不同。获取API Key：https://help.aliyun.com/zh/model-studio/get-api-key
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        # 以下是北京地域base_url，如果使用新加坡地域的模型，需要将base_url替换为：https://dashscope-intl.aliyuncs.com/compatible-mode/v1
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        model="qwen-plus"    # 此处以qwen-plus为例，可按需更换模型名称。模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
        )
    messages = [
        {"role":"system","content":"You are a helpful assistant."}, 
        {"role":"user","content":"你是谁？"}
    ]
    response = llm.invoke(messages)
    print(response.json())

if __name__ == "__main__":
    get_response()运行代码，可以得到以下结果：{
    "content": "我是来自阿里云的大规模语言模型，我叫通义千问。",
    "additional_kwargs": {},
    "response_metadata": {
        "token_usage": {
            "completion_tokens": 16,
            "prompt_tokens": 22,
            "total_tokens": 38
        },
        "model_name": "qwen-plus",
        "system_fingerprint": "",
        "finish_reason": "stop",
        "logprobs": null
    },
    "type": "ai",
    "name": null,
    "id": "run-xxx",
    "example": false,
    "tool_calls": [],
    "invalid_tool_calls": []
}流式输出流式输出使用 stream 方法实现，无需在参数中配置 stream 参数。from langchain_openai import ChatOpenAI
import os

def get_response():
    llm = ChatOpenAI(
        # 若没有配置环境变量，请用阿里云百炼API Key将下行替换为：api_key="sk-xxx",
        # 新加坡和北京地域的API Key不同。获取API Key：https://help.aliyun.com/zh/model-studio/get-api-key
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        # 以下是北京地域base_url，如果使用新加坡地域的模型，需要将base_url替换为：https://dashscope-intl.aliyuncs.com/compatible-mode/v1
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1", 
        model="qwen-plus",  # 此处以qwen-plus为例，可按需更换模型名称。模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
        stream_usage=True
        )
    messages = [
        {"role":"system","content":"You are a helpful assistant."}, 
        {"role":"user","content":"你是谁？"},
    ]
    response = llm.stream(messages)
    for chunk in response:
        print(chunk.model_dump_json())

if __name__ == "__main__":
    get_response()运行代码，可以得到以下结果：{"content": "", "additional_kwargs": {}, "response_metadata": {}, "type": "AIMessageChunk", "name": null, "id": "run-xxx", "example": false, "tool_calls": [], "invalid_tool_calls": [], "usage_metadata": null, "tool_call_chunks": []}
{"content": "我是", "additional_kwargs": {}, "response_metadata": {}, "type": "AIMessageChunk", "name": null, "id": "run-xxx", "example": false, "tool_calls": [], "invalid_tool_calls": [], "usage_metadata": null, "tool_call_chunks": []}
{"content": "来自", "additional_kwargs": {}, "response_metadata": {}, "type": "AIMessageChunk", "name": null, "id": "run-xxx", "example": false, "tool_calls": [], "invalid_tool_calls": [], "usage_metadata": null, "tool_call_chunks": []}
{"content": "阿里", "additional_kwargs": {}, "response_metadata": {}, "type": "AIMessageChunk", "name": null, "id": "run-xxx", "example": false, "tool_calls": [], "invalid_tool_calls": [], "usage_metadata": null, "tool_call_chunks": []}
{"content": "云", "additional_kwargs": {}, "response_metadata": {}, "type": "AIMessageChunk", "name": null, "id": "run-xxx", "example": false, "tool_calls": [], "invalid_tool_calls": [], "usage_metadata": null, "tool_call_chunks": []}
{"content": "的大规模语言模型", "additional_kwargs": {}, "response_metadata": {}, "type": "AIMessageChunk", "name": null, "id": "run-xxx", "example": false, "tool_calls": [], "invalid_tool_calls": [], "usage_metadata": null, "tool_call_chunks": []}
{"content": "，我叫通", "additional_kwargs": {}, "response_metadata": {}, "type": "AIMessageChunk", "name": null, "id": "run-xxx", "example": false, "tool_calls": [], "invalid_tool_calls": [], "usage_metadata": null, "tool_call_chunks": []}
{"content": "义千问。", "additional_kwargs": {}, "response_metadata": {}, "type": "AIMessageChunk", "name": null, "id": "run-xxx", "example": false, "tool_calls": [], "invalid_tool_calls": [], "usage_metadata": null, "tool_call_chunks": []}
{"content": "", "additional_kwargs": {}, "response_metadata": {"finish_reason": "stop"}, "type": "AIMessageChunk", "name": null, "id": "run-xxx", "example": false, "tool_calls": [], "invalid_tool_calls": [], "usage_metadata": null, "tool_call_chunks": []}
{"content": "", "additional_kwargs": {}, "response_metadata": {}, "type": "AIMessageChunk", "name": null, "id": "run-xxx", "example": false, "tool_calls": [], "invalid_tool_calls": [], "usage_metadata": {"input_tokens": 22, "output_tokens": 16, "total_tokens": 38}, "tool_call_chunks": []}关于输入参数的配置，可以参考输入参数配置，相关参数在 ChatOpenAI 对象中定义。通过 HTTP 接口调用您可以通过 HTTP 接口来调用阿里云百炼服务，获得与通过 HTTP 接口调用 OpenAI 服务相同结构的返回结果。前提条件您需要开通阿里云百炼模型服务并获得 API-KEY，详情请参考：获取 API Key。我们推荐您将 API-KEY 配置到环境变量中以降低 API-KEY 的泄露风险，配置方法可参考配置 API Key 到环境变量。您也可以在代码中配置 API-KEY，但是泄露风险会提高。提交接口调用北京：POST https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions
新加坡：POST https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions请求示例以下示例展示通过cURL命令来调用 API 的脚本。说明 如果您没有配置 API-KEY 为环境变量，需将$DASHSCOPE_API_KEY 更改为您的 API-KEY。非流式输出curl# ======= 重要提示 =======
# 新加坡和北京地域的API Key不同。获取API Key：https://help.aliyun.com/zh/model-studio/get-api-key
# 以下是北京地域base_url，如果使用新加坡地域的模型，需要将base_url替换为：https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions
# === 执行时请删除该注释 ===
curl --location 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions' \
--header "Authorization: Bearer $DASHSCOPE_API_KEY" \
--header 'Content-Type: application/json' \
--data '{
    "model": "qwen-plus",  
    "messages": [
        {
            "role": "system",
            "content": "You are a helpful assistant."
        },
        {
            "role": "user", 
            "content": "你是谁？"
        }
    ]
}'
运行命令可得到以下结果：{
    "choices": [
        {
            "message": {
                "role": "assistant",
                "content": "我是来自阿里云的大规模语言模型，我叫通义千问。"
            },
            "finish_reason": "stop",
            "index": 0,
            "logprobs": null
        }
    ],
    "object": "chat.completion",
    "usage": {
        "prompt_tokens": 11,
        "completion_tokens": 16,
        "total_tokens": 27
    },
    "created": 1715252778,
    "system_fingerprint": "",
    "model": "qwen-plus",
    "id": "chatcmpl-xxx"
}流式输出如果您需要使用流式输出，请在请求体中指定 stream 参数为 true。# ======= 重要提示 =======
# 新加坡和北京地域的API Key不同。获取API Key：https://help.aliyun.com/zh/model-studio/get-api-key
# 以下是北京地域base_url，如果使用新加坡地域的模型，需要将base_url替换为：https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions
# === 执行时请删除该注释 ===
curl --location 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions' \
--header "Authorization: Bearer $DASHSCOPE_API_KEY" \
--header 'Content-Type: application/json' \
--data '{
    "model": "qwen-plus",  
    "messages": [
        {
            "role": "system",
            "content": "You are a helpful assistant."
        },
        {
            "role": "user", 
            "content": "你是谁？"
        }
    ],
    "stream":true
}'运行命令可得到以下结果：data: {"choices":[{"delta":{"content":"","role":"assistant"},"index":0,"logprobs":null,"finish_reason":null}],"object":"chat.completion.chunk","usage":null,"created":1715931028,"system_fingerprint":null,"model":"qwen-plus","id":"chatcmpl-3bb05cf5cd819fbca5f0b8d67a025022"}

data: {"choices":[{"finish_reason":null,"delta":{"content":"我是"},"index":0,"logprobs":null}],"object":"chat.completion.chunk","usage":null,"created":1715931028,"system_fingerprint":null,"model":"qwen-plus","id":"chatcmpl-3bb05cf5cd819fbca5f0b8d67a025022"}

data: {"choices":[{"delta":{"content":"来自"},"finish_reason":null,"index":0,"logprobs":null}],"object":"chat.completion.chunk","usage":null,"created":1715931028,"system_fingerprint":null,"model":"qwen-plus","id":"chatcmpl-3bb05cf5cd819fbca5f0b8d67a025022"}

data: {"choices":[{"delta":{"content":"阿里"},"finish_reason":null,"index":0,"logprobs":null}],"object":"chat.completion.chunk","usage":null,"created":1715931028,"system_fingerprint":null,"model":"qwen-plus","id":"chatcmpl-3bb05cf5cd819fbca5f0b8d67a025022"}

data: {"choices":[{"delta":{"content":"云的大规模语言模型"},"finish_reason":null,"index":0,"logprobs":null}],"object":"chat.completion.chunk","usage":null,"created":1715931028,"system_fingerprint":null,"model":"qwen-plus","id":"chatcmpl-3bb05cf5cd819fbca5f0b8d67a025022"}

data: {"choices":[{"delta":{"content":"，我叫通义千问。"},"finish_reason":null,"index":0,"logprobs":null}],"object":"chat.completion.chunk","usage":null,"created":1715931028,"system_fingerprint":null,"model":"qwen-plus","id":"chatcmpl-3bb05cf5cd819fbca5f0b8d67a025022"}

data: {"choices":[{"delta":{"content":""},"finish_reason":"stop","index":0,"logprobs":null}],"object":"chat.completion.chunk","usage":null,"created":1715931028,"system_fingerprint":null,"model":"qwen-plus","id":"chatcmpl-3bb05cf5cd819fbca5f0b8d67a025022"}

data: [DONE]
输入参数的详情请参考输入参数配置。异常响应示例在访问请求出错的情况下，输出的结果中会通过 code 和 message 指明出错原因。{
    "error": {
        "message": "Incorrect API key provided. ",
        "type": "invalid_request_error",
        "param": null,
        "code": "invalid_api_key"
    }
}状态码说明

错误码说明400 - Invalid Request Error输入请求错误，细节请参见具体报错信息。401 - Incorrect API key providedAPI key 不正确。429 - Rate limit reached for requestsQPS、QPM 等超限。429 - You exceeded your current quota, please check your plan and billing details额度超限或者欠费。500 - The server had an error while processing your request服务端错误。503 - The engine is currently overloaded, please try again later服务端负载过高，可重试。
