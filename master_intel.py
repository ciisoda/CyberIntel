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

client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com", timeout=30.0)

ASSETS = {
    "くらべられっ子": ["mv_kurabe.png", "cover_kurabe.jpg"],
    "泥の分际で私だけ的大切を夺おうだなんて": ["mv_doro.png", "cover_doro.jpg"],
    "終点の先が在るとするならば。": ["mv_shuten.png", "cover_shuten.jpg"], # 🌟 已修正
    "いつかオトナになれるといいね。": ["mv_otona.png", "cover_otona.jpg"],
    "过去に囚われている": ["mv_kako.png", "cover_kako.jpg"],
    "ロックな君とはお别れだ": ["mv_rock.png", "cover_rock.jpg"]
}

def clean(text):
    if not text: return ""
    text = str(text).replace('*', '').replace('#', '').replace('「', '').replace('」', '')
    return escape(text).strip().replace("\n", "<br>")

def get_real_news(feed_url):
    """🌟 核心增强：抓取真实 RSS，杜绝 404"""
    try:
        r = requests.get(feed_url, timeout=10)
        # 用正则抓取最新的三条标题和链接
        items = re.findall(r'<item>.*?<title>(.*?)</title>.*?<link>(.*?)</link>', r.text, re.S)
        news_data = []
        for t, l in items[:3]:
            # 让 AI 把原始标题改写成更酷的情报风格
            ai_title = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": f"将此新闻标题改写成极简的网安情报风格（15字内）: {t}"}]
            ).choices[0].message.content.strip()
            news_data.append(f"{ai_title}|{l}")
        return "\n".join(news_data)
    except:
        return "Intelligence Feed Offline|#"

def get_ai(prompt_type, ctx=""):
    prompts = {
        "word": "选一个日语生活词或网安词，标注假名。只回词。不要符号。",
        "desc": f"解释'{ctx}'。若是歌词请注出处。禁止 Markdown。",
        "lyric": f"提供一句TUYU歌曲《{ctx}》的日文歌词和中文翻译。格式: 歌词|翻译",
        "cve": f"作为专家审计 CVE。评分|描述|建议。禁止星号。内容:{ctx}"
    }
    try:
        res = client.chat.completions.create(model="deepseek-chat", messages=[{"role": "user", "content": prompts[prompt_type]}])
        return res.choices[0].message.content.strip()
    except: return ""

def git_sync():
    if not GITHUB_TOKEN: return
    try:
        os.chdir(BASE_DIR)
        subprocess.run(["git", "add", "."], check=True)
        msg = f"NAS Recon Sync: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        subprocess.run(["git", "commit", "-m", msg], check=True)
        remote_url = f"https://{GITHUB_TOKEN}@github.com/{GH_REPO}.git"
        subprocess.run(["git", "push", remote_url, "main", "--force"], check=True, capture_output=True)
    except: pass

# --- 执行流程 ---
print(f"[{datetime.now()}] 启动 2026 生产级情报审计...")
chosen_song = random.choice(list(ASSETS.keys()))
mv_bg, cover = ASSETS[chosen_song][0], ASSETS[chosen_song][1]

word = clean(get_ai("word"))
desc = clean(get_ai("desc", word))
lyric_raw = get_ai("lyric", chosen_song)
# 🛠️ 修正：采用你推荐的更稳的 split 逻辑
parts = (re.split(r"[|\n｜]", lyric_raw) + ["どんなに努力しても", "无论怎么努力"])[:2]
l_parts = [chosen_song, parts[0], parts[1]]

def parse_intel_links(raw_text, color_var):
    html_out = ""
    for line in raw_text.split('\n'):
        if '|' in line:
            t, u = line.split('|', 1)
            html_out += f'<div style="margin-bottom:12px;">• {clean(t)} <a href="{u.strip()}" target="_blank" style="color:{color_var};font-size:10px;text-decoration:none;text-shadow: 0 0 5px {color_var};">[LINK]</a></div>'
    return html_out if html_out else "<div>Recon Syncing...</div>"

