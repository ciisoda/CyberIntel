import os, requests, urllib.parse, re, math
from openai import OpenAI
from datetime import datetime, date
from bs4 import BeautifulSoup
from functools import lru_cache

# ===== 1. 环境初始化 =====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
API_KEY = os.getenv("DEEPSEEK_API_KEY")
BARK_KEY = os.getenv("BARK_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")

GITHUB_HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "marble-soda-intel-v32",
    "Authorization": f"Bearer {GITHUB_TOKEN}" if GITHUB_TOKEN else None
}

def log(msg): print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

# TUYU 真货资产库 (强锁定)
TUYU_ASSETS = {
    "くらべられっ子": {"bg": "mv_kurabe.png", "cover": "cover_kurabe.jpg"},
    "泥の分際で私だけの大切を奪おうだなんて": {"bg": "mv_doro.png", "cover": "cover_doro.jpg"},
    "終点へと向かう楽曲": {"bg": "mv_shuten.png", "cover": "cover_shuten.jpg"},
    "いつかオトナになれるといいね。": {"bg": "mv_otona.png", "cover": "cover_otona.jpg"},
    "過去に囚われている": {"bg": "mv_kako.png", "cover": "cover_kako.jpg"},
    "ロックな君とはお别れだ": {"bg": "mv_rock.png", "cover": "cover_rock.jpg"}
}

# ===== 2. 文本清洗与解析引擎 =====

def clean_tags(text):
    # 彻底清除干扰 UI 的符号
    tags = ['#', '*', '`', '>', '-', '评分', '研判', '总结', '建议', '：', ':']
    for t in tags: text = text.replace(t, '')
    return text.strip()

@lru_cache(maxsize=128)
def get_ai_intel(text, intel_type="cve"):
    prompts = {
        "cve": f"分析漏洞返回格式：评分 | 总结(80字内) | 建议。{text}",
        "japan": f"总结日本IT/留学动态(3句内)。{text}",
        "word": "选网安或音游日语词，回 单词+假名。",
        "desc": f"详细解释 '{text}' 并给出一个短例句，用换行符分隔。",
        "lyric": f"严格选一段歌词。格式：歌名 | 日语 | 中文。禁止多余字：{list(TUYU_ASSETS.keys())}"
    }
    try:
        res = client.chat.completions.create(model="deepseek-chat", messages=[{"role": "user", "content": prompts[intel_type]}], stream=False)
        return res.choices[0].message.content.strip()
    except Exception as e:
        log(f"⚠️ AI 异常: {e}")
        return "5.0 | 解析超时 | 建议检查"

def sync_security():
    log("📡 研判 GitHub 武器库...")
    results = []
    try:
        url = "https://api.github.com/search/repositories?q=CVE-2026+OR+Exploit&sort=updated"
        res = requests.get(url, headers=GITHUB_HEADERS, timeout=15)
        if res.status_code != 200: return []
        
        for repo in res.json().get('items', [])[:4]:
            raw = get_ai_intel(repo['description'] or "No desc", "cve")
            # 弹性解析：防止 split 炸裂
            parts = (raw.split('|') + ["5.0", "无研判总结", "无风险建议"])[:3]
            
            score_match = re.search(r"\d+(\.\d+)?", parts[0])
            score = float(score_match.group()) if score_match else 5.0
            stars = repo.get('stargazers_count', 0)
            heat = round(score + math.log(stars + 1) * 0.6, 2)
            
            results.append({
                "name": repo['full_name'], "url": repo['html_url'], 
                "score": score, "summary": clean_tags(parts[1]), "advice": clean_tags(parts[2]), "heat": heat
            })
    except: pass
    return sorted(results, key=lambda x: x['heat'], reverse=True)

# ===== 3. UI 渲染与存档 =====

