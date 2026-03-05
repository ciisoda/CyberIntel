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

def get_ai_content(text, prompt_type="summary"):
    prompts = {
        "summary": f"翻译并总结这段网安内容，中文回答，严禁使用星号：{text}",
        "word": "选一个网安或音游相关的日语单词，回单词+假名，不要标点。",
        "desc": f"解释日语词 '{text}' 并给出一个关于音游或网安的例句，中文回答。"
    }
    try:
        res = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompts[prompt_type]}],
            stream=False
        )
        return res.choices[0].message.content.strip().replace("*", "")
    except: return "AI 分析暂时离线"

def sync_github():
    feeds = []
    try:
        res = requests.get("https://api.github.com/search/repositories?q=CVE-2026+OR+Exploit&sort=updated", timeout=15).json()
        for repo in res.get('items', [])[:4]:
            feeds.append({"name": repo['full_name'], "url": repo['html_url'], "desc": get_ai_content(repo['description'] or "No desc", "summary")})
    except: pass
    return feeds

def crawl_solidot():
    news = []
    try:
        soup = BeautifulSoup(requests.get("https://www.solidot.org/", timeout=15).text, 'html.parser')
        for art in soup.find_all('div', class_='block_m'):
            h2 = art.find('h2')
            if h2 and h2.find('a'):
                a_tag = h2.find('a')
                if any(k in a_tag.text for k in ["安全", "漏洞", "黑客", "加密"]):
                    summary = get_ai_content(art.find('div', class_='p_mainnew').get_text()[:300] if art.find('div', class_='p_mainnew') else a_tag.text, "summary")
                    news.append({"title": a_tag.text, "url": "https://www.solidot.org" + a_tag['href'], "summary": summary})
            if len(news) >= 5: break
    except: pass
    return news

def run():
    word = get_ai_content(None, "word")
    desc = get_ai_content(word, "desc")
    github_data = sync_github()
    news_data = crawl_solidot()
    
    # 构建内容块
    g_html = "".join([f"<div style='margin-bottom:15px;padding:12px;background:#1a1d2e;border-radius:8px;border-left:4px solid #ff79c6;'><a href='{g['url']}' target='_blank' style='color:#ff79c6;text-decoration:none;font-weight:bold;'>{g['name']}</a><br><small style='color:#8b949e;'>{g['desc']}</small></div>" for g in github_data])
    n_html = "".join([f"<div style='margin-bottom:18px;'><a href='{n['url']}' target='_blank' style='color:#8be9fd;text-decoration:none;font-weight:bold;'>• {n['title']}</a><p style='font-size:13px;color:#bd93f9;margin-top:6px;line-height:1.4;'>{n['summary']}</p></div>" for n in news_data])
    
    # 🚩 最终 HTML 模板 (已严格逃逸 CSS 大括号)
    html = f"""
    <html><head><meta charset='utf-8'><meta http-equiv="refresh" content="600">
    <style>
        body{{{{ background: #0b0e14; color: #e1e1e6; font-family: 'Segoe UI', sans-serif; padding: 25px; line-height: 1.5; }}}}
        .main-title{{{{ color: #ff79c6; border-bottom: 2px solid #ff79c6; display: inline-block; padding-bottom: 5px; margin-bottom: 25px; font-style: italic; }}}}
        .container{{{{ display: grid; grid-template-columns: 1fr 1.4fr; gap: 20px; }}}}
        .panel{{{{ background: #111420; border: 1px solid #2d3143; padding: 20px; border-radius: 12px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }}}}
        .jp-card{{{{ background: linear-gradient(135deg, #282a36 0%, #44475a 100%); padding: 20px; border-radius: 10px; margin-bottom: 20px; position: relative; overflow: hidden; }}}}
        .jp-word{{{{ font-size: 42px; font-weight: 900; color: #50fa7b; text-shadow: 2px 2px 10px rgba(80,250,123,0.3); }}}}
        h3{{{{ color: #bd93f9; text-transform: uppercase; letter-spacing: 1px; font-size: 14px; margin-bottom: 15px; }}}}
        @media (max-width: 800px) {{{{ .container {{{{ grid-template-columns: 1fr; }}}} }}}}
    </style></head><body>
        <h1 class="main-title">INTEL_TERMINAL // V13.0</h1>
        <div class="container">
            <div class="panel">
                <h3>Vocabulary Update</h3>
                <div class="jp-card">
                    <div class="jp-word">{word}</div>
                    <p style="color:#f8f8f2; margin-top:10px; font-size:15px;">{desc}</p>
                </div>
                <h3>GitHub Armory</h3>
                {g_html if g_html else "Scanning for exploits..."}
            </div>
            <div class="panel">
                <h3>Security Feed</h3>
                {n_html if n_html else "All systems clear."}
            </div>
        </div>
        <div style="margin-top:20px; font-size:10px; color:#44475a; text-align:center;">
            Logged at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} // System: Marble_soda
        </div>
    </body></html>
    """
    with open("index.html", "w", encoding="utf-8") as f: f.write(html)
    requests.get(f"https://api.day.app/{BARK_KEY}/指挥中心刷新完成/词汇: {word}")

if __name__ == "__main__":
    run()
