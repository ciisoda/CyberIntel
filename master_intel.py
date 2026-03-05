import os
import requests
from openai import OpenAI
from datetime import datetime
from bs4 import BeautifulSoup

# ===== 1. 核心配置 =====
API_KEY = os.getenv("DEEPSEEK_API_KEY")
BARK_KEY = os.getenv("BARK_KEY")
client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

# ===== 2. 精选曲库 =====
TUYU_SONGS = [
    "《くらべられっ子》",
    "《泥の分際で私だけの大切を奪おうだなんて》",
    "《終点へと向かう楽曲》",
    "《いつかオトナになれるといいね。》",
    "《過去に囚われている》",
    "《ロックな君とはお別れだ》"
]

# 🚩 映射表：这里同时处理背景(png)和封面(jpg)
ASSET_MAPPING = {
    "くらべられっ子": {"bg": "mv_kurabe.png", "cover": "cover_kurabe.jpg"},
    "泥の分際で": {"bg": "mv_doro.png", "cover": "cover_doro.jpg"},
    "终点へと": {"bg": "mv_shuten.png", "cover": "cover_shuten.jpg"},
    "オトナになれると": {"bg": "mv_otona.png", "cover": "cover_otona.jpg"},
    "过去に囚われている": {"bg": "mv_kako.png", "cover": "cover_kako.jpg"},
    "ロックな君": {"bg": "mv_rock.png", "cover": "cover_rock.jpg"}
}

# ===== 3. AI 获取函数 (略，同 V18.3) =====
def get_ai_content(text, prompt_type="summary"):
    song_list_str = ", ".join(TUYU_SONGS)
    prompts = {
        "summary": f"总结这段网安内容，中文回答：{text}",
        "word": "选一个网安或音游相关的日语单词，回单词+假名。",
        "desc": f"解释日语词 '{text}' 并给出音游或网安例句，中文回答。",
        "lyric": f"请从 [{song_list_str}] 中选歌词。格式：歌名 | 日语歌词 | 中文翻译。"
    }
    try:
        res = client.chat.completions.create(model="deepseek-chat", messages=[{"role": "user", "content": prompts[prompt_type]}], stream=False)
        return res.choices[0].message.content.strip().replace("*", "")
    except: return "未知曲目 | 无法获取歌词 | AI 离线"

# ... (sync_github 和 crawl_solidot 保持不变) ...

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
                    p_main = art.find('div', class_='p_mainnew')
                    summary = get_ai_content(p_main.get_text()[:300] if p_main else a_tag.text, "summary")
                    news.append({"title": a_tag.text, "url": "https://www.solidot.org" + a_tag['href'], "summary": summary})
            if len(news) >= 5: break
    except: pass
    return news

