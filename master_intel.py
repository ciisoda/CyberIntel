import os, requests, re, subprocess, random
from openai import OpenAI
from datetime import datetime
from html import escape

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
API_KEY = os.getenv("DEEPSEEK_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# 🚩 配置
BARK_KEY = "Eda3xELXUYRR8eeQ4gWam8"
GH_REPO = "ciisoda/CyberIntel"

client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com", timeout=25.0)

ASSETS = {
    "くらべられっ子": ["mv_kurabe.png", "cover_kurabe.jpg"],
    "泥の分际で私だけ的大切を夺おうだなんて": ["mv_doro.png", "cover_doro.jpg"],
    "终点へと向かう楽曲": ["mv_shuten.png", "cover_shuten.jpg"],
    "いつかオトナになれるといいね。": ["mv_otona.png", "cover_otona.jpg"],
    "过去に囚われている": ["mv_kako.png", "cover_kako.jpg"],
    "ロックな君とはお别れだ": ["mv_rock.png", "cover_rock.jpg"]
}

def clean(text):
    if not text: return ""
    text = str(text).replace('「', '').replace('」', '')
    text = re.sub(r'[#*`>\-]', '', text)
    return escape(text).strip().replace("\n", " ")

def get_ai(prompt_type, ctx=""):
    prompts = {
        "word": "选一个网安日语词，标注假名，只回词。",
        "desc": f"简单解释'{ctx}'并给个例句。",
        "japan": "三句总结日本IT安全动态。",
        "lyric": f"提供一句TUYU歌曲《{ctx}》的日文歌词和中文翻译。格式: 歌词|翻译",
        "news": "总结:1.日元汇率 2.半导体行情 3.今日顶级Hacker标题。分三行。",
        "cve": f"审计该CVE。若虚假则分数为0。格式: 分数|描述|建议。内容:{ctx}"
    }
    try:
        res = client.chat.completions.create(model="deepseek-chat", messages=[{"role": "user", "content": prompts[prompt_type]}])
        return res.choices[0].message.content.strip()
    except: return "0.0|分析失败|网络波动"

def send_bark(title, content):
    if not BARK_KEY: return
    url = f"https://api.day.app/{BARK_KEY}/{title}/{content}?group=CyberIntel"
    try: requests.get(url, timeout=10)
    except: pass

def git_sync():
    if not GITHUB_TOKEN: return
    try:
        os.chdir(BASE_DIR)
        subprocess.run(["git", "add", "."], check=True)
        msg = f"Final Fix: {datetime.now().strftime('%H:%M')}"
        subprocess.run(["git", "commit", "-m", msg], check=True)
        remote_url = f"https://{GITHUB_TOKEN}@github.com/{GH_REPO}.git"
        subprocess.run(["git", "push", remote_url, "main", "--force"], check=True)
    except: pass

# --- 数据准备 ---
chosen_song = random.choice(list(ASSETS.keys()))
mv_bg, cover = ASSETS[chosen_song][0], ASSETS[chosen_song][1]

word = clean(get_ai("word"))
desc = clean(get_ai("desc", word))
japan = clean(get_ai("japan"))
news = clean(get_ai("news"))
lyric_raw = get_ai("lyric", chosen_song)
parts = (re.split(r"[|\n｜]", lyric_raw) + [chosen_song, "努力は報われない", "努力不一定有回报"])[:3]

cve_html = ""
try:
    headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
    r = requests.get("https://api.github.com/search/repositories?q=CVE-2026+OR+CVE-2025&sort=updated", headers=headers, timeout=10)
    for repo in r.json().get("items", [])[:8]:
        intel = (re.split(r"[|/｜]", get_ai("cve", repo.get("description", ""))) + ["0.0", "分析中", "请核对"])[:3]
        is_poc = any(x in repo["full_name"].lower() for x in ["poc", "exploit", "rce"])
        tag_color = "#ff007f" if is_poc or float(intel[0] if intel[0].replace('.','',1).isdigit() else 0) > 7 else "#00d4ff"
        
        cve_html += f'''
        <div class="cve-card">
            <div class="cve-top">
                <a class="cve-link" style="color:{tag_color}" href="{repo["html_url"]}" target="_blank">{clean(repo["full_name"])}</a>
                <span class="cve-tag" style="border-color:{tag_color};color:{tag_color}">SC: {intel[0]}</span>
            </div>
            <div class="cve-body">{clean(intel[1])}</div>
            <div class="cve-hint">📡 {clean(repo["owner"]["login"])} | 💡 {clean(intel[2])}</div>
        </div>'''
except: cve_html = "<p>Data Offline</p>"

# --- HTML 模板 (修复了顶部对齐和语法截断) ---
full_html = f'''<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
* {{ box-sizing: border-box; }}
:root {{ --p: #ff007f; --b: #00d4ff; --bg: rgba(15, 15, 25, 0.6); }}
body {{ 
    margin:0; padding:15px; background:#05050a; color:#fff; font-family: sans-serif; 
    background: linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.8)), url('{mv_bg}') no-repeat center center fixed; 
    background-size: cover; height:100vh; overflow:hidden; 
}}
.glass {{ background: var(--bg); backdrop-filter: blur(25px); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; padding: 15px; display:flex; flex-direction:column; overflow:hidden; }}
.header {{ height:85px; display:flex; align-items:center; gap:15px; margin-bottom:15px; border: 1px solid var(--p); }}
.header img {{ width:55px; height:55px; border-radius:6px; border:1px solid var(--p); }}
.container {{ display:grid; grid-template-columns:1fr 1.6fr; gap:15px; height:calc(100vh - 135px); }}
.scroll {{ overflow-y:auto; scrollbar-width:none; }}
.scroll::-webkit-scrollbar {{ display:none; }}
.cve-card {{ margin-bottom:10px; padding-bottom:8px; border-bottom:1px solid rgba(255,255,255,0.05); }}
.cve-top {{ display:flex; justify-content:space-between; }}
.cve-link {{ font-weight:bold; text-decoration:none; font-size:13px; }}
.cve-tag {{ border: 1px solid; padding: 0 4px; border-radius: 3px; font-size: 10px; }}
.cve-body {{ font-size:11.5px; margin:4px 0; opacity:0.8; line-height:1.4; }}
.label {{ font-size:9px; color:var(--p); letter-spacing:1px; margin-bottom:6px; font-weight:bold; }}
</style></head><body>
<div class="glass header"><img src="{cover}"><div><h1 style="font-size:16px;margin:0;">{clean(parts[0])}</h1><p style="font-size:12px;color:var(--p);margin:2px 0;">{clean(parts[1])}</p><div style="font-size:9px;opacity:0.4;">{clean(parts[2])}</div></div></div>
<div class="container">
    <div style="display:flex;flex-direction:column;gap:15px;">
        <div class="glass" style="height:32%;"><span class="label">VOCAL_INTEL</span><div style="color:var(--b);font-size:18px;font-weight:bold;">{word}</div><div class="scroll" style="font-size:11px;">{desc}</div></div>
        <div class="glass" style="height:32%;border-left:3px solid var(--b);"><span class="label">MARKET_RECON</span><div class="scroll" style="font-size:11px;line-height:1.5;color:#99f1ff;">{news}</div></div>
        <div class="glass" style="height:32%;border-left:3px solid var(--p);"><span class="label">JAPAN_FEED</span><div class="scroll" style="font-size:11px;line-height:1.5;">{japan}</div></div>
    </div>
    <div class="glass"><span class="label">CVE_MONITOR</span><div class="scroll">{cve_html}</div></div>
</div></body></html>'''

with open(os.path.join(BASE_DIR, "index.html"), "w", encoding="utf-8") as f: f.write(full_html)
git_sync()
send_bark("CyberIntel_Sync", f"Recon 任务已完成。当前图源:《{chosen_song}》")
print("任务圆满完成。")
