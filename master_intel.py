import os
import requests
from openai import OpenAI
from datetime import datetime
from bs4 import BeautifulSoup

# ===== 1. 核心配置区 (从环境变量读取) =====
API_KEY = os.getenv("DEEPSEEK_API_KEY")
BARK_KEY = os.getenv("BARK_KEY")

client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

# ===== 2. AI 处理逻辑 (适配 DeepSeek) =====
def get_ai_content(text, prompt_type="summary"):
    prompts = {
        "summary": f"翻译并总结这段网安内容，中文回答，保持专业：{text}",
        "word": "选一个网安或技术相关的酷的日语单词，只回单词（含假名），不要任何标点。",
        "desc": f"解释日语词 '{text}' 并给出一个关于网安技术或生活的例句，中文回答。"
    }
    try:
        res = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompts[prompt_type]}],
            stream=False
        )
        return res.choices[0].message.content.strip().replace("*", "")
    except Exception as e:
        log(f"AI 调用异常: {e}")
        return "AI 分析暂时离线"

# ===== 3. 核心抓取模块 =====

def sync_github():
    log("📡 正在监控 GitHub CVE-2026 & Exploit...")
    feeds = []
    try:
        # 搜索最新的 CVE 或 Exploit 项目
        api_url = "https://api.github.com/search/repositories?q=CVE-2026+OR+Exploit+OR+vulnerability&sort=updated"
        headers = {"Accept": "application/vnd.github.v3+json"}
        res = requests.get(api_url, headers=headers, timeout=15).json()
        
        for repo in res.get('items', [])[:4]:
            feeds.append({
                "name": repo['full_name'],
                "url": repo['html_url'],
                "desc": get_ai_content(repo['description'] or "No description", "summary")
            })
    except Exception as e:
        log(f"GitHub 抓取异常: {e}")
    return feeds

def crawl_solidot():
    log("📰 正在采集 Solidot 安全新闻...")
    news = []
    try:
        res = requests.get("https://www.solidot.org/", timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        for art in soup.find_all('div', class_='block_m'):
            h2 = art.find('h2')
            if h2 and h2.find('a'):
                a_tag = h2.find('a')
                title = a_tag.text
                if any(k in title for k in ["安全", "漏洞", "攻击", "黑客", "CVE", "加密"]):
                    p_main = art.find('div', class_='p_mainnew')
                    summary = get_ai_content(p_main.get_text()[:300] if p_main else title, "summary")
                    news.append({
                        "title": title,
                        "url": "https://www.solidot.org" + a_tag['href'],
                        "summary": summary
                    })
            if len(news) >= 5: break
    except Exception as e:
        log(f"新闻抓取异常: {e}")
    return news

# ===== 4. 主运行流程 =====

def run():
    # 1. AI 日语模块
    word = get_ai_content(None, "word")
    desc = get_ai_content(word, "desc")
    
    # 2. 数据采集
    github_data = sync_github()
    news_data = crawl_solidot()
    
    # 3. 构造 HTML (沿用你最喜欢的 V12.1 样式)
    g_html = "".join([f"<div style='margin-bottom:12px;border-left:3px solid #50fa7b;padding-left:10px;'><a href='{g['url']}' target='_blank' style='color:#50fa7b;text-decoration:none;'><b>{g['name']}</b></a><br><i style='font-size:12px;color:#8b949e;'>{g['desc']}</i></div>" for g in github_data])
    n_html = "".join([f"<div style='margin-bottom:15px;'><a href='{n['url']}' target='_blank' style='color:#58a6ff;text-decoration:none;'><b>· {n['title']}</b></a><p style='font-size:13px;color:#8b949e;margin-top:5px;'>{n['summary']}</p></div>" for n in news_data])
    
    html = f"""
    <html><head><meta charset='utf-8'>
    <meta http-equiv="refresh" content="600">
    <style>
        body{{background:#0d1117;color:#c9d1d9;font-family:-apple-system,sans-serif;padding:30px;line-height:1.6;}}
        .grid{{display:grid;grid-template-columns:1fr 1.2fr;gap:25px;}}
        .card{{background:#161b22;padding:25px;border-radius:12px;border:1px solid #30363d;box-shadow: 0 4px 6px rgba(0,0,0,0.3);}}
        h3{{border-bottom:1px solid #333;padding-bottom:10px;margin-top:0;}}
    </style></head><body>
        <h1 style='color:#f0f6fc;'>🛡️ 情报指挥中心 V12.1 (云端增强版)</h1>
        <div class='grid'>
            <div class='card'>
                <h3 style='color:#ff79c6;'>🇯🇵 日语补完计划</h3>
                <div style='font-size:48px;font-weight:bold;color:#ff79c6;margin:15px 0;'>{word}</div>
                <p style='font-size:16px;'>{desc}</p>
                <br>
                <h3 style='color:#50fa7b;'>💾 GitHub 武器库</h3>
                {g_html if g_html else "等待新情报入库..."}
            </div>
            <div class='card'>
                <h3 style='color:#58a6ff;'>🚨 重点安全快讯</h3>
                {n_html if n_html else "暂无相关安全新闻"}
            </div>
        </div>
    </body></html>
    """
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    
    # 4. 推送手机通知
    requests.get(f"https://api.day.app/{BARK_KEY}/指挥中心更新成功/今日日语: {word}\n已扫描最新 CVE 情报")
    log("✅ 任务全量完成。")

if __name__ == "__main__":
    run()
