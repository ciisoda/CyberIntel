import os, requests, urllib.parse, re, math
from openai import OpenAI
from datetime import datetime, date
from functools import lru_cache

# ===== 1. 环境初始化 =====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
API_KEY = os.getenv("DEEPSEEK_API_KEY")
BARK_KEY = os.getenv("BARK_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")

GITHUB_HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "marble-soda-intel-v34",
    "Authorization": f"Bearer {GITHUB_TOKEN}" if GITHUB_TOKEN else None
}

def log(msg): print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

TUYU_ASSETS = {
    "くらべられっ子": {"bg": "mv_kurabe.png", "cover": "cover_kurabe.jpg"},
    "泥の分際で私だけの大切を奪おうだなんて": {"bg": "mv_doro.png", "cover": "cover_doro.jpg"},
    "終点へと向かう楽曲": {"bg": "mv_shuten.png", "cover": "cover_shuten.jpg"},
    "いつかオトナになれるといいね。": {"bg": "mv_otona.png", "cover": "cover_otona.jpg"},
    "過去に囚われている": {"bg": "mv_kako.png", "cover": "cover_kako.jpg"},
    "ロックな君とはお别れだ": {"bg": "mv_rock.png", "cover": "cover_rock.jpg"}
}

# ===== 2. 增强型清洗引擎 =====
def clean_tags(text):
    if not text: return ""
    tags = ['#', '*', '`', '>', '-', '评分', '研判', '总结', '建议', '歌名', '日语', '中文', '：', ':']
    for t in tags: text = text.replace(t, '')
    return text.strip()

@lru_cache(maxsize=128)
def get_ai_intel(text, intel_type="cve"):
    prompts = {
        "cve": f"评分 | 总结 | 建议。{text}",
        "japan": f"以3个短句总结日本IT/留学动态。{text}",
        "word": "选网安或音游日语词，回 单词+假名。",
        "desc": f"解释 '{text}' 并给出一个短例句，必须换行。",
        "lyric": f"严格格式：歌名 | 日语歌词 | 中文。禁止多余字：{list(TUYU_ASSETS.keys())}"
    }
    try:
        res = client.chat.completions.create(model="deepseek-chat", messages=[{"role": "user", "content": prompts[intel_type]}], stream=False)
        return res.choices[0].message.content.strip()
    except: return "5.0 | 超时 | 检查网络"

def sync_security():
    results = []
    try:
        url = "https://api.github.com/search/repositories?q=CVE-2026+OR+Exploit&sort=updated"
        res = requests.get(url, headers=GITHUB_HEADERS, timeout=15)
        for repo in res.json().get('items', [])[:4]:
            raw = get_ai_intel(repo['description'] or "No desc", "cve")
            parts = (raw.split('|') + ["5.0", "待分析", "待研判"])[:3]
            score_match = re.search(r"\d+(\.\d+)?", parts[0])
            score = float(score_match.group()) if score_match else 5.0
            heat = round(score + math.log(repo.get('stargazers_count', 0) + 1) * 0.6, 2)
            results.append({"name": repo['full_name'], "url": repo['html_url'], "score": score, "summary": clean_tags(parts[1]), "advice": clean_tags(parts[2]), "heat": heat})
    except: pass
    return sorted(results, key=lambda x: x['heat'], reverse=True)

# ===== 3. UI 布局重组 =====
def run():
    log("🏁 启动 V34.0 架构重组版...")
    word_raw = get_ai_intel("Word", "word")
    word = clean_tags(word_raw)
    desc = get_ai_intel(word, "desc")
    lyric_raw = get_ai_intel("Lyric", "lyric")
    lyric_parts = (lyric_raw.split('|') + ["TUYU", "...", "..."])[:3]
    
    mv_bg, album_cover = "mv_default.png", "cover_default.jpg"
    for key, assets in TUYU_ASSETS.items():
        if key in clean_tags(lyric_parts[0]):
            mv_bg, album_cover = assets["bg"], assets["cover"]
            break

    sec_data = sync_security()
    japan_intel = get_ai_intel("日本IT", "japan")
    
    sec_html = "".join([f"""
        <div class='item-card-p'>
            <div style='display:flex; justify-content:space-between; align-items:center;'>
                <a href='{s['url']}' target='_blank' class='cve-title'>{s['name']}</a>
                <span class='score-tag' style='background:{"#ff4d4d" if s['score']>8.5 else "#00d4ff"}'>{s['score']} | 🔥 {s['heat']}</span>
            </div>
            <p class='summary-text'><b>研判：</b>{s['summary']}</p>
            <p class='advice-text'>💡 {s['advice']}</p>
        </div>""" for s in sec_data])

    html = f"""
    <html><head><meta charset='utf-8'><meta http-equiv="refresh" content="600">
    <style>
        body {{ 
            margin: 0; padding: 30px; background-color: #05050a; color: #e1e1e6; font-family: 'Segoe UI', sans-serif;
            background-image: linear-gradient(rgba(5,5,10,0.6), rgba(5,5,10,0.6)), url('{mv_bg}');
            background-size: cover; background-position: center; background-attachment: fixed;
        }}
        /* 顶部 TUYU 版块重构 */
        .lyric-box {{ 
            background: rgba(20, 20, 35, 0.85); backdrop-filter: blur(12px); border: 1px solid #ff007f; 
            padding: 25px; border-radius: 20px; margin-bottom: 30px; display: flex; align-items: center; gap: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        }}
        .album-art {{ width: 120px; height: 120px; border-radius: 12px; border: 2px solid #ff007f; flex-shrink: 0; }}
        .lyric-content {{ flex: 1; }}
        .system-tag {{ font-size: 10px; color: #ff007f; letter-spacing: 3px; font-weight: bold; text-transform: uppercase; }}
        
        .grid {{ display: grid; grid-template-columns: 1fr 1.6fr; gap: 30px; }}
        .section-box {{ 
            background: rgba(10, 10, 20, 0.85); padding: 25px; border-radius: 20px; 
            border: 1px solid rgba(255,255,255,0.1); height: fit-content;
        }}
        
        /* 版块标题样式 */
        h3 {{ color: #ff007f; font-size: 11px; letter-spacing: 2px; margin: 0 0 20px 0; border-bottom: 1px solid rgba(255,0,127,0.3); padding-bottom: 8px; }}
        
        .jp-word {{ font-size: 28px; color: #00d4ff; font-weight: bold; margin-bottom: 15px; }}
        .desc-text {{ font-size: 14px; line-height: 1.8; white-space: pre-wrap; background: rgba(255,255,255,0.05); padding: 18px; border-radius: 12px; }}
        
        /* 新闻版块独立样式 */
        .news-card {{ margin-top: 25px; padding: 20px; background: rgba(255, 0, 127, 0.1); border-left: 4px solid #ff007f; border-radius: 8px; font-size: 13px; line-height: 1.7; }}
        
        .cve-title {{ font-size: 15px; color: #ff007f; font-weight: bold; text-decoration: none; }}
        .item-card-p {{ margin-bottom: 20px; padding-bottom: 15px; border-bottom: 1px solid rgba(255,255,255,0.05); }}
        .summary-text {{ font-size: 13px; margin: 10px 0; opacity: 0.9; }}
        .advice-text {{ font-size: 12px; color: #00d4ff; opacity: 0.8; }}
        .score-tag {{ padding: 3px 8px; border-radius: 5px; font-size: 11px; color: white; font-weight: bold; }}
    </style></head><body>
        <div class="lyric-box">
            <img src="{album_cover}" class="album-art">
            <div class="lyric-content">
                <div class="system-tag">♫ TUYU_INTELLIGENCE_
