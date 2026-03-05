import os
import requests
from openai import OpenAI

# 从 GitHub Secrets 读取钥匙
API_KEY = os.getenv("DEEPSEEK_API_KEY")
BARK_KEY = os.getenv("BARK_KEY")

client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")
BARK_URL = f"https://api.day.app/{BARK_KEY}/"

def fetch_intel():
    # 这里模拟抓取一段网安新闻，你可以后续接入真实的爬虫
    return "发现针对 macOS 的新型持久化后门漏洞，利用了特定的系统服务权限提升。"

def analyze_with_japanese(text):
    try:
        # 让 DeepSeek 强行加入日语术语标注
        prompt = f"请分析以下网安情报，并为其中的技术词汇标注日语翻译（如：漏洞 -> 脆弱性）：\n{text}"
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI 分析失败: {e}"

def generate_html(report):
    # 生成 HTML，名字必须叫 index.html 才能覆盖你 NAS 上的文件
    html_template = f"""
    <!DOCTYPE html>
    <html lang="zh">
    <head>
        <meta charset="UTF-8">
        <title>云端网安情报站</title>
        <style>
            body {{ background: #0d1117; color: #c9d1d9; font-family: sans-serif; padding: 20px; }}
            .card {{ border: 1px solid #30363d; padding: 15px; border-radius: 6px; background: #161b22; }}
            h1 {{ color: #58a6ff; border-bottom: 1px solid #30363d; padding-bottom: 10px; }}
            pre {{ white-space: pre-wrap; word-wrap: break-word; line-height: 1.6; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>🛡️ 每日安全情报 (日语学习版)</h1>
            <pre>{report}</pre>
            <hr>
            <p style="font-size: 0.8em; color: #8b949e;">更新时间: 2026年3月</p>
        </div>
    </body>
    </html>
    """
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_template)

def push_notification(msg):
    # 截取前 50 个字发推送到手机
    requests.get(f"{BARK_URL}云端情报更新/{msg[:50]}...")

if __name__ == "__main__":
    raw_data = fetch_intel()
    analysis = analyze_with_japanese(raw_data)
    generate_html(analysis)
    push_notification(analysis)
    print("✅ 文件 index.html 已生成，准备投送！")
