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
    return escape(text).strip().replace("\n", "<br>")

def get_ai(prompt_type, ctx=""):
    prompts = {
        "word": "选一个网安日语词，标注假名，只回词。不要废话。",
        "desc": f"简单解释'{ctx}'并给个例句。不要废话。",
        "japan": "三句总结日本IT安全动态。不要废话。",
        "lyric": f"提供一句TUYU歌曲《{ctx}》的日文歌词和中文翻译。格式严格为: 歌词|翻译 。",
        "news": "作为情报猎人，极简总结:1.日元汇率 2.半导体行情 3.今日顶级Hacker标题。分三行。",
        "cve": f"作为网安专家，审计该CVE。若内容虚假分数为0。格式严格: 评分|描述|建议。内容:{ctx}"
    }
    try:
        res = client.chat.completions.create(model="deepseek-chat", messages=[{"role": "user", "content": prompts[prompt_type]}])
        return res.choices[0].message.content.strip()
    except: return "0.0|分析失败|网络超时"

def send_bark(title, content):
    if not BARK_KEY: return
    url = f"https://api.day.app/{BARK_KEY}/{title}/{content}?group=CyberIntel&icon=https://raw.githubusercontent.com/tuyu/assets/main/icon.png"
    try: requests.get(url, timeout=10)
    except: pass

def git_sync():
    if not GITHUB_TOKEN: return
    try:
        os.chdir(BASE_DIR)
        subprocess.run(["git", "add", "."], check=True)
        msg = f"Recon Sync: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        subprocess.run(["git", "commit", "-m", msg], check=True)
        remote_url = f"https://{GITHUB_TOKEN}@github.com/{GH_REPO}.git"
        subprocess.run(["git", "push", remote_url, "main", "--force"], check=True)
    except: pass

# --- 执行审计 ---
chosen_song = random.choice(list(ASSETS.keys()))
mv_bg, cover = ASSETS[chosen_song][0], ASSETS[chosen_song][1]

word = clean(get_ai("word"))
desc = clean(get_ai("desc", word))
japan = clean(get_ai("japan"))
news = clean(get_ai("news"))
lyric_raw = get_ai("lyric", chosen_song)
parts = (re.split(r"[|\n｜]", lyric_raw) + [chosen_song, "どんなに努力しても", "无论怎么努力"])[:3]

cve_html = ""
try:
    headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
    r = requests.get("https://api.github.com/search/repositories?q=CVE-2026+OR+CVE-2025&sort=updated", headers=headers, timeout=10)
    for repo in r.json().get("items", [])[:8]:
        intel = (re.split(r"[|/｜]", get_ai("cve", repo.get("description", ""))) + ["0.0", "分析中", "请核对"])[:3]
        is_poc = any(x in repo["full_name"].lower() for x in ["poc", "exploit", "bypass"])
        tag_style = "border: 1px solid #ff007f; color: #ff007f; box-shadow: 0 0 5px #ff007f;" if is_poc else ""
        cve_html += f'''
        <div class="cve-card">
            <div class="cve-top">
                <a class="cve-link" href="{repo["html_url"]}" target="_blank">{clean(repo["full_name"])}</a>
                <span class="cve-tag">SC: {clean(intel[0])}</span>
            </div>
            <div class="cve-body">{clean(intel[1])}</div>
            <div class="cve-hint">📡 SOURCE: {clean(repo["owner"]["login"])} | 💡 {clean(intel[2])}</div>
        </div>'''
except: cve_html = "<p>Feed Offline</p>"

