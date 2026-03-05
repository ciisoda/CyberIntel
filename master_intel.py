import os
import requests
from openai import OpenAI

# ======= 核心修改：从 GitHub 保险箱读取钥匙 =======
API_KEY = os.getenv("sk-7c5f0784703742bd923d64015035eedd")
BARK_KEY = os.getenv("Eda3xELXUYRR8eeQ4gWam8")
BARK_URL = f"https://api.day.app/{BARK_KEY}/"
# ===============================================

client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")

def fetch_cve_data():
    print("[1/3] 📡 正在抓取情报...")
    return "通报：发现一个新的高危漏洞，请及时关注 GitHub 自动化分析结果。"

def analyze_threat(cve_text):
    print("[2/3] 🤖 AI 正在深度分析...")
    try:
        res = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": f"分析该漏洞等级并50字总结危害：{cve_text}"}]
        )
        return res.choices[0].message.content
    except Exception as e:
        return f"分析失败，请检查 Key 是否有效。错误: {e}"

def push_alert(content):
    print("[3/3] 📲 正在推送至 iPhone...")
    # 简单的推送逻辑
    requests.get(f"{BARK_URL}云端情报提醒/{content}")

if __name__ == "__main__":
    data = fetch_cve_data()
    report = analyze_threat(data)
    print(f"\nAI 报告：{report}\n")
    push_alert(report)
    print("✨ 云端任务执行完毕！")
