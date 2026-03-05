import os
import requests
from openai import OpenAI
from datetime import datetime
from bs4 import BeautifulSoup

# ===== 1. 核心配置区 =====
API_KEY = os.getenv("DEEPSEEK_API_KEY")
BARK_KEY = os.getenv("BARK_KEY")

client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

# ===== 2. AI 处理逻辑 (适配音游人/网安生偏好) =====
def get_ai_content(text, prompt_type="summary"):
    prompts = {
        "summary": f"翻译并总结这段网安内容，中文回答，严禁使用星号：{text}",
        "word": "选一个网安或音游(如osu!mania)相关的酷的日语单词，只回单词（含假名），不带标点。",
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
    log("📡 正在监控 GitHub CVE-2026...")
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
    log("📰 正在采集 Solidot 安全新闻...")
    news = []
    try:
        res = requests.get("https://www.solidot.org/", timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        for art in soup.find_all('div', class_='block_m'):
            h2 = art.find('h2')
            if h2:
                # 🚩 修复之前的语法错误点 (第 60 行)
                a_tag = h2.find('a') 
                if a_tag:
                    title = a_tag.text
                    if any(k in title for k in ["安全", "漏洞", "攻击", "黑客", "软件"]):
                        p_main = art.find('div', class_='p_mainnew')
                        summary = get_ai_content(p_main.get_text()[:300] if p_main else title, "summary")
                        news.append({
                            "title": title, 
                            "url": "https://www.solidot.org" + a_tag['href'], 
                            "summary": summary
                        })
            if len(news) >= 5: break
    except: pass
    return news

# ===== 4. 构造 HTML 并输出 =====
def run():
    word = get_ai_content(None, "word")
    desc = get_ai_content(word, "desc")
    github_data = sync_github()
    news_data = crawl_solidot()
    
    # 采用多段拼接，防止长字符串导致复制错误
    g_html = ""
    for g in github_data:
        g_html += f"<div style='margin-bottom:12px;border-left:3px solid #50fa7b;padding-left:10px;'>"
        g_html += f"<a href='{g['url']}' target='_blank' style='color:#50fa7b;text-decoration:none;'><b>{g['name']}</b></a><br>"
        g_html += f"<i style='font-size:12px;color:#8b949e;'>{g['desc']}</i></div>"
        
    n_html = ""
    for n in news_data:
        n_html += f"<div style='margin-bottom:15px;'>"
        n_html += f"<a href='{n['url']}' target='_blank' style='color:#58a6ff;text-decoration:none;'><b>· {n['title']}</b></a>"
        n_html += f"<p style='font-size:13px;color:#8b949e;margin-top:5px;'>{n['summary']}</p></div>"
    
    html = f"""
    <html><head><meta charset='utf-8'><meta http-equiv="refresh" content="600">
    <style>
        body{{background:#0d1117;color:#c9d1d9;font-family:sans-serif;padding:30px;line-height:1.6;}}
        .grid{{display:grid;grid-template-columns:1fr 1.2fr;gap:25px;}}
        .card{{background:#1
