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
    "User-Agent": "marble-soda-intel-v33",
    "Authorization": f"Bearer {GITHUB_TOKEN}" if GITHUB_TOKEN else None
}

def log(msg): print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

TUYU_ASSETS = {
    "くらべられっ子": {"bg": "mv_kurabe.png", "cover": "cover_kurabe.jpg"},
    "泥の分際で私だけの大切を夺おうだなんて": {"bg": "mv_doro.png", "cover": "cover_doro.jpg"},
    "终点へと向かう楽曲": {"bg": "mv_shuten.png", "cover": "cover_shuten.jpg"},
    "いつかオトナになれるといいね。": {"bg": "mv_otona.png", "cover": "cover_otona.jpg"},
    "过去に囚われている": {"bg": "mv_kako.png", "cover": "cover_kako.jpg"},
    "ロックな君とはお别れだ": {"bg": "mv_rock.png", "cover": "cover_rock.jpg"}
}

# ===== 2. 清洗引擎 =====
def clean_tags(text):
    if not text: return ""
    tags = ['#', '*', '`', '>', '-', '评分', '研判', '总结', '建议', '：', ':']
    for t in tags: text = text.replace(t, '')
    return text.strip()

@lru_cache(maxsize=128)
def get_ai_intel(text, intel_type="cve"):
    prompts = {
        "cve": f"评分|总结|建议。{text}",
        "japan": f"3句总结日本IT。{text}",
        "word": "选网安日语词，回 单词+假名。",
        "desc": f"详细解释 '{text}' 并给出一个短例句，必须换行。",
        "lyric": f"歌名 | 日语 | 中文。禁止多余字：{list(TUYU_ASSETS.keys())}"
    }
    try:
        res = client.chat.completions.create(model="deepseek-chat", messages=[{"role": "user", "content": prompts[intel_type]}], stream=False)
        return res.choices[0].message.content.strip()
    except: return "5.0 | 超时 | 检查"

def sync_security():
    results = []
    try:
        url = "https://api.github.com/search/repositories?q=CVE-2026+OR+Exploit&sort=updated"
        res = requests.get(url, headers=GITHUB_HEADERS, timeout=15)
        for repo in res.json().get('items', [])[:4]:
            raw = get_ai_intel(repo['description'] or "No desc", "cve")
            parts = (raw.split('|') + ["5.0", "无总结", "无建议"])[:3]
            score_match = re.search(r"\d+(\.\d+)?", parts[0])
            score = float(score_match.group()) if score_match else 5.0
            heat = round(score + math.log(repo.get('stargazers_count', 0) + 1) * 0.6, 2)
            results.append({"name": repo['full_name'], "url": repo['html_url'], "score": score, "summary": clean_tags(parts[1]), "advice": clean_tags(parts[2]), "heat": heat})
    except: pass
    return sorted(results, key=lambda x: x['heat'], reverse=True)

# ===== 3. UI 渲染 =====
def run():
    word = clean_tags(get_ai_intel("Word", "word"))
    desc = get_ai_intel(word, "desc")
    lyric_raw = get_ai_intel("Lyric", "lyric")
    lyric_parts = (lyric_raw.split('|') + ["TUYU", "...", "..."])[:3]
    
    mv_bg, album_cover = "mv_default.png", "cover_default.jpg"
    for key, assets in TUYU_ASSETS.items():
        if key in lyric_parts[0]:
            mv_bg, album_cover = assets["bg"], assets["cover"]
            break

    sec_data = sync_security()
    japan_intel = get_ai_intel("日本IT", "japan")
    
    sec_html = "".join([f"""
        <div class='item-card-p'>
            <div style='display:flex; justify-content:space-between;'>
                <a href='{s['url']}' target='_blank' class='cve-title'>{s['name']}</a>
                <span class='score-tag' style='background:{"#ff4d4d" if s['score']>8.5 else "#00d4ff"}'>{s['score']}</span>
            </div>
            <p class='summary-text'><b>研判：</b>{s['summary']}</p>
            <p class='advice-text'>💡 {s['advice']}</p>
        </div>""" for s in sec_data])

    html = f"""
    <html><head><meta charset='utf-8'><meta http-equiv="refresh" content="600">
    <style>
        body {{ 
            margin: 0; padding: 25px; background-color: #05050a; color: #e1e1e6; font-family: sans-serif;
            /* 🚩 核心修改：取消遮罩，增加亮度 */
            background-image: url('{mv_bg}');
            background-size: cover; background-position: center; background-attachment: fixed;
            filter: brightness(1.05);
        }}
        .lyric-box {{ background: rgba(15, 15, 25, 0.85); backdrop-filter: blur(10px); border: 1px solid #ff007f; 
                     padding: 20px; border-radius: 15px; margin-bottom: 25px; display: flex; align-items: center; gap: 20px; }}
        .grid {{ display: grid; grid-template-columns: 1fr 1.6fr; gap: 20px; }}
        .section-box {{ background: rgba(10, 10, 20, 0.9); padding: 20px; border-radius: 15px; border: 1px solid rgba(255,255,255,0.1); }}
        .jp-word {{ font-size: 26px; color: #00d4ff; font-weight: bold; margin-bottom: 10px; }}
        .desc-text {{ font-size: 14px; line-height: 1.6; white-space: pre-wrap; background: rgba(255,255,255,0.05); padding: 12px; border-radius: 8px; }}
        .cve-title {{ font-size: 14px; color: #ff007f; font-weight: bold; text-decoration: none; }}
        .summary-text {{ font-size: 13px; margin: 5px 0; }}
        .advice-text {{ font-size: 12px; color: #00d4ff; }}
        .score-tag {{ padding: 2px 6px; border-radius: 4px; font-size: 10px; color: white; }}
    </style></head><body>
        <div class="lyric-box">
            <img src="{album_cover}" style="width:100px; height:100px; border-radius:8px;">
            <div>
                <p style="font-size:22px; margin:0 0 5px 0;">{clean_tags(lyric_parts[1])}</p>
                <p style="color:#ff007f; font-size:14px; margin:0;">{clean_tags(lyric_parts[2])}</p>
            </div>
        </div>
        <div class="grid">
            <div class="section-box">
                <div class="jp-word">{word}</div>
                <div class="desc-text">{clean_tags(desc)}</div>
                <div style="margin-top:15px; font-size:13px; border-left:3px solid #ff007f; padding-left:10px;">{clean_tags(japan_intel)}</div>
            </div>
            <div class="section-box">{sec_html}</div>
        </div>
    </body></html>
    """
    with open(os.path.join(BASE_DIR, "index.html"), "w", encoding="utf-8") as f: f.write(html)
    log("💾 V33.0 辉度增强版已更新")

if __name__ == "__main__": run()
