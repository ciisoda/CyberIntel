import os, requests, urllib.parse, re, math
from openai import OpenAI
from datetime import datetime, date

# ===== 1. 初始化 =====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
API_KEY = os.getenv("DEEPSEEK_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")

TUYU_ASSETS = {
    "くらべられっ子": {"bg": "mv_kurabe.png", "cover": "cover_kurabe.jpg"},
    "泥の分際で私だけの大切を奪おうだなんて": {"bg": "mv_doro.png", "cover": "cover_doro.jpg"},
    "終点へと向かう楽曲": {"bg": "mv_shuten.png", "cover": "cover_shuten.jpg"},
    "いつかオトナになれるといいね。": {"bg": "mv_otona.png", "cover": "cover_otona.jpg"},
    "過去に囚われている": {"bg": "mv_kako.png", "cover": "cover_kako.jpg"},
    "ロックな君とはお别れだ": {"bg": "mv_rock.png", "cover": "cover_rock.jpg"}
}

def clean(t): return re.sub(r'[#*`>\-：:]', '', t).strip() if t else ""

def get_ai(prompt_type, context=""):
    prompts = {
        "word": "选个网安或TUYU歌词里的日语单词+假名。",
        "desc": f"详细解释{context}并给个例句，换行分隔。",
        "japan": "三句总结日本IT/留学/签证最新动态。",
        "lyric": f"格式：歌名 | 日语 | 中文。选一首：{list(TUYU_ASSETS.keys())}",
        "cve": f"评分|简述|建议。内容：{context}"
    }
    try:
        res = client.chat.completions.create(model="deepseek-chat", messages=[{"role":"user","content":prompts[prompt_type]}])
        return res.choices[0].message.content.strip()
    except: return "Error | 数据获取失败"

# ===== 2. 逻辑执行 =====
word = clean(get_ai("word"))
desc = get_ai("desc", word)
japan = get_ai("japan")
lyric_raw = get_ai("lyric")
l_parts = (lyric_raw.split('|') + ["TUYU", "...", "..."])[:3]

mv_bg, cover = "mv_default.png", "cover_default.jpg"
for k, v in TUYU_ASSETS.items():
    if k in clean(l_parts[0]): mv_bg, cover = v["bg"], v["cover"]

# CVE 抓取
cve_html = ""
try:
    r = requests.get("https://api.github.com/search/repositories?q=CVE-2026&sort=updated", 
                     headers={"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {})
    for repo in r.json().get('items', [])[:4]:
        intel = (get_ai("cve", repo['description']).split('|') + ["5.0","分析中","检查"])[:3]
        cve_html += f"""
        <div class='cve-card'>
            <div style='display:flex;justify-content:space-between;'>
                <a class='cve-link' href='{repo['html_url']}'>{repo['full_name']}</a>
                <span class='badge'>{intel[0]}</span>
            </div>
            <p class='cve-sub'>{clean(intel[1])}</p>
            <p class='cve-adv'>💡 {clean(intel[2])}</p>
        </div>"""
except: cve_html = "<p>GitHub API 限制中...</p>"

# ===== 3. UI 物理布局 =====
html = f"""
<!DOCTYPE html><html><head><meta charset='utf-8'>
<style>
    :root {{ --pink: #ff007f; --blue: #00d4ff; --panel: rgba(15, 15, 25, 0.88); }}
    body {{ 
        margin:0; padding:20px; background:#05050a; color:#eee; font-family:sans-serif;
        background: linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.5)), url('{mv_bg}') center/cover fixed;
    }}
    /* 顶部重构 */
    .top-nav {{ 
        display:flex; align-items:center; background:var(--panel); padding:20px; 
        border-radius:15px; border:1px solid var(--pink); margin-bottom:20px; gap:20px;
    }}
    .main-grid {{ display:grid; grid-template-columns: 1fr 1.6fr; gap:20px; height: 75vh; }}
    .left-col {{ display:flex; flex-direction:column; gap:20px; }}
    .box {{ background:var(--panel); padding:20px; border-radius:15px; border:1px solid rgba(255,255,255,0.1); }}
    
    /* 核心修复：防止内容撑爆 */
    .word-desc {{ max-height: 250px; overflow-y: auto; font-size:14px; line-height:1.6; white-space:pre-wrap; }}
    .news-box {{ margin-top:auto; border-left:4px solid var(--pink); background:rgba(255,0,127,0.1); padding:15px; font-size:13px; }}
    
    .cve-card {{ margin-bottom:15px; padding-bottom:10px; border-bottom:1px solid rgba(255,255,255,0.05); }}
    .cve-link {{ color:var(--pink); font-weight:bold; text-decoration:none; font-size:15px; }}
    .badge {{ background:var(--blue); color:#000; padding:2px 6px; border-radius:4px; font-size:10px; font-weight:bold; }}
    .cve-adv {{ color:var(--blue); font-size:12px; margin-top:5px; }}
</style></head><body>
    <div class="top-nav">
        <img src="{cover}" style="width:80px;height:80px;border-radius:10px;border:1px solid var(--pink);">
        <div>
            <div style="font-size:10px; color:var(--pink); letter-spacing:2px;">TUYU_INTEL // V35.0</div>
            <div style="font-size:20px; font-weight:bold; margin:5px 0;">{clean(l_parts[1])}</div>
            <div style="font-size:13px; color:var(--pink);">{clean(l_parts[2])}</div>
        </div>
    </div>
    <div class="main-grid">
        <div class="left-col">
            <div class="box">
                <div style="color:var(--blue); font-size:24px; font-weight:bold; margin-bottom:10px;">{word}</div>
                <div class="word-desc">{clean(desc)}</div>
            </div>
            <div class="box news-box">
                <b style="color:var(--pink);">🎌 Japan_Study_Log:</b><br>{clean(japan)}
            </div>
        </div>
        <div class="box" style="overflow-y:auto;">
            <div style="font-size:12px; color:var(--pink); margin-bottom:15px; letter-spacing:1px;">🔥 CVE_THREAT_FEED</div>
            {cve_html}
        </div>
    </div>
</body></html>
"""
with open(os.path.join(BASE_DIR, "index.html"), "w", encoding="utf-8") as f: f.write(html)
