import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from dotenv import load_dotenv


def main():
    load_dotenv(Path(__file__).with_name(".env"), encoding="utf-8-sig")
    api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    if not api_key:
        print("请先在 .env 中填写 DEEPSEEK_API_KEY。")
        return 1

    question = "请用一句话说明：什么是 AI Agent？"
    payload = {
        "model": "deepseek-flash",
        "messages": [
            {"role": "system", "content": "你是一位使用中文、回答简洁的编程老师。"},
            {"role": "user", "content": question},
        ],
        "thinking": {"type": "disabled"},
        "max_tokens": 128,
        "stream": False,
    }
    request = Request(
        "https://api.deepseek.com/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    print("发送问题：", question)
    try:
        with urlopen(request, timeout=30) as response:
            result = json.load(response)
        answer = result["choices"][0]["message"]["content"]
        if not isinstance(answer, str) or not answer.strip():
            raise ValueError("Empty answer")
    except HTTPError as error:
        print(f"DeepSeek 请求失败，HTTP 状态码：{error.code}。")
        return 1
    except (URLError, TimeoutError):
        print("网络连接失败或请求超时，请检查网络后重试。")
        return 1
    except (ValueError, KeyError, IndexError, TypeError):
        print("DeepSeek 响应格式异常或回答为空。")
        return 1

    print("模型回答：", answer)
    print("结束原因：", result["choices"][0].get("finish_reason"))
    print("Token 用量：", result.get("usage", {}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
