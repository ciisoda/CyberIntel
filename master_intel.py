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

# ===== 2. 精选曲库 (保持 PNG+JPG 双图逻辑) =====
TUYU_SONGS = [
    "《くらべられっ子》",
    "《泥の分際で私だけの大切を奪おうだなんて》",
    "《終点へと向かう楽曲》",
    "《いつかオトナになれるといいね。》",
    "《過去に囚われている》",
    "《ロックな君とはお別れだ》"
]

ASSET_MAPPING = {
    "くらべられっ子": {"bg": "mv_kurabe.png", "cover": "cover_kurabe.jpg"},
    "泥の分際で": {"bg": "mv_doro.png", "cover": "cover_doro.jpg"},
    "终点へと": {"bg": "mv_shuten.png", "cover": "cover_shuten.jpg"},
    "オトナになれると": {"bg": "mv_otona.png", "cover": "cover_otona.jpg"},
    "过去に囚われている": {"bg": "mv_kako.png", "cover": "cover_kako.jpg"},
    "ロックな君": {"bg": "mv_rock.png", "cover": "cover_rock.jpg"}
}

def get_ai_content(text, prompt_type="summary"):
    song_list_str = ", ".join(TUYU_SONGS)
    prompts = {
        "summary": f"总结网安内容，中文回答：{text}",
        "word": "选网安或音游相关的日语单词，回单词+假名。",
        "desc": f"解释日语词 '{text}' 并给出音游或网安例句，中文回答。",
        "lyric": f"请从 [{song_list_str}] 中选一段歌词。格式必须严格为：歌名 | 日语歌词 | 中文翻译。不要多余废话。"
    }
    try:
        res = client.chat.completions.create(model="deepseek-chat", messages=[{"role": "user", "content": prompts[prompt_type]}], stream=False)
        return res.choices[0].message.content.strip().replace("*", "")
    except: return "未知曲目 | 歌词加载失败 | AI 离线"

# ... (sync_github 和 crawl_solidot 逻辑维持不变) ...
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

def run():
    word = get_ai_content(None, "word")
    desc = get_ai_content(word, "desc")
    lyric_raw = get_ai_content(None, "lyric")
    
    parts = lyric_raw.split('|')
    song_name = parts[0].strip() if len(parts) > 0 else "TUYU"
    lyric_jp = parts[1].strip() if len(parts) > 1 else "歌词解析错误"
    lyric_cn = parts[2].strip() if len(parts) > 2 else ""

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
            background-color: #05050a; color: #f0f0f5; 
            font-family: 'Segoe UI', Tahoma, sans-serif; 
            margin: 0; padding: 25px;
            /* 🚩 调整遮罩不透明度，让 PNG 截图更清晰 */
            background-image: linear-gradient(rgba(5, 5, 10, 0.75), rgba(5, 5, 10, 0.75)), url('{mv_bg}');
            background-size: cover; background-position: center; background-attachment: fixed;
        }}
        .header {{ border-left: 4px solid #ff007f; padding-left: 15px; margin-bottom: 25px; }}
        .header h1 {{ color: #ff007f; margin: 0; font-size: 24px; text-shadow: 0 0 10px rgba(255, 0, 127, 0.5); }}

        /* 🚩 优化后的歌词框：解决文本挤压问题 */
        .lyric-box {{ 
            background: rgba(25, 25, 40, 0.6); backdrop-filter: blur(15px);
            border: 1px solid rgba(255, 0, 127, 0.3); 
            padding: 20px; border-radius: 15px; margin-bottom: 30px;
            display: flex; align-items: center; gap: 25px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }}
        .album-art {{ 
            width: 120px; height: 120px; border-radius: 12px; 
            box-shadow: 0 0 20px rgba(0,0,0,0.6); border: 1px solid #444;
            flex-shrink: 0; object-fit: cover;
        }}
        .lyric-content {{ flex: 1; min-width: 0; }}
        .song-title {{ color: #ff007f; font-size: 12px; letter-spacing: 2px; font-weight: bold; margin-bottom: 10px; display: block; }}
        .lyric-jp {{ color: #ffffff; font-size: 20px; display: block; margin-bottom: 8px; line-height: 1.4; }}
        .lyric-cn {{ color: #bd93f9; font-size: 14px; font-style: italic; }}

        .grid {{ display: grid; grid-template-columns: 1fr 1.6fr; gap: 25px; }}
        
        /* 🚩 重点：调低不透明度（0.6），增加磨砂感 */
        .section-box {{ 
            background: rgba(15, 15, 25, 0.6); 
            backdrop-filter: blur(10px); 
            padding: 30px; border-radius: 15px; 
            border: 1px solid rgba(255, 255, 255, 0.1); 
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }}
        
        .word-title {{ font-size: 38px; color: #00d4ff; font-weight: bold; margin: 15px 0; text-shadow: 0 0 12px rgba(0, 212, 255, 0.4); }}
        .word-desc {{ color: #d1d1d6; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 20px; font-size: 15px; line-height: 1.7; }}
        h3 {{ color: #ff007f; font-size: 13px; text-transform: uppercase; margin-bottom: 20px; letter-spacing: 1.5px; }}
        
        a {{ text-decoration: none; font-weight: bold; transition: color 0.2s; }}
        .item-card-p a {{ color: #ff007f; }}
        .item-card-b a {{ color: #00d4ff; }}
        .item-card-p, .item-card-b {{ margin-bottom: 20px; padding-bottom: 15px; border-bottom: 1px solid rgba(255,255,255,0.05); }}
        .item-card-p p, .item-card-b p {{ font-size: 13px; color: #a0a0a5; margin: 8px 0 0 0; line-height: 1.5; }}
        
        @media (max-width: 900px) {{ 
            .grid {{ grid-template-columns: 1fr; }}
            .lyric-box {{ flex-direction: column; text-align: center; }}
        }}
    </style></head><body>
        <div class="header">
            <h1>TUYU_TERMINAL // V18.5</h1>
            <small style="color: #888;">Marble_soda // 惠州学院網安 // OSU!MANIA 11,000PP</small>
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
            </div>
            <div class="section-box">
                <h3>GitHub Security & Feed</h3>
                <div style="margin-bottom: 30px;">{g_list if g_list else "Scanning repositories..."}</div>
                <div>{n_list if n_list else "Monitoring threats..."}</div>
            </div>
        </div>
    </body></html>
    """
    with open("index.html", "w", encoding="utf-8") as f: f.write(html)
    log(f"✅ V18.5 透明版部署成功: {song_name}")

if __name__ == "__main__":
    run()
