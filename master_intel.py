import os, requests, re, subprocess, random
from openai import OpenAI
from datetime import datetime
from html import escape

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
API_KEY = os.getenv("DEEPSEEK_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# 🚩 配置区
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
    # 🌟 核心增强：加入 Tech & Financial News 审计逻辑
    prompts = {
        "word": "选一个网安日语词，标注假名，只回词。不要废话。",
        "desc": f"简单解释'{ctx}'并给个例句。不要废话。",
        "japan": "三句总结日本IT安全动态。不要废话。",
        "lyric": f"提供一句TUYU歌曲《{ctx}》的日文歌词和中文翻译。格式严格为: 歌词|翻译 。",
        "news": "作为猎人，总结当下的:1.日元汇率趋势 2.半导体或大宗行情 3.今日顶级Hacker新闻标题。分三行，极简。",
        "cve": f"审计CVE仓库。评分|描述(Win11/UWP等)|建议。内容:{ctx}"
    }
    try:
        res = client.chat.completions.create(model="deepseek-chat", messages=[{"role": "user", "content": prompts[prompt_type]}])
        return res.choices[0].message.content.strip()
    except: return "Intelligence Lost in Matrix..."

def send_bark(title, content):
    if BARK_KEY == "你的_BARK_KEY_在这里": return
    url = f"https://api.day.app/{BARK_KEY}/{title}/{content}?group=CyberIntel"
    try: requests.get(url, timeout=5)
    except: pass

def git_sync():
    if not GITHUB_TOKEN or GH_REPO == "ciisoda/你的仓库名": return
    try:
        os.chdir(BASE_DIR)
        subprocess.run(["git", "add", "."], check=True)
        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if not status.stdout.strip(): return
        msg = f"Recon Sync: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        subprocess.run(["git", "commit", "-m", msg], check=True)
        remote_url = f"https://{GITHUB_TOKEN}@github.com/{GH_REPO}.git"
        subprocess.run(["git", "push", remote_url, "main", "--force"], check=True, capture_output=True)
    except Exception as e: print(f"Git Error: {e}")

# --- 开始生成 ---
print(f"[{datetime.now()}] 启动前 0.001% 级别的多维审计...")

chosen_song = random.choice(list(ASSETS.keys()))
mv_bg, cover = ASSETS[chosen_song][0], ASSETS[chosen_song][1]

# 抓取所有情报
lyric_raw = get_ai("lyric", chosen_song)
l_parts = (re.split(r"[|\n｜]", lyric_raw) + [chosen_song, "努力は報われない", "努力不一定有回报"])[:3]

word = clean(get_ai("word"))
desc = clean(get_ai("desc", word))
japan = clean(get_ai("japan"))
news_feed = clean(get_ai("news")) # 🆕 新增的新闻板块数据

cve_html = ""
try:
    headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
    r = requests.get("https://api.github.com/search/repositories?q=CVE-2026+OR+CVE-2025&sort=updated", headers=headers, timeout=10)
    for repo in r.json().get("items", [])[:8]:
        intel = (re.split(r"[|/]", get_ai("cve", repo.get("description", ""))) + ["0.0", "分析中", "请交叉核对"])[:3]
        is_poc = any(x in repo["full_name"].lower() for x in ["poc", "exploit", "bypass"])
        tag_style = "border: 1px solid #ff007f; color: #ff007f;" if is_poc else ""
        
        cve_html += f'''
        <div class="cve-card">
            <div class="cve-top">
                <a class="cve-link" href="{repo["html_url"]}" target="_blank">{clean(repo["full_name"])}</a>
                <span class="cve-tag" style="{tag_style}">SC: {clean(intel[0])}</span>
            </div>
            <div class="cve-body">{clean(intel[1])}</div>
            <div class="cve-hint">📡 {clean(repo["owner"]["login"])} | 💡 {clean(intel[2])}</div>
        </div>'''
except: cve_html = "<p>External Feed Blocked.</p>"

# HTML 模板：微调布局以兼容新板块
full_html = f'''<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
* {{ box-sizing: border-box; }}
:root {{ --p: #ff007f; --b: #00d4ff; --bg: rgba(15, 15, 25, 0.55); }}
body {{ margin:0; padding:20px; background:#05050a; color:#fff; font-family: sans-serif; background-image: linear-gradient(rgba(0,0,0,0.4), rgba(0,0,0,0.7)), url('{mv_bg}'); background-size:cover; background-position:center; background-attachment:fixed; height:100vh; overflow:hidden; }}
.glass {{ background: var(--bg); backdrop-filter: blur(25px); -webkit-backdrop-filter: blur(25px); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; padding: 15px; display:flex; flex-direction:column; }}
.header {{ height:90px; display:flex; align-items:center; gap:20px; margin-bottom:15px; border-bottom:1px solid var(--p); }}
.header img {{ width:65px; height:65px; border-radius:8px; border:1.5px solid var(--p); }}
.container {{ display:grid; grid-template-columns:1fr 1.6fr; gap:15px; height:calc(100vh - 150px); }}
.scroll {{ overflow-y:auto; scrollbar-width:none; }}
.scroll::-webkit-scrollbar {{ display:none; }}
.cve-card {{ margin-bottom:12px; padding-bottom:8px; border-bottom:1px solid rgba(255,255,255,0.05); }}
.cve-top {{ display:flex; justify-content:space-between; align-items:center; }}
.cve-link {{ color:var(--p); font-weight:bold; text-decoration:none; font-size:13px; }}
.cve-tag {{ border: 1px solid var(--b); color: var(--b); padding: 0 5px; border-radius: 3px; font-size: 10px; }}
.cve-body {{ font-size:12px; margin:5px 0; opacity:0.8; line-height:1.4; }}
.cve-hint {{ font-size:10px; color:var(--b); opacity:0.7; }}
.label {{ font-size:9px; color:var(--p); letter-spacing:2px; margin-bottom:8px; font-weight:bold; }}
.neon-text {{ text-shadow: 0 0 8px var(--b); color: var(--b); }}
</style></head><body>
<div class="glass header"><img src="{cover}"><div><h1 style="font-size:18px;margin:0;">{clean(l_parts[0])}</h1><p style="font-size:13px;color:var(--p);margin:3px 0;">{clean(l_parts[1])}</p><div style="font-size:10px;opacity:0.4;">{clean(l_parts[2])}</div></div></div>
<div class="container">
    <div style="display:flex;flex-direction:column;gap:15px;">
        <div class="glass" style="height:32%;"><span class="label">VOCAL_INTEL</span><div class="neon-text" style="font-size:22px;font-weight:bold;margin-bottom:5px;">{word}</div><div class="scroll" style="font-size:12px;">{desc}</div></div>
        <div class="glass" style="height:32%;border-left:3px solid var(--b);"><span class="label">MARKET_RECON</span><div class="scroll" style="font-size:12px;line-height:1.5;color:#99f1ff;">{news_feed}</div></div>
        <div class="glass" style="height:32%;border-left:3px solid var(--p);"><span class="label">JAPAN_FEED</span><div class="scroll" style="font-size:12px;line-height:1.5;">{japan}</div></div>
    </div>
    <div class="glass"><span class="label">CVE_MONITOR</span><div class="scroll">{cve_html}</div></div>
</div></body></html>'''

with open(os.path.join(BASE_DIR, "index.html"), "w", encoding="utf-8") as f:
    f.write(full_html)

git_sync()
send_bark("MasterIntel_Updated", f"Tech & Financial 板块已上线。当前：{chosen_song}")
print("多维审计完成，GitHub 已同步。")