# --- HTML 模板 (完全还原你原本的荧光特效和顶部布局) ---
full_html = f'''<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
* {{ box-sizing: border-box; }}
:root {{ --p: #ff007f; --b: #00d4ff; --bg: rgba(15, 15, 25, 0.45); }}
body {{ 
    margin:0; padding:20px; background:#05050a; color:#fff; font-family: sans-serif; 
    background-image: linear-gradient(rgba(0,0,0,0.3), rgba(0,0,0,0.6)), url('{mv_bg}'); 
    background-size:cover; background-position:center; background-attachment:fixed; 
    height:100vh; overflow:hidden; 
}}
.glass {{ 
    background: var(--bg); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); 
    border: 1px solid rgba(255, 255, 255, 0.15); border-top: 1px solid rgba(255, 255, 255, 0.3); 
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5); border-radius: 12px; padding: 18px; 
    display:flex; flex-direction:column; overflow:hidden;
}}
.header {{ height:100px; display:flex; align-items:center; gap:20px; margin-bottom:15px; border-bottom:1px solid rgba(255, 0, 127, 0.5); }}
.header img {{ width:75px; height:75px; border-radius:8px; border:1.5px solid var(--p); box-shadow: 0 0 10px rgba(255,0,127,0.4); }}
.container {{ display:grid; grid-template-columns:1fr 1.6fr; gap:15px; height:calc(100vh - 160px); }}
.scroll {{ overflow-y:auto; scrollbar-width:none; flex:1; }}
.scroll::-webkit-scrollbar {{ display:none; }}
.cve-card {{ margin-bottom:15px; padding-bottom:10px; border-bottom:1px solid rgba(255,255,255,0.08); }}
.cve-top {{ display:flex; justify-content:space-between; align-items:center; }}
.cve-link {{ color:var(--p); font-weight:bold; text-decoration:none; font-size:14px; text-shadow: 0 0 5px rgba(255,0,127,0.4); }}
.neon-blue {{ color: var(--b); text-shadow: 0 0 8px rgba(0, 212, 255, 0.7), 0 0 15px rgba(0, 212, 255, 0.4); }}
.cve-tag {{ 
    border: 1px solid var(--b); color: var(--b); padding: 0 6px; border-radius: 3px; font-size: 10px; font-weight: bold; 
    box-shadow: 0 0 5px rgba(0,212,255,0.4) inset, 0 0 5px rgba(0,212,255,0.4); text-shadow: 0 0 5px rgba(0,212,255,0.8); 
}}
.cve-body {{ font-size:12px; margin:6px 0; opacity:0.85; line-height:1.6; text-shadow: 1px 1px 2px rgba(0,0,0,0.8); }}
.cve-hint {{ font-size:11px; color:var(--b); opacity:0.9; text-shadow: 0 0 6px rgba(0,212,255,0.5); }}
.label {{ font-size:9px; color:var(--p); letter-spacing:2px; margin-bottom:8px; display:block; font-weight:bold; text-shadow: 0 0 5px rgba(255,0,127,0.4); }}
</style></head><body>
<div class="glass header"><img src="{cover}"><div><h1 style="font-size:20px;margin:0;text-shadow: 0 0 10px rgba(255,255,255,0.5);">{clean(parts[0])}</h1><p style="font-size:14px;color:var(--p);margin:4px 0 0 0;">{clean(parts[1])}</p><div style="font-size:11px;opacity:0.5;">{clean(parts[2])}</div></div></div>
<div class="container">
    <div style="display:flex;flex-direction:column;gap:15px;">
        <div class="glass" style="height:32%;"><span class="label">VOCAL_INTEL</span><div class="neon-blue" style="font-size:24px;font-weight:bold;margin-bottom:10px;">{word}</div><div class="scroll" style="text-shadow: 1px 1px 2px rgba(0,0,0,0.8);">{desc}</div></div>
        <div class="glass" style="height:32%;border-left:4px solid var(--b);"><span class="label">MARKET_RECON</span><div class="scroll" style="font-size:11px;line-height:1.5;color:#99f1ff;text-shadow: 1px 1px 2px rgba(0,0,0,0.8);">{news}</div></div>
        <div class="glass" style="height:32%;border-left:4px solid var(--p);"><span class="label">JAPAN_FEED</span><div class="scroll" style="font-size:12.5px;line-height:1.6;text-shadow: 1px 1px 2px rgba(0,0,0,0.8);">{japan}</div></div>
    </div>
    <div class="glass"><span class="label">CVE_MONITOR</span><div class="scroll">{cve_html}</div></div>
</div></body></html>'''

with open(os.path.join(BASE_DIR, "index.html"), "w", encoding="utf-8") as f: f.write(full_html)
git_sync()
send_bark("TUYU_CyberIntel", f"UI 荧光特效已完全还原。当前歌曲：《{chosen_song}》")
print("UI 还原任务完成。")
