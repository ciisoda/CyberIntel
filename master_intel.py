import os, requests, urllib.parse, re, math
from openai import OpenAI
from datetime import datetime, date

# ===== 1. 环境配置 =====
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
        "word": "选一个网安或TUYU歌词里的日语单词+假名。",
        "desc": f"解释'{context}'并给个短例句，必须分行。",
        "japan": "三句总结日本IT/留学/签证最新动态。",
        "lyric": f"格式：歌名 | 日语歌词 | 中文翻译。选一首：{list(TUYU_ASSETS.keys())}",
        "cve": f"评分|简述|建议。内容：{context}"
    }
    try:
        res = client.chat.completions.create(model="deepseek-chat", messages=[{"role":"user","content":prompts[prompt_type]}])
        return res.choices[0].message.content.strip()
    except: return "Error | 获取失败"

# ===== 2. 逻辑获取 =====
word_raw = get_ai("word")
word = clean(word_raw)
desc = get_ai("desc", word)
japan = get_ai("japan")
lyric_raw = get_ai("lyric")
l_parts = (lyric_raw.split('|') + ["TUYU", "...", "..."])[:3]

mv_bg, cover = "mv_default.png", "cover_default.jpg"
for k, v in TUYU_ASSETS.items():
    if k in clean(l_parts[0]): mv_bg, cover = v["bg"], v["cover"]

cve_html = ""
try:
    r = requests.get("https://api.github.com/search/repositories?q=CVE-2026&sort=updated", timeout=10)
    for repo in r.json().get('items', [])[:5]:
        intel = (get_ai("cve", repo['description']).split('|') + ["5.0","分析中","检查"])[:3]
        cve_html += f"""
        <div class='cve-card'>
            <div style='display:flex;justify-content:space-between;align-items:center;'>
                <a class='cve-link' href='{repo['html_url']}'>{repo['full_name']}</a>
                <span class='badge'>{intel[0]}</span>
            </div>
            <p class='cve-sub'>{clean(intel[1])}</p>
            <p class='cve-adv'>💡 {clean(intel[2])}</p>
        </div>"""
except: cve_html = "<div class='glass-box'>GitHub 数据加载中...</div>"

# ===== 3. UI 极致协调布局 =====
html = f"""
<!DOCTYPE html><html><head><meta charset='utf-8'><meta http-equiv="refresh" content="600">
<style>
    :root {{ --pink: #ff007f; --blue: #00d4ff; --white: rgba(255, 255, 255, 0.9); }}
    body {{ 
        margin:0; padding:25px; background:#05050a; color:var(--white); font-family: 'Segoe UI', system-ui, sans-serif;
        background: linear-gradient(rgba(0,0,0,0.4), rgba(0,0,0,0.4)), url('{mv_bg}') center/cover fixed no-repeat;
    }}
    
    /* 🚩 统一毛玻璃规范 */
    .glass-box {{ 
        background: rgba(15, 15, 25, 0.7); 
        backdrop-filter: blur(12px); 
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.15); 
        border-radius: 18px; 
        padding: 22px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    }}

    .top-nav {{ display:flex; align-items:center; gap:25px; margin-bottom:25px; border: 1px solid rgba(255,0,127,0.3); }}
    .main-grid {{ display:grid; grid-template-columns: 1fr 1.6fr; gap:25px; height: 78vh; }}
    .left-col {{ display:flex; flex-direction:column; gap:25px; }}
    
    .word-title {{ color:var(--blue); font-size:26px; font-weight:bold; margin-bottom:12px; text-shadow: 0 0 10px rgba(0,212,255,0.3); }}
    .word-desc {{ font-size:14px; line-height:1.7; white-space:pre-wrap; opacity: 0.9; max-height:200px; overflow-y:auto; }}
    
    /* 🚩 新闻版块统一化 */
    .news-box {{ border-left: 4px solid var(--pink); background: rgba(255,0,127,0.1); margin-top:auto; }}
    
    .cve-card {{ margin-bottom:18px; padding-bottom:12px; border-bottom: 1px solid rgba(255,255,255,0.08); }}
    .cve-link {{ color:var(--pink); font-weight:bold; text-decoration:none; font-size:15px; transition: 0.3s; }}
    .cve-link:hover {{ text-shadow: 0 0 8px var(--pink); }}
    .badge {{ background:var(--blue); color:#000; padding:2px 7px; border-radius:5px; font-size:11px; font-weight:bold; }}
    .cve-sub {{ font-size:13px; margin:8px 0; opacity:0.8; line-height:1.5; }}
    .cve-adv {{ color:var(--blue); font-size:12px; font-style:italic; }}

    h3 {{ font-size:11px; color:var(--pink); letter-spacing:2px; text-transform:uppercase; margin-bottom:15px; border-bottom:1px solid rgba(255,0,127,0.2); padding-bottom:5px; }}
</style></head><body>

    <div class="glass-box top-nav">
        <img src="{cover}" style="width:85px;height:85px;border-radius:12px;border:1px solid var(--pink); box-shadow: 0 0 15px rgba(255,0,127,0.2);">
        <div>
            <div style="font-size:10px; color:var(--pink); letter-spacing:3px; font-weight:bold;">TUYU_STATION // V36.0</div>
            <div style="font-size:24px; font-style:italic; margin:8px 0; font-weight:300;">{clean(l_parts[1])}</div>
            <div style="font-size:14px; color:var(--pink); font-weight:500;">{clean(l_parts[2])}</div>
        </div>
    </div>

    <div class="main-grid">
        <div class="left-col">
            <div class="glass-box">
                <h3>Vocal Intel</h3>
                <div class="word-title">{word}</div>
                <div class="word-desc">{clean(desc)}</div>
            </div>
            <div class="glass-box news-box">
                <h3 style="border-bottom:none; margin-bottom:8px;">Japan Study Log</h3>
                <div style="font-size:13px; line-height:1.7; opacity:0.9;">{clean(japan)}</div>
            </div>
        </div>
        <div class="glass-box" style="overflow-y:auto;">
            <h3>Threat Intelligence Feed</h3>
            {cve_html}
        </div>
    </div>

</body></html>
    """
    with open(os.path.join(BASE_DIR, "index.html"), "w", encoding="utf-8") as f: f.write(html)
    print("V36.0 协调版已生成")

if __name__ == "__main__": run()
