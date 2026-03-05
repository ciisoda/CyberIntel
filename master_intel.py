import os
import requests
from openai import OpenAI
from datetime import datetime
from bs4 import BeautifulSoup

# ===== 1. 配置区 =====
API_KEY = os.getenv("DEEPSEEK_API_KEY")
BARK_KEY = os.getenv("BARK_KEY")

client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

# ===== 2. AI 处理逻辑 =====
def get_ai_content(text, prompt_type="summary"):
    prompts = {
        "summary": f"翻译并总结这段网安内容，中文回答，严禁使用星号：{text}",
        "word": "选一个网安或音游相关的酷的日语单词，只回单词（含假名），不要任何标点。",
        "desc": f"解释日语词 '{text}' 并给出一个关于音游或网安技术的例句，严禁使用星号，中文回答。"
    }
    try:
        res = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompts[prompt_type]}],
            stream=False
        )
        return res.choices[0].message.content.strip().replace("*", "")
    except Exception as e:
        log(f"AI 异常: {e}")
        return "AI 分析暂时离线"

# ===== 3. 核心抓取模块 =====
def sync_github():
    log("📡 监控 GitHub CVE-2026...")
    feeds = []
    try:
        api_url = "https://api.github.com/search/repositories?q=CVE-2026+OR+Exploit+OR+vulnerability&sort=updated"
        headers = {"Accept": "application/vnd.github.v3+json"}
        res = requests.get(api_url, headers=headers, timeout=15).json()
        for repo in res.get('items', [])[:4]:
            feeds.append({
                "name": repo['full_name'],
                "url": repo['html_url'],
                "desc": get_ai_content(repo['description'] or "No description", "summary")
            })
    except: pass
    return feeds

def crawl_solidot():
    log("📰 采集 Solidot 安全新闻...")
    news = []
    try:
        res = requests.get("https://www.solidot.org/", timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        for art in soup.find_all('div', class_='block_m'):
            h2 = art.find('h2')
            if h2 and h2.find('a'):
                a_tag = h2.find('
