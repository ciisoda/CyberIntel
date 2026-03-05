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
    
    # 构造卡片内容
    g_html = "".join([f"<div style='margin-bottom:15px;padding:12px;background:rgba(255,121,198,0.1);border-radius:8px;border:1px solid #ff79c6;'><a href='{g['url']}' target='_blank' style='color:#ff79c6;text-decoration:none;font-weight:bold;'>{g['name']}</a><br><small style='color:#bd93f9;'>{g['desc']}</small></div>" for g in github_data])
    n_html = "".join([f"<div style='margin-bottom:18px;'><a href='{n['url']}' target='_blank' style='color:#8be9fd;text-decoration:none;font-weight:bold;'>• {n['title']}</a><p style='font-size:13px;color:#f8f8f2;margin-top:6px;opacity:0.8;'>{n['summary']}</p></div>" for n in news_data])
    
    # 🚩 重要：CSS 全部大括号使用 {{}} 逃逸，确保不会触发 Python SyntaxError
    html = f"""
    <html><head><meta charset='utf-8'><meta http-equiv="refresh" content="600">
    <style>
        body{{{{ background: #0b0e14; color: #f8f8f2; font-family: 'Inter', sans-serif; margin: 0; padding: 0; }}}}
        .banner{{{{ width: 100%; height: 250px; background: url('https://img.api.aa1.cn/2026/03/05/tuyu-aesthetic.jpg') center/cover; position: relative; border-bottom: 4px solid #ff79c6; }}}}
        .banner-overlay{{{{ position: absolute; bottom: 0; left: 0; right: 0; background: linear-gradient(transparent, #0b0e14); height: 100px; }}}}
        .content{{{{ padding: 25px; display: grid; grid-template-columns: 1fr 1.5fr; gap: 20px; }}}}
        .panel{{{{ background: rgba(25, 29, 45, 0.7); backdrop-filter: blur(10px); border: 1px solid #2d3143; padding: 20px; border-radius: 15px; }}}}
        .word-box{{{{ background: linear-gradient(135deg, #ff79c6 0%, #bd93f9 100%); padding: 25px; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 0 20px rgba(255,121,198,0.3); }}}}
        .jp-word{{{{ font-size: 48px; font-weight: bold; color: #fff; text-shadow: 0 0 15px rgba(255,255,255,0.5); }}}}
        h3{{{{ color: #ff79c6; font-size: 14px; text-transform: uppercase; letter-spacing: 2px; border-left: 3px solid #ff79c6; padding-left: 10px; margin-bottom: 15px; }}}}
        @media (max-width: 800px) {{{{ .content {{{{ grid-template-columns: 1fr; }}}} }}}}
    </style></head><body>
        <div class="banner"><div class="banner-overlay"></div></div>
        <div style="padding-left: 25px; margin-top: -30px; position: relative; z-index: 1;">
            <h1 style="color: #ff79c6; font-style: italic; text-shadow: 0 0 10px #ff79c6;">TUYU_INTEL_SYSTEM // V14.0</h1>
        </div>
        <div class="content">
            <div class="panel">
                <h3>Vocabulary Update</h3>
                <div class="word-box">
                    <div class="jp-word">{word}</div>
                    <p style="margin-top:15px; font-size:16px; line-height:1.4;">{desc}</p>
                </div>
                <h3>GitHub CVE Armory</h3>
                {g_html if g_html else "Awaiting mission data..."}
            </div>
            <div class="panel">
                <h3>Global Threat Feed</h3>
                {n_html if n_html else "No threats detected."}
            </div>
        </div>
        <footer style="text-align: center; padding: 20px; color: #44475a; font-size: 11px;">
             Marble_soda // 2026-03-05 // osu!mania PP: 11,000+
        </footer>
    </body></html>
    """
    with open("index.html", "w", encoding="utf-8") as f: f.write(html)
    requests.get(f"https://api.day.app/{BARK_KEY}/指挥中心刷新完成/词汇: {word}")

if __name__ == "__main__":
    run()
