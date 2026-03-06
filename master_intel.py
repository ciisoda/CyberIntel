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
    "User-Agent": "marble-soda-intel-v34.1",
    "Authorization": f"Bearer {GITHUB_TOKEN}" if GITHUB_TOKEN else None
}

def log(msg): print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

# TUYU 资产库 (确保文件名与你文件夹里的一致)
TUYU_ASSETS = {
    "くらべられっ子": {"bg": "mv_kurabe.png", "cover": "cover_kurabe.jpg"},
    "泥の分際で私だけの大切を奪おうだなんて": {"bg": "mv_doro.png", "cover": "cover_doro.jpg"},
    "終点へと向かう楽曲": {"bg": "mv_shuten.png", "cover": "cover_shuten.jpg"},
    "いつかオトナになれるといいね。": {"bg": "mv_otona.png", "cover": "cover_otona.jpg"},
    "過去に囚われている": {"bg": "mv_kako.png", "cover": "cover_kako.jpg"},
    "ロックな君とはお别れだ": {"bg": "mv_rock.png", "cover": "cover_rock.jpg"}
}

def clean_tags(text):
    if not text: return ""
    # 暴力清除所有可能导致 HTML 乱码的符号
    return re.sub(r'[#*`>\-：:]', '', text).replace('评分', '').replace('研判', '').strip()

@lru_cache(maxsize=128)
def get_ai_intel(text, intel_type="cve"):
    prompts = {
        "cve": f"评分|总结|建议。{text}",
        "japan": f"3句总结日本留学IT动态。{text}",
        "word": "选网安日语词，回 单词+假名。",
        "desc": f"解释 '{text}' 并给出一个短例句，用换行符分隔。",
        "lyric": f"格式：歌名 | 日语 | 中文。{list(TUYU_ASSETS.keys())}"
    }
    try:
        res = client.chat.completions.create(model="deepseek-chat", messages=[{"role": "user", "content": prompts[intel_type]}], stream=False)
        return res.choices[0].message.content.strip()
    except: return "5.0 | Timeout | Retry"

def sync_security():
    results = []
    try:
        url = "https://api.github.com/search/repositories?q=CVE-2026+OR+Exploit&sort=updated"
        res = requests.get(url, headers=GITHUB_HEADERS, timeout=15)
        for repo in res.json().get('items', [])[:4]:
            raw = get_ai_intel(repo['description'] or "No desc", "cve")
            parts = (raw.split('|') + ["5.0", "分析中", "请检查"])[:3]
            score_match = re.search(r"\d+(\.\d+)?", parts[0])
            score = float(score_match.group()) if score_match else 5.0
            heat = round(score + math.log(repo.get('stargazers_count', 0) + 1) * 0.6, 2)
            results.append({"name": repo['full_name'], "url": repo['html_url'], "score": score, "summary": clean_tags(parts[1]), "advice": clean_tags(parts[2]), "heat": heat})
    except: pass
    return sorted(results, key=lambda x: x['heat'], reverse=True)

def run():
    log("🏁 启动 V34.1 物理修复版...")
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
            <div style='display:flex; justify-content
