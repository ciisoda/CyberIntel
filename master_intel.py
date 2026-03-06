import os
import requests
import urllib.parse
from openai import OpenAI
from datetime import datetime, date # 🚩 新增这一行，用于日期快照存档
from bs4 import BeautifulSoup

# ===== 1. 核心配置区 =====
API_KEY = os.getenv("DEEPSEEK_API_KEY")
BARK_KEY = os.getenv("BARK_KEY")
client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

# ===== 2. 精选曲库与资源映射 (保留真货逻辑) =====
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

# ===== 3. AI 获取逻辑 (集成内容长度限制，确保文本不乱) =====
def get_ai_content(text, prompt_type="summary"):
    song_list_str = ", ".join(TUYU_SONGS)
    prompts = {
        # 🚩 内容限制：翻译并总结网安内容，中文回答，控制在 100 字以内，不要多余废话。
        "summary": f"翻译并总结这段网安内容，中文回答，限制在 100 字以内，不要废话，严禁星号：{text}",
        "word": "选网安或音游相关的日语单词，回单词+假名。",
        # 🚩 内容限制：解释日语词 '{text}' 并给出一个简短的音游相关例句，总字数控制在 120 字以内。
        "desc": f"解释日语词 '{text}' 并给出一个简短的音游或网安相关例句，中文回答，限制在 120 字以内。",
        "lyric": f"请严格从曲库 [{song_list_str}] 中选一段歌词。格式严格为：歌名 | 日语歌词 | 中文翻译。严禁星号。"
    }
    try:
        res = client.chat.completions.create(model="deepseek-chat", messages=[{"role": "user", "content": prompts[prompt_type]}], stream=False)
        return res.choices[0].message.content.strip().replace("*", "")
    except Exception as e:
        log(f"❌ AI 解析异常: {e}")
        return "未知曲目 | 加载失败 | AI 离线"

# ... (sync_github 和 crawl_solidot 爬虫模块保持正常功能) ...
def sync_github():
    log("📡 扫描 GitHub CVE...")
    feeds = []
    try:
        res = requests.get("https://api.github.com/search/repositories?q=CVE-2026+OR+Exploit&sort=updated", timeout=15).json()
        for repo in res.get('items', [])[:4]:
            # 描述长度在 HTML 模板里截断，AI 总结只负责翻译和简述
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

