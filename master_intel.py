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

# ===== 2. 官方精选曲库 (已二次精简) =====
# 🚩 仅保留你最认可的曲目
TUYU_SONGS = [
    "《くらべられっ子》",
    "《泥の分際で私だけの大切を奪おうだなんて》",
    "《終点へと向かう楽曲》",
    "《いつかオトナになれるといいね。》",
    "《過去に囚われている》",
    "《ロックな君とはお別れだ》"
]

# 🚩 图片映射字典 (需确保 NAS 中有对应文件)
IMAGE_MAPPING = {
    "くらべられっ子": "cover_kurabe.jpg",
    "泥の分際で": "cover_doro.jpg",
    "终点へと": "cover_shuten.jpg",
    "オトナになれると": "cover_otona.jpg",
    "过去に囚われている": "cover_kako.jpg",
    "ロックな君": "cover_rock.jpg"
}

# ===== 3. AI 处理逻辑 (强约束版) =====
def get_ai_content(text, prompt_type="summary"):
    song_list_str = ", ".join(TUYU_SONGS)
    prompts = {
        "summary": f"翻译并总结这段网安内容，中文回答，严禁使用星号：{text}",
        "word": "选一个网安或音游相关的日语单词，回单词+假名，不要标点。",
        "desc": f"解释日语词 '{text}' 并给出一个关于音游或网安的例句，中文回答。",
        "lyric": f"请严格从 TUYU(ツユ) 的曲库中随机选一段经典歌词：[{song_list_str}]。格式：歌名 | 日语歌词 | 中文翻译。严禁星号。"
    }
    try:
        res = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompts[prompt_type]}],
            stream=False
        )
        return res.choices[0].message.content.strip().replace("*", "")
    except: return "未知曲目 | 无法获取歌词 | AI 离线中"

# ... (sync_github 和 crawl_solidot 函数与 V18.0 一致) ...

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

# ===== 4. 主流程 =====
def run():
    word = get_ai_content(None, "word")
    desc = get_ai_content(word, "desc")
    lyric_raw = get_ai_content(None, "lyric")
    
    parts = lyric_raw.split('|')
    song_name = parts[0].strip() if len(parts) > 0 else "TUYU"
    lyric_jp = parts[1].strip() if len(parts) > 1 else "歌词加载失败"
    lyric_cn = parts[2].strip() if len(parts) > 2 else ""

    cover_filename = "cover_default.jpg"
    for key in IMAGE_MAPPING.keys():
        if key in song_name:
            cover_filename = IMAGE_MAPPING[key]
            break

    github_data = sync_github()
    news_data = crawl_solidot()
    
    g_list = "".join([f"<div class='item-card-p'><a href='{g['url']}'>{g['name']}</a><p>{g['desc']}</p></div>" for g in github_data])
    n_list = "".join([f"<div class='item-card-b'><a href='{n['url']}'>{n['title']}</a><p>{n['summary']}</p></div>" for n in news_data])
    
    html = f"""
    <html><head><meta charset='utf-8'><meta http-equiv="refresh" content="600">
    <style>
        body {{ 
            background-color: #0d0d16; color: #e0e0e0; 
            font-family: 'Helvetica Neue', Arial, sans-serif; 
            margin: 0; padding: 20px;
            background-image: linear-gradient(rgba(13, 13, 22, 0.9), rgba(13, 13, 22, 0.9)), url('{cover_filename}');
            background-size: cover; background-attachment: fixed;
        }}
        .header {{ border-left: 5px solid #ff007f; padding-left: 15px; margin-bottom: 20px; }}
        .header h1 {{ color: #ff007f; margin: 0; font-size: 24px; letter-spacing: 2px; }}
        .lyric-box {{ background: rgba(20, 20, 35, 0.85); border: 1px solid rgba(255, 0, 127, 0.5); padding: 20px; border-radius: 8px; margin-bottom: 25px; text-align: center; box-shadow: 0 0 20px rgba(255, 0, 127, 0.2); }}
        .song-title {{ color: #ff007f; font-size: 11px; font-weight: bold; text-transform: uppercase; letter-spacing: 2.5px; margin-bottom: 12px; display: block; opacity: 0.8; }}
        .lyric-jp {{ color: #f8f8f2; font-style: italic; font-size: 20px; text-shadow: 0 0 10px rgba(255, 0, 127, 0.3); display: block; margin-bottom: 8px; }}
        .lyric-cn {{ color: #ff007f; font-size: 14px; opacity: 0.9; }}
        .grid {{ display: grid; grid-template-columns: 1fr 1.5fr; gap: 20px; }}
        .section-box {{ background: rgba(20, 20, 35, 0.9); padding: 20px; border-radius: 4px; border: 1px solid #333; }}
        .word-title {{ font-size: 40px; color: #00d4ff; font-weight: bold; margin: 10px 0; }}
        .word-desc {{ color: #bbb; line-height: 1.6; border-top: 1px solid #444; padding-top: 10px; }}
        h3 {{ color: #ff007f; font-size: 12px; text-transform: uppercase; margin-bottom: 15px; }}
        a {{ text-decoration: none; font-weight: bold; transition: 0.3s; }}
        .item-card-p a {{ color: #ff007f; }}
        .item-card-b a {{ color: #00d4ff; }}
        .item-card-p, .item-card-b {{ margin-bottom: 15px; padding-bottom: 10px; border-bottom: 1px solid #222; }}
        .item-card-p p, .item-card-b p {{ font-size: 13px; color: #888; margin: 5px 0 0 0; }}
        @media (max-width: 900px) {{ .grid {{ grid-template-columns: 1fr; }} }}
    </style></head><body>
        <div class="header">
            <h1>TUYU_INTEL_TERMINAL // V18.2</h1>
            <small style="color: #666;">Marble_soda // OSU!MANIA 11k pp // TUYU 精选模式</small>
        </div>
        <div class="lyric-box">
            <span class="song-title">♫ Now Playing: {song_name}</span>
            <span class="lyric-jp">{lyric_jp}</span>
            <span class="lyric-cn">{lyric_cn}</span>
        </div>
        <div class="grid">
            <div class="section-box">
                <h3>Daily Japanese补完</h3>
                <div class="word-title">{word}</div>
                <div class="word-desc">{desc}</div>
                <br>
                <h3>GitHub CVE Armory</h3>
                {g_list if g_list else "入库中..."}
            </div>
            <div class="section-box">
                <h3>Global Threat Feed</h3>
                {n_list if n_list else "暂无威胁"}
            </div>
        </div>
    </body></html>
    """
    with open("index.html", "w", encoding="utf-8") as f: f.write(html)
    log(f"✅ 同步成功：{song_name}")

if __name__ == "__main__":
    run()