def run():
    log("🏁 启动 V32.0 终极视觉版...")
    word_raw = get_ai_intel("Word", "word")
    word = clean_tags(word_raw)
    desc = get_ai_intel(word, "desc")
    lyric_raw = get_ai_intel("Lyric", "lyric")
    
    lyric_parts = (lyric_raw.split('|') + ["TUYU", "...", "..."])[:3]
    song_name = clean_tags(lyric_parts[0])
    
    # 🚩 资产资源路径硬锁定
    mv_bg, album_cover = "mv_default.png", "cover_default.jpg"
    for key, assets in TUYU_ASSETS.items():
        if key in song_name:
            mv_bg, album_cover = assets["bg"], assets["cover"]
            break

    security_data = sync_security()
    japan_intel = get_ai_intel("日本IT及签证情报", "japan")
    
    sec_html = "".join([f"""
        <div class='item-card-p'>
            <div style='display:flex; justify-content:space-between; align-items:center;'>
                <a href='{s['url']}' target='_blank' class='cve-title'>{s['name']}</a>
                <span class='score-tag' style='background:{"#ff4d4d" if s['score']>8.5 else "#00d4ff"}'>
                    {s['score']} | 🔥 {s['heat']}
                </span>
            </div>
            <p class='summary-text'><b>研判：</b>{s['summary']}</p>
            <p class='advice-text'>💡 {s['advice']}</p>
        </div>""" for s in security_data])

    html = f"""
    <html><head><meta charset='utf-8'><meta http-equiv="refresh" content="600">
    <style>
        body {{ 
            margin: 0; padding: 25px; background-color: #05050a; color: #e1e1e6; font-family: 'Segoe UI', system-ui, sans-serif;
            /* 🚩 强制渲染：背景图路径硬编码 */
            background-image: linear-gradient(rgba(5,5,10,0.7), rgba(5,5,10,0.7)), url('{mv_bg}');
            background-size: cover; background-position: center; background-attachment: fixed; background-repeat: no-repeat;
        }}
        .score-tag {{ padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: bold; color: white; }}
        .lyric-box {{ background: rgba(25, 25, 40, 0.75); backdrop-filter: blur(15px); border: 1px solid rgba(255, 0, 127, 0.4); 
                     padding: 22px; border-radius: 15px; margin-bottom: 25px; display: flex; align-items: center; gap: 25px; }}
        .album-art {{ width: 110px; height: 110px; border-radius: 10px; object-fit: cover; flex-shrink: 0; border: 1px solid #444; }}
        .grid {{ display: grid; grid-template-columns: 1fr 1.6fr; gap: 25px; }}
        .section-box {{ background: rgba(10, 10, 20, 0.8); backdrop-filter: blur(12px); padding: 25px; border-radius: 15px; border: 1px solid rgba(255,255,255,0.08); height: fit-content; }}
        
        /* 🚩 核心修复：左侧排版解压 */
        .jp-word {{ font-size: 26px; color: #00d4ff; font-weight: bold; margin-bottom: 12px; }}
        .desc-text {{ font-size: 14px; line-height: 1.8; color: #d1d1d6; white-space: pre-wrap; background: rgba(255,255,255,0.04); padding: 15px; border-radius: 8px; }}
        
        .cve-title {{ font-size: 15px; color: #ff007f; font-weight: bold; text-decoration: none; }}
        .item-card-p {{ margin-bottom: 18px; padding-bottom: 12px; border-bottom: 1px solid rgba(255,255,255,0.05); }}
        .summary-text {{ font-size: 13px; color: #f0f0f5; margin: 8px 0; line-height: 1.5; }}
        .advice-text {{ font-size: 12px; color: #00d4ff; font-style: italic; }}
        
        h3 {{ color: #ff007f; font-size: 11px; text-transform: uppercase; letter-spacing: 2.5px; margin-bottom: 15px; }}
        .japan-card {{ margin-top: 15px; padding: 15px; background: rgba(255, 0, 127, 0.1); border-left: 3px solid #ff007f; border-radius: 4px; font-size: 13px; line-height: 1.6; }}
    </style></head><body>
        <div class="lyric-box">
            <img src="{album_cover}" class="album-art">
            <div style="flex:1;">
                <span style="color:#ff007f; font-size:11px; letter-spacing:2px; font-weight:bold;">♫ TUYU_SYSTEM // V32.0</span>
                <p style="font-size:24px; font-style:italic; margin:10px 0;">{clean_tags(lyric_parts[1])}</p>
                <p style="color:#ff007f; font-size:14px; margin:0;">{clean_tags(lyric_parts[2])}</p>
            </div>
        </div>
        <div class="grid">
            <div class="section-box">
                <h3>Vocal & Japan_Study</h3>
                <div class="jp-word">{word}</div>
                <div class="desc-text">{clean_tags(desc)}</div>
                <div class="japan-card">🎌 <b>Japan_Study_Log:</b><br>{clean_tags(japan_intel)}</div>
            </div>
            <div class="section-box">
                <h3>🔥 High Heat Vulnerability</h3>
                {sec_html}
            </div>
        </div>
    </body></html>
    """
    with open(os.path.join(BASE_DIR, "index.html"), "w", encoding="utf-8") as f: f.write(html)
    
    # 历史存档
    history_dir = os.path.join(BASE_DIR, "history")
    if not os.path.exists(history_dir): os.makedirs(history_dir)
    with open(os.path.join(history_dir, f"{date.today()}.html"), "w", encoding="utf-8") as f: f.write(html)
    log(f"💾 存档已生成: {date.today()}")

    # 推送逻辑
    if BARK_KEY and security_data:
        try:
            top = security_data[0]
            title, body = urllib.parse.quote(f"🚨 高风险: {top['score']}"), urllib.parse.quote(f"{top['name']}\n词: {word[:8]}")
            requests.get(f"https://api.day.app/{BARK_KEY}/{title}/{body}?group=TuyuIntel", timeout=12)
        except: pass

if __name__ == "__main__": run()