# ===== 4. UI/UX 文本重塑 (全页面磨砂重写与文本限制) =====
def run():
    log("🏁 启动 V19.0 精致化与存档流程...")
    word = get_ai_content(None, "word")
    desc = get_ai_content(word, "desc")
    lyric_raw = get_ai_content(None, "lyric")
    
    parts = lyric_raw.split('|')
    song_name = parts[0].strip() if len(parts) > 0 else "TUYU"
    lyric_jp = parts[1].strip() if len(parts) > 1 else "歌词加载失败"
    lyric_cn = parts[2].strip() if len(parts) > 2 else ""

    # 双图映射逻辑
    mv_bg = "mv_default.png"
    album_cover = "cover_default.jpg"
    for key, assets in ASSET_MAPPING.items():
        if key in song_name:
            mv_bg = assets["bg"]
            album_cover = assets["cover"]
            break

    github_data = sync_github()
    news_data = crawl_solidot()
    
    # 构建内容块 (关键修复：加入 summary-text 限制)
    g_list = "".join([f"<div class='item-card-p'><a href='{g['url']}' target='_blank'>{g['name']}</a><p class='summary-text'>{g['desc']}</p></div>" for g in github_data])
    n_list = "".join([f"<div class='item-card-b'><a href='{n['url']}' target='_blank'>{n['title']}</a><p class='summary-text'>{n['summary']}</p></div>" for n in news_data])
    
    # 🚩 重塑日语卡片布局，将例句独立
    jap_desc = desc
    jap_interpretation = jap_desc.split('例句：')[0] if '例句：' in jap_desc else jap_desc
    jap_example = jap_desc.split('例句：')[1] if '例句：' in jap_desc else ''
    jap_example_block = f'<p class="jp-example"><em>{jap_example}</em></p>' if jap_example else ''

    html = f"""
    <html><head><meta charset='utf-8'><meta http-equiv="refresh" content="600">
    <style>
        /* 全局审美重塑 */
        body {{ 
            background-color: #0d0d16; color: #f0f0f5; 
            font-family: 'Segoe UI', Tahoma, system-ui, sans-serif; 
            margin: 0; padding: 25px;
            background-image: linear-gradient(rgba(13, 13, 22, 0.7), rgba(13, 13, 22, 0.7)), url('{mv_bg}');
            background-size: cover; background-position: center; background-attachment: fixed;
        }}
        h1 {{ color:#ff007f; font-size:24px; letter-spacing: 2px; text-shadow: 0 0 15px rgba(255, 0, 127, 0.5); }}

        /* 歌词播放器框重塑 (对齐与仪式感) */
        .lyric-box-new {{ 
            background: rgba(25, 25, 40, 0.6); backdrop-filter: blur(15px);
            border: 1px solid rgba(255, 0, 127, 0.4); 
            padding: 20px; border-radius: 18px; margin-bottom: 30px;
            display: flex; align-items: center; gap: 25px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }}
        .album-art-new {{ width: 120px; height: 120px; border-radius: 10px; object-fit: cover; flex-shrink: 0; border: 1px solid #444; }}
        .lyric-content-new {{ flex: 1; min-width: 0; text-align: left; display: flex; flex-direction: column; gap: 8px; }}
        .song-title {{ color: #a0a0b0; font-size: 12px; font-weight: bold; letter-spacing: 2px; margin-bottom: 5px; display: block; }}
        .lyric-jp {{ color: #ffffff; font-size: 20px; font-style: italic; line-height: 1.4; }}
        .lyric-cn {{ color: #ff007f; font-size: 14px; opacity: 0.9; }}

        .grid {{ display: grid; grid-template-columns: 1fr 1.6fr; gap: 25px; }}
        
        /* 琉璃幻象卡片 */
        .section-box {{ 
            background: rgba(15, 15, 25, 0.6); backdrop-filter: blur(10px); 
            padding: 30px; border-radius: 15px; 
            border: 1px solid rgba(255, 255, 255, 0.08); 
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }}
        
        /* 单词卡片文本重塑 */
        .jp-word {{ font-size: 42px; color: #00d4ff; font-weight: bold; margin: 15px 0; text-shadow: 0 0 12px rgba(0, 212, 255, 0.4); }}
        .jp-interpretation {{ color: #d1d1d6; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 15px; font-size: 15px; line-height: 1.7; }}
        .jp-example {{ color: #bbb; font-size: 13px; margin-top: 10px; }}
        
        h3 {{ color: #ff007f; font-size: 13px; text-transform: uppercase; margin-bottom: 20px; letter-spacing: 1.5px; }}
        
        a {{ text-decoration: none; font-weight: bold; transition: color 0.2s; }}
        .item-card-p a {{ color: #ff007f; font-size: 14px; }} .item-card-b a {{ color: #00d4ff; font-size: 14px; }}
        .item-card-p, .item-card-b {{ margin-bottom: 20px; padding-bottom: 12px; border-bottom: 1px solid rgba(255,255,255,0.05); }}
        
        /* 🚩 关键修复：限制摘要长度为3行 */
        .summary-text {{ 
            font-size: 13px; color: #999; margin: 8px 0 0 0; line-height: 1.5;
            display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden;
        }}
        
        @media (max-width: 900px) {{ 
            .grid {{ grid-template-columns: 1fr; }}
            .lyric-box-new {{ flex-direction: column; text-align: center; }}
            .lyric-content-new {{ text-align: center; }}
        }}
    </style></head><body>
        <div class="header">
            <h1>TUYU_TERMINAL // V19.0</h1>
            <small style="color: #666;">Marble_soda // 恵州学院網安生 // OSU!MANIA 11,000PP</small>
        </div>
        <div class="lyric-box-new">
            <img src="{album_cover}" class="album-art-new">
            <div class="lyric-content-new">
                <span class="song-title">♫ NOW PLAYING: {song_name}</span>
                <span class="lyric-jp">{lyric_jp}</span>
                <span class="lyric-cn">{lyric_cn}</span>
            </div>
        </div>
        <div class="grid">
            <div class="section-box">
                <h3>DAILY_日本語補完</h3>
                <div class="jp-word">{word}</div>
                <div class="jp-interpretation">{jap_interpretation}</div>
                {jap_example_block}
            </div>
            <div class="section-box">
                <h3>GLOBAL Threat & Sec Armory</h3>
                <div style="margin-bottom: 30px;">{g_list if g_list else "Scanning for assets..."}</div>
                <div>{n_list if n_list else "Monitoring threats..."}</div>
            </div>
        </div>
        <footer style="text-align:center; margin-top:30px; color:#1a1d2e; font-size:10px;">DESIGNED FOR MARBLE_SODA // TUYU FOREVER // SNAPSHOT: {date.today()}</footer>
    </body></html>
    """
    
    # 🚩 核心逻辑：双重写入逻辑 (本地存档与网页快照)
    with open("index.html", "w", encoding="utf-8") as f: f.write(html)
    log("💾 index.html 写入完成")

    # 存档：创建 history 文件夹，生成带日期快照
    output_dir = "history"
    if not os.path.exists(output_dir): os.makedirs(output_dir)
    history_file = f"{output_dir}/{date.today()}.html"
    with open(history_file, "w", encoding="utf-8") as f: f.write(html)
    log(f"💾 历史快照已存档: {history_file}")

    # ===== 5. 健壮的推送逻辑 (保留 V18.8 编码版) =====
    if BARK_KEY:
        try:
            safe_song = "".join(filter(lambda x: x not in '0123456789.《》', song_name))[:12]
            safe_word = word.split()[0][:12] if word else "DataUpdate"
            title_encoded = urllib.parse.quote("TUYU终端已同步")
            body_encoded = urllib.parse.quote(f"♫ {safe_song}\n新词: {safe_word}")
            requests.get(f"https://api.day.app/{BARK_KEY}/{title_encoded}/{body_encoded}?isArchive=1&group=TuyuIntel", timeout=12)
            log(f"🔔 Bark 推送成功: {song_name}")
        except Exception as e:
            log(f"❌ 推送由于编码失败: {e}")

if __name__ == "__main__":
    run()