# ===== 4. 主运行流程 =====
def run():
    word = get_ai_content(None, "word")
    desc = get_ai_content(word, "desc")
    lyric_raw = get_ai_content(None, "lyric")
    
    parts = lyric_raw.split('|')
    song_name = parts[0].strip() if len(parts) > 0 else "TUYU"
    lyric_jp = parts[1].strip() if len(parts) > 1 else "歌词加载失败"
    lyric_cn = parts[2].strip() if len(parts) > 2 else ""

    # 🚩 动态资源匹配逻辑
    mv_bg = "mv_default.png"
    album_cover = "cover_default.jpg"
    
    for key, assets in ASSET_MAPPING.items():
        if key in song_name:
            mv_bg = assets["bg"]
            album_cover = assets["cover"]
            break

    github_data = sync_github()
    news_data = crawl_solidot()
    
    g_list = "".join([f"<div class='item-card-p'><a href='{g['url']}'>{g['name']}</a><p>{g['desc']}</p></div>" for g in github_data])
    n_list = "".join([f"<div class='item-card-b'><a href='{n['url']}'>{n['title']}</a><p>{n['summary']}</p></div>" for n in news_data])
    
    html = f"""
    <html><head><meta charset='utf-8'><meta http-equiv="refresh" content="600">
    <style>
        body {{ 
            background-color: #05050a; color: #e1e1e6; 
            font-family: 'Segoe UI', sans-serif; 
            margin: 0; padding: 20px;
            background-image: linear-gradient(rgba(5, 5, 10, 0.82), rgba(5, 5, 10, 0.82)), url('{mv_bg}');
            background-size: cover; background-position: center; background-attachment: fixed;
        }}
        .header {{ border-left: 4px solid #ff007f; padding-left: 15px; margin-bottom: 25px; }}
        .header h1 {{ color: #ff007f; margin: 0; font-size: 24px; letter-spacing: 2px; }}

        /* 🚩 仿播放器设计的歌词框 */
        .lyric-box {{ 
            background: rgba(20, 20, 35, 0.75); backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 0, 127, 0.4); 
            padding: 20px; border-radius: 12px; margin-bottom: 25px;
            display: flex; align-items: center; gap: 20px;
        }}
        .album-art {{ 
            width: 100px; height: 100px; border-radius: 8px; 
            box-shadow: 0 0 15px rgba(0,0,0,0.5); border: 1px solid #444;
        }}
        .lyric-content {{ flex: 1; text-align: left; }}
        .song-title {{ color: #ff007f; font-size: 11px; letter-spacing: 2px; margin-bottom: 8px; display: block; }}
        .lyric-jp {{ color: #fff; font-size: 19px; display: block; margin-bottom: 5px; font-style: italic; }}
        .lyric-cn {{ color: #ff007f; font-size: 13px; opacity: 0.9; }}

        .grid {{ display: grid; grid-template-columns: 1fr 1.6fr; gap: 20px; }}
        .section-box {{ background: rgba(10, 10, 20, 0.85); backdrop-filter: blur(8px); padding: 25px; border-radius: 10px; border: 1px solid #2d2d3d; }}
        .word-title {{ font-size: 40px; color: #00d4ff; font-weight: bold; margin: 10px 0; }}
        .word-desc {{ color: #a0a0b0; border-top: 1px solid #333; padding-top: 15px; font-size: 14px; line-height: 1.6; }}
        h3 {{ color: #ff007f; font-size: 12px; text-transform: uppercase; margin-bottom: 15px; }}
        
        a {{ text-decoration: none; font-weight: bold; }}
        .item-card-p a {{ color: #ff007f; }}
        .item-card-b a {{ color: #00d4ff; }}
        .item-card-p, .item-card-b {{ margin-bottom: 15px; padding-bottom: 12px; border-bottom: 1px solid #222; }}
        .item-card-p p, .item-card-b p {{ font-size: 13px; color: #888; margin: 5px 0 0 0; }}
        
        @media (max-width: 900px) {{ 
            .grid {{ grid-template-columns: 1fr; }}
            .lyric-box {{ flex-direction: column; text-align: center; }}
            .lyric-content {{ text-align: center; }}
        }}
    </style></head><body>
        <div class="header">
            <h1>TUYU_TERMINAL // V18.4</h1>
            <small style="color: #666;">Marble_soda // 恵州学院網安 // OSU!MANIA 11,000PP</small>
        </div>

        <div class="lyric-box">
            <img src="{album_cover}" class="album-art">
            <div class="lyric-content">
                <span class="song-title">♫ NOW PLAYING: {song_name}</span>
                <span class="lyric-jp">{lyric_jp}</span>
                <span class="lyric-cn">{lyric_cn}</span>
            </div>
        </div>

        <div class="grid">
            <div class="section-box">
                <h3>Japanese Learning</h3>
                <div class="word-title">{word}</div>
                <div class="word-desc">{desc}</div>
                <br>
                <h3>GitHub Security Armory</h3>
                {g_list if g_list else "Scanning..."}
            </div>
            <div class="section-box">
                <h3>Global Threat Feed</h3>
                {n_list if n_list else "Monitoring..."}
            </div>
        </div>
    </body></html>
    """
    with open("index.html", "w", encoding="utf-8") as f: f.write(html)
    log(f"✅ 双图联动同步成功: {song_name}")

if __name__ == "__main__":
    run()