# 🌟 真实数据源：The Hacker News (全球) & Yahoo Japan IT (日本)
market_html = parse_intel_links(get_real_news("https://feeds.feedburner.com/TheHackersNews"), "var(--b)")
japan_html = parse_intel_links(get_real_news("https://news.yahoo.co.jp/rss/categories/it.xml"), "var(--p)")

cve_html = ""
try:
    headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
    r = requests.get("https://api.github.com/search/repositories?q=CVE-2026+OR+CVE-2025&sort=updated", headers=headers, timeout=10)
    for repo in r.json().get("items", [])[:8]:
        intel = (re.split(r"[|/｜]", get_ai("cve", repo.get("description", ""))) + ["0.0", "分析中", "请核对信息"])[:3]
        is_poc = any(x in repo["full_name"].lower() for x in ["poc", "exploit", "bypass"])
        tag_style = "border: 1px solid #ff007f; color: #ff007f; box-shadow: 0 0 5px #ff007f;" if is_poc else ""
        
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
except: cve_html = "<p>Data Feed Blocked.</p>"

# --- HTML 模板 (严格对照旧版 UI) ---
full_html = f'''<!DOCTYPE html><html><head><meta charset="utf-8"><meta http-equiv="refresh" content="600">
<style>
* {{ box-sizing: border-box; }}
:root {{ --p: #ff007f; --b: #00d4ff; --bg: rgba(15, 15, 25, 0.45); }}
body {{ margin:0; padding:20px; background:#05050a; color:#fff; font-family: sans-serif; background-image: linear-gradient(rgba(0,0,0,0.3), rgba(0,0,0,0.6)), url('{mv_bg}'); background-size:cover; background-position:center; background-attachment:fixed; height:100vh; overflow:hidden; }}
.glass {{ background: var(--bg); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.15); border-top: 1px solid rgba(255, 255, 255, 0.3); box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5); border-radius: 12px; padding: 18px; display:flex; flex-direction:column; overflow:hidden; }}
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
<div class="glass header">
    <img src="{cover}">
    <div class="header-text">
        <h1 style="font-size:20px;margin:0;text-shadow: 0 0 10px rgba(255,255,255,0.5);">{clean(l_parts[0])}</h1>
        <p style="font-size:14px;color:var(--p);margin:4px 0 0 0;font-weight:bold;">{clean(l_parts[1])}</p>
        <div style="font-size:11px;opacity:0.5;margin-top:2px;">{clean(l_parts[2])}</div>
    </div>
</div>
<div class="container">
    <div style="display:flex;flex-direction:column;gap:15px;">
        <div class="glass" style="flex:1.2;display:flex;flex-direction:column;overflow:hidden;"><span class="label">VOCAL_INTEL</span><div class="neon-blue" style="font-size:24px;font-weight:bold;margin-bottom:10px;">{word}</div><div class="scroll" style="text-shadow: 1px 1px 2px rgba(0,0,0,0.8);">{desc}</div></div>
        <div class="glass" style="flex:1;border-left:4px solid var(--b);"><span class="label">MARKET_RECON</span><div class="scroll" style="font-size:11.5px;line-height:1.7;color:#99f1ff;text-shadow: 1px 1px 2px rgba(0,0,0,0.8);">{market_html}</div></div>
        <div class="glass" style="flex:1;border-left:4px solid var(--p);"><span class="label">JAPAN_FEED</span><div class="scroll" style="font-size:11.5px;line-height:1.7;color:#ffb3d9;text-shadow: 1px 1px 2px rgba(0,0,0,0.8);">{japan_html}</div></div>
    </div>
    <div class="glass" style="display:flex;flex-direction:column;overflow:hidden;"><span class="label">CVE_MONITOR</span><div class="scroll">{cve_html}</div></div>
</div></body></html>'''

with open(os.path.join(BASE_DIR, "index.html"), "w", encoding="utf-8") as f: f.write(full_html)
git_sync()
print("2026 生产级加固完成。")
