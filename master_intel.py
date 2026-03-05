import os
import requests
import urllib.parse  # 🚩 必须引入，用于解决推送失败问题
from openai import OpenAI
from datetime import datetime
from bs4 import BeautifulSoup

# ===== 1. 核心配置区 =====
API_KEY = os.getenv("DEEPSEEK_API_KEY")
BARK_KEY = os.getenv("BARK_KEY")
client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

# ===== 2. 精选曲库与资源映射 =====
TUYU_SONGS = [
    "《くらべられっ子》", "《泥の分際で私だけの大切を奪おうだなんて》",
    "《終点へと向かう楽曲》", "《いつかオトナになれるといいね。》",
    "《過去に囚われている》", "《ロックな君とはお別れだ》"
]

ASSET_MAPPING = {
    "くらべられっ子": {"bg": "mv_kurabe.png", "cover": "cover_kurabe.jpg"},
    "泥の分際で": {"bg": "mv_doro.png", "cover": "cover_doro.jpg"},
    "终点へと": {"bg": "mv_shuten.png", "cover": "cover_shuten.jpg"},
    "オトナになれると": {"bg": "mv_otona.png", "cover": "cover_otona.jpg"},
    "过去に囚われている": {"bg": "mv_kako.png", "cover": "cover_kako.jpg"},
    "ロックな君": {"bg": "mv_rock.png", "cover": "cover_rock.jpg"}
}

# ===== 3. AI 获取逻辑 (集成 Japanese + Lyric) =====
def get_ai_content(text, prompt_type="summary"):
    song_list_str = ", ".join(TUYU_SONGS)
    prompts = {
        "summary": f"总结网安内容，中文回答：{text}",
        "word": "选网安或音游相关的日语单词，回单词+假名。",
        "desc": f"解释日语词 '{text}' 并给出音游或网安例句，中文回答。",
        "lyric": f"请从 [{song_list_str}] 中选歌词。格式严格为：歌名 | 日语歌词 | 中文翻译。严禁星号。"
    }
    try:
        res = client.chat.completions.create(model="deepseek-chat", messages=[{"role": "user", "content": prompts[prompt_type]}], stream=False)
        return res.choices[0].message.content.strip().replace("*", "")
    except: return "未知曲目 | 歌词加载失败 | AI 离线"

# ===== 4. 爬虫模块 =====
def sync_github():
    log("📡 扫描 GitHub 武器库...")
    feeds = []
    try:
        res = requests.get("https://api.github.com/search/repositories?q=CVE-2026+OR+Exploit&sort=updated", timeout=15).json()
        for repo in res.get('items', [])[:4]:
            feeds.append({"name": repo['full_name'], "url": repo['html_url'], "desc": get_ai_content(repo['description'] or "No desc", "summary")})
    except: pass
    return feeds

def crawl_solidot():
    log("📰 采集 Solidot 快讯...")
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

# ===== 5. 主流程与 HTML 生成 =====
def run():
    word = get_ai_content(None, "word")
    desc = get_ai_content(word, "desc")
    lyric_raw = get_ai_content(None, "lyric")
    
    parts = lyric_raw.split('|')
    song_name = parts[0].strip() if len(parts) > 0 else "TUYU"
    lyric_jp = parts[1].strip() if len(parts) > 1 else "歌词解析错误"
    lyric_cn = parts[2].strip() if len(parts) > 2 else ""

    # 资源匹配逻辑
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
            background-color: #05050a; color: #f0f0f5; font-family: 'Segoe UI', sans-serif; 
            margin: 0; padding: 25px;
            background-image: linear-gradient(rgba(5, 5, 10, 0.75), rgba(5, 5, 10, 0.75)), url('{mv_bg}');
            background-size: cover; background-position: center; background-attachment: fixed;
        }}
        .lyric-box {{ 
            background: rgba(25, 25, 40, 0.6); backdrop-filter: blur(15px); border: 1px solid rgba(255, 0, 127, 0.3); 
            padding: 20px; border-radius: 15px; margin-bottom: 30px; display: flex; align-items: center; gap: 25px;
        }}
        .album-art {{ width: 120px; height: 120px; border-radius: 12px; object-fit: cover; flex-shrink: 0; border: 1px solid #444; }}
        .lyric-content {{ flex: 1; min-width: 0; }}
        .song-title {{ color: #ff007f; font-size: 12px; font-weight: bold; margin-bottom: 8px; display: block; }}
        .lyric-jp {{ color: #ffffff; font-size: 19px; display: block; margin-bottom: 5px; font-style: italic; }}
        .lyric-cn {{ color: #bd93f9; font-size: 13px; }}
        .grid {{ display: grid; grid-template-columns: 1fr 1.6fr; gap: 25px; }}
        .section-box {{ background: rgba(15, 15, 25, 0.6); backdrop-filter: blur(10px); padding: 25px; border-radius: 15px; border: 1px solid rgba(255, 255, 255, 0.1); }}
        .word-title {{ font-size: 36px; color: #00d4ff; font-weight: bold; margin: 10px 0; }}
        .word-desc {{ color: #d1d1d6; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 15px; font-size: 14px; line-height: 1.6; }}
        h3 {{ color: #ff007f; font-size: 12px; text-transform: uppercase; margin-bottom: 15px; }}
        a {{ text-decoration: none; font-weight: bold; }}
        .item-card-p a {{ color: #ff007f; }} .item-card-b a {{ color: #00d4ff; }}
        .item-card-p, .item-card-b {{ margin-bottom: 15px; padding-bottom: 10px; border-bottom: 1px solid rgba(255,255,255,0.05); }}
        .item-card-p p, .item-card-b p {{ font-size: 13px; color: #888; margin: 5px 0 0 0; }}
    </style></head><body>
        <h1 style="color:#ff007f; font-size:22px; margin-bottom:20px;">TUYU_TERMINAL // V18.6</h1>
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
                <h3>Vocabulary</h3>
                <div class="word-title">{word}</div>
                <div class="word-desc">{desc}</div>
            </div>
            <div class="section-box">
                <h3>Intelligence</h3>
                <div>{g_list if g_list else "Scanning..."}</div>
                <div>{n_list if n_list else "Monitoring..."}</div>
            </div>
        </div>
    </body></html>
    """
    with open("index.html", "w", encoding="utf-8") as f: f.write(html)

    # 🚩 核心修复：Bark 安全编码推送
    try:
        title_encoded = urllib.parse.quote("情报中心同步成功")
        body_encoded = urllib.parse.quote(f"♫ {song_name}\n今日日语: {word}")
        requests.get(f"https://api.day.app/{BARK_KEY}/{title_encoded}/{body_encoded}", timeout=10)
        log(f"🔔 Bark 推送成功: {song_name}")
    except Exception as e:
        log(f"❌ 推送由于编码或网络失败: {e}")

if __name__ == "__main__":
    run()
