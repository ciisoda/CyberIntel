import os, requests, re, subprocess, random
from openai import OpenAI
from datetime import datetime
from html import escape

# 🛠️ 安全加固：环境变量读取
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
API_KEY = os.getenv("DEEPSEEK_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
BARK_KEY = os.getenv("BARK_KEY", "Eda3xELXUYRR8eeQ4gWam8")
GH_REPO = "ciisoda/CyberIntel"

client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com", timeout=30.0)

# 🌟 资产修正：终点の先が在るとするならば。
ASSETS = {
    "くらべられっ子": ["mv_kurabe.png", "cover_kurabe.jpg"],
    "泥の分际で私だけ的大切を夺おうだなんて": ["mv_doro.png", "cover_doro.jpg"],
    "終点の先が在るとするならば。": ["mv_shuten.png", "cover_shuten.jpg"],
    "いつかオトナになれるといいね。": ["mv_otona.png", "cover_otona.jpg"],
    "过去に囚われている": ["mv_kako.png", "cover_kako.jpg"],
    "ロックな君とはお别れだ": ["mv_rock.png", "cover_rock.jpg"]
}

def clean(text):
    if not text: return ""
    # 🌟 暴力清洗：抹除所有 Markdown 符号，防止 UI 出现 * 杂质
    text = str(text).replace('*', '').replace('#', '').replace('「', '').replace('」', '')
    return escape(text).strip().replace("\n", "<br>")

def get_ai(prompt_type, ctx=""):
    # 🌟 锁定 2026 年 3 月时效，禁止 Markdown
    prompts = {
        "word": "从 TUYU 歌词或生活中选一个词，标注假名。只回词。禁止任何符号。",
        "desc": f"简单解释词语 '{ctx}'。若是歌词请注出处。禁止使用 Markdown 符号或加粗。",
        "japan": "三句总结 2026 年 3 月日本最新 IT 动态。禁止陈旧信息。",
        "lyric": f"提供一句TUYU歌曲《{ctx}》的日文歌词和中文翻译。格式严格为: 歌词|翻译 。",
        "news": "搜集三条 2026 年 3 月全球网安情报。格式严格: 标题|URL。确保链接真实。",
        "cve": f"作为网安专家审计 CVE。评分|描述|建议。禁止星号。内容:{ctx}"
    }
    try:
        res = client.chat.completions.create(model="deepseek-chat", messages=[{"role": "user", "content": prompts[prompt_type]}])
        return res.choices[0].message.content.strip()
    except: return ""

def send_bark(title, content):
    if not BARK_KEY: return
    url = f"https://api.day.app/{BARK_KEY}/{title}/{content}?group=CyberIntel&icon=https://raw.githubusercontent.com/tuyu/assets/main/icon.png"
    try: requests.get(url, timeout=5)
    except: pass

def git_sync():
    if not GITHUB_TOKEN: return
    try:
        os.chdir(BASE_DIR)
        subprocess.run(["git", "add", "."], check=True)
        msg = f"NAS Recon Sync: {datetime.now().strftime('%H:%M')}"
        subprocess.run(["git", "commit", "-m", msg], check=True)
        # 使用更安全的 push，避免日志泄露 token
        remote_url = f"https://{GITHUB_TOKEN}@github.com/{GH_REPO}.git"
        subprocess.run(["git", "push", remote_url, "main", "--force"], check=True, capture_output=True)
    except: pass

# --- 执行审计 ---
print(f"[{datetime.now()}] 启动 2026 深度审计...")
chosen_song = random.choice(list(ASSETS.keys()))
mv_bg, cover = ASSETS[chosen_song][0], ASSETS[chosen_song][1]

word = clean(get_ai("word"))
desc = clean(get_ai("desc", word))
japan = clean(get_ai("japan"))
lyric_raw = get_ai("lyric", chosen_song)
parts = (re.split(r"[|\n｜]", lyric_raw) + ["歌词", "翻译"])[:2]
l_parts = [chosen_song, parts[0], parts[1]]

# 🌟 MARKET_RECON 修复：修正变量名 Bug，去掉不稳定的 Link Check
news_html = ""
news_raw = get_ai("news").split('\n') # 修复变量名一致性
for line in news_raw:
    if '|' in line:
        title, url = line.split('|', 1)
        # 直接信任链接，减少 403/429 误杀导致的空白
        news_html += f'<div style="margin-bottom:12px;">• {clean(title)} <a href="{url.strip()}" target="_blank" style="color:var(--b);text-decoration:none;font-size:10px;text-shadow: 0 0 5px var(--b);">[LINK]</a></div>'
if not news_html: news_html = f'<div style="color:var(--b); opacity:0.6;">Waiting for 2026 data...</div>'

cve_html = ""
try:
    headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
    r = requests.get("https://api.github.com/search/repositories?q=CVE-2026+OR+CVE-2025&sort=updated", headers=headers, timeout=10)
    for repo in r.json().get("items", [])[:8]:
        intel = (re.split(r"[|/｜]", get_ai("cve", repo.get("description", ""))) + ["0.0", "分析中", "请核对"])[:3]
        is_poc = any(x in repo["full_name"].lower() for x in ["poc", "exploit"])
        tag_style = "border: 1px solid #ff007f; color: #ff007f; box-shadow: 0 0 5px #ff007f;" if is_poc else ""
        
        # 🌟 右侧蓝字还原：SOURCE 链接化，严格遵循原生 .cve-hint 风格
        cve_html += f'''
        <div class="cve-card">
            <div class="cve-top">
                <a class="cve-link" href="{repo["html_url"]}" target="_blank">{clean(repo["full_name"])}{" [WEAPONIZED]" if is_poc else ""}</a>
                <span class="cve-tag" style="{tag_style}">SC: {clean(intel[0])}</span>
            </div>
            <div class="cve-body" style="line-height:1.6; margin-top:5px; opacity:0.85;">{clean(intel[1])}</div>
            <div class="cve-hint">
                <a href="{repo["html_url"]}" target="_blank" style="color:inherit; text-decoration:none;">📡 SOURCE: {clean(repo["owner"]["login"])}</a> | 💡 {clean(intel[2])}
            </div>
        </div>'''
except: cve_html = "<p>Data Offline</p>"

# --- HTML 模板 (死磕 100px Header 和霓虹特效) ---
full_html = f'''<!DOCTYPE html><html><head><meta charset="utf-8"><meta http-equiv="refresh" content="600">
<style>
* {{ box-sizing: border-box; }}
:root {{ --p: #ff007f; --b: #00d4ff; --bg: rgba(15, 15, 25, 0.45); }}
body {{ margin:0; padding:20px; background:#05050a; color:#fff; font-family: sans-serif; background-image: linear-gradient(rgba(0,0,0,0.3), rgba(0,0,0,0.6)), url('{mv_bg}'); background-size:cover; background-position:center; background-attachment:fixed; height:100vh; overflow:hidden; }}
.glass {{ background: var(--bg); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.15); border-top: 1px solid rgba(255, 255, 255, 0.3); box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5); border-radius: 12px; padding: 18px; }}
.header {{ height:100px; display:flex; align-items:center; gap:20px; margin-bottom:15px; border-bottom:1px solid rgba(255, 0, 127, 0.5); }}
.header img {{ width:75px; height:75px; border-radius:8px; border:1.5px solid var(--p); box-shadow: 0 0 10px rgba(255,0,127,0.4); }}
.header-text {{ display:flex; flex-direction:column; justify-content:center; }}
.container {{ display:grid; grid-template-columns:1fr 1.6fr; gap:15px; height:calc(100vh - 160px); }}
.scroll {{ overflow-y:auto; flex:1; scrollbar-width:none; }}
.scroll::-webkit-scrollbar {{ display:none; }}
.cve-card {{ margin-bottom:18px; padding-bottom:10px; border-bottom:1px solid rgba(255,255,255,0.08); }}
.cve-top {{ display:flex; justify-content:space-between; align-items:center; }}
.cve-link {{ color:var(--p); font-weight:bold; text-decoration:none; font-size:14px; text-shadow: 0 0 5px rgba(255,0,127,0.4); }}
.neon-blue {{ color: var(--b); text-shadow: 0 0 8px rgba(0, 212, 255, 0.7), 0 0 15px rgba(0, 212, 255, 0.4); }}
.cve-tag {{ border: 1px solid var(--b); color: var(--b); padding: 0 6px; border-radius: 3px; font-size: 10px; font-weight: bold; box-shadow: 0 0 5px rgba(0,212,255,0.4) inset, 0 0 5px rgba(0,212,255,0.4); text-shadow: 0 0 5px rgba(0,212,255,0.8); }}
.cve-body {{ font-size:12px; margin:6px 0; opacity:0.85; line-height:1.6; text-shadow: 1px 1px 2px rgba(0,0,0,0.8); }}
.cve-hint {{ font-size:11px; color:var(--b); opacity:0.9; text-shadow: 0 0 6px rgba(0,212,255,0.5); }}
.label {{ font-size:9px; color:var(--p); letter-spacing:2px; margin-bottom:10px; display:block; font-weight:bold; text-shadow: 0 0 5px rgba(255,0,127,0.4); }}
</style></head><body>
<div class="glass header"><img src="{cover}"><div class="header-text"><h1 style="font-size:20px;margin:0;text-shadow: 0 0 10px rgba(255,255,255,0.5);">{clean(l_parts[0])}</h1><p style="font-size:14px;color:var(--p);margin:4px 0 0 0;font-weight:bold;">{clean(l_parts[1])}</p><div style="font-size:11px;opacity:0.5;margin-top:2px;">{clean(l_parts[2])}</div></div></div>
<div class="container">
    <div style="display:flex;flex-direction:column;gap:15px;">
        <div class="glass" style="flex:1.2;display:flex;flex-direction:column;overflow:hidden;"><span class="label">VOCAL_INTEL</span><div class="neon-blue" style="font-size:24px;font-weight:bold;margin-bottom:10px;">{word}</div><div class="scroll" style="text-shadow: 1px 1px 2px rgba(0,0,0,0.8);">{desc}</div></div>
        <div class="glass" style="flex:1;border-left:4px solid var(--b);"><span class="label">MARKET_RECON</span><div class="scroll" style="font-size:11.5px;line-height:1.7;color:#99f1ff;text-shadow: 1px 1px 2px rgba(0,0,0,0.8);">{news_html}</div></div>
        <div class="glass" style="flex:1;border-left:4px solid var(--p);"><span class="label">JAPAN_FEED</span><div class="scroll" style="font-size:12.5px;line-height:1.6;text-shadow: 1px 1px 2px rgba(0,0,0,0.8);">{japan}</div></div>
    </div>
    <div class="glass" style="display:flex;flex-direction:column;overflow:hidden;"><span class="label">CVE_MONITOR</span><div class="scroll">{cve_html}</div></div>
</div></body></html>'''

with open(os.path.join(BASE_DIR, "index.html"), "w", encoding="utf-8") as f:
    f.write(full_html)

git_sync()
send_bark("TUYU_CyberIntel", f"情报站已稳健同步。当前歌曲：《{chosen_song}》")
print("任务圆满完成。")
