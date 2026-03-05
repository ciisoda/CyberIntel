import os
import requests
from openai import OpenAI

# ======= 配置区 =======
API_KEY = "sk-7c5f0784703742bd923d64015035eedd"
BARK_KEY = "Eda3xELXUYRR8eeQ4gWam8" # 只需要链接最后那串字符
BARK_URL = f"https://api.day.app/{BARK_KEY}/"
# =====================

client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")

def fetch_cve_data():
    print("[1/3] 📡 正在抓取情报...")
    # 这里模拟你 V12.1 的抓取结果
    return "通报：某知名 NAS 系统发现 RCE 漏洞，攻击者可绕过身份验证执行代码。"

def analyze_threat(cve_text):
    print("[2/3] 🤖 AI 正在深度分析...")
    try:
        res = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": f"分析该漏洞等级并50字总结危害：{cve_text}"}]
        )
        return res.choices[0].message.content
    except Exception as e:
        return f"分析失败: {e}"

def push_alert(content):
    print("[3/3] 📲 正在推送至 iPhone...")
    requests.get(f"{BARK_URL}情报预警/{content}")

if __name__ == "__main__":
    data = fetch_cve_data()
    report = analyze_threat(data)
    print(f"\nAI 报告：{report}\n")
    push_alert(report)
    print("✨ 全部完成！")
