import os
import requests
from openai import OpenAI

# 核心：从系统环境中读取钥匙
API_KEY = os.getenv("DEEPSEEK_API_KEY")
BARK_KEY = os.getenv("BARK_KEY")

if not API_KEY or not BARK_KEY:
    print("❌ 错误：环境变量读取失败，请检查 GitHub Secrets 和 YAML 配置")
    exit(1)

client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")
BARK_URL = f"https://api.day.app/{BARK_KEY}/"

def fetch_data():
    return "通报：发现一个新的高危漏洞，请及时关注 GitHub 自动化分析结果。"

def analyze(text):
    try:
        res = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": f"分析漏洞危害：{text}"}]
        )
        return res.choices[0].message.content
    except Exception as e:
        return f"AI 分析失败: {e}"

def push(content):
    requests.get(f"{BARK_URL}云端情报提醒/{content}")

if __name__ == "__main__":
    report = analyze(fetch_data())
    print(report)
    push(report)
