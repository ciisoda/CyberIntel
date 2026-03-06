import os, requests, re, subprocess
from openai import OpenAI
from datetime import datetime
from html import escape

# ========= 1. 核心配置与初始化 =========
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
API_KEY = os.getenv("DEEPSEEK_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# 🚩【填入你的 Bark Key，例如 "PDU2xxxx"】
BARK_KEY = "Eda3xELXUYRR8eeQ4gWam8"
# 🚩【填入你的 GitHub 仓库信息，例如 "ciisoda/tuyu-intel"】
GH_REPO = "ciisoda/CyberIntel"

client = OpenAI(
    api_key=API_KEY,
    base_url="https://api.deepseek.com",
    timeout=25.0
)

ASSETS = {
    "くらべられっ子": ["mv_kurabe.png", "cover_kurabe.jpg"],
    "泥の分際で私だけの大切を夺おうだなんて": ["mv_doro.png", "cover_doro.jpg"],
    "终点へと向かう楽曲": ["mv_shuten.png", "cover_shuten.jpg"],
    "いつかオトナになれるといいね。": ["mv_otona.png", "cover_otona.jpg"],
    "过去に囚われている": ["mv_kako.png", "cover_kako.jpg"],
    "ロックな君とはお别れだ": ["mv_rock.png", "cover_rock.jpg"]
}

# ========= 2. 功能插件库 =========

def clean(text):
    if not text: return ""
    text = str(text).replace('「', '').replace('」', '')
    text = re.sub(r'[#*`>\-]', '', text)
    return escape(text).strip().replace("\n", "<br>")

def get_ai(prompt_type, ctx=""):
    prompts = {
        "word": "选一个网安日语词，标注假名，只回词。",
        "desc": f"简单解释'{ctx}'并给个例句。",
        "japan": "三句总结日本IT动态。",
        "lyric": f"格式:歌名|歌词|翻译。选一首:{list(ASSETS.keys())}",
        "cve": f"评分|简述|建议。内容:{ctx}"
    }
    try:
        res = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompts[prompt_type]}]
        )
        return res.choices[0].message.content.strip()
    except: return ""

def send_bark(title, content):
    """Bark 手机推送插件"""
    if BARK_KEY == "你的_BARK_KEY_在这里": return
    url = f"https://api.day.app/{BARK_KEY}/{title}/{content}?group=CyberIntel&icon=https://raw.githubusercontent.com/tuyu/assets/main/icon.png"
    try: requests.get(url, timeout=5)
    except: print("Bark Push Failed")

def git_sync():
    """GitHub 自动备份插件 (已修复权限问题)"""
    if not GITHUB_TOKEN or GH_REPO == "ciisoda/你的仓库名": return
    try:
        os.chdir(BASE_DIR)
        # 修复 Git 领地所有权报错
        subprocess.run(["git", "config", "--global", "--add", "safe.directory", BASE_DIR], check=False)
        
        subprocess.run(["git", "add", "."], check=True)
        msg = f"NAS Auto Sync: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        subprocess.run(["git", "commit", "-m", msg], check=True)
        
        remote_url = f"https://{GITHUB_TOKEN}@github.com/{GH_REPO}.git"
        subprocess.run(["git", "push", remote_url, "main", "--force"], check=True)
        print("GitHub Sync Success")
    except Exception as e:
        print(f"Git Error: {e}")

# ========= 3. 数据处理流 =========

print(f"[{datetime.now()}] 正在连线获取情报...")

lyric_raw = get_ai("lyric")
parts = re.split(r"[|\n｜]", lyric_raw)
l_parts = [p.strip() for p in parts if p.strip()]
if len(l_parts) < 3:
    l_parts = ["くらべられっ子", "あの子になりたかった", "我曾想成为那个孩子"]

mv_bg, cover = "mv_default.png", "cover_default.jpg"
for k, v in ASSETS.items():
    if k in l_parts[0] or l_parts[0] in k:
        mv_bg, cover = v[0], v[1]
        break

word = clean(get_ai("word"))
desc = clean(get_ai("desc", word))
japan = clean(get_ai("japan"))

cve_html = ""
try:
    headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
    api_url = "https://api.github.com/search/repositories?q=CVE-2026&sort=updated"
    r = requests.get(api_url, headers=headers, timeout=10)
    repos = r.json().get("items", [])[:6]
    for repo in repos:
        intel_raw = get_ai("cve", repo.get("description", ""))
        intel = (re.split(r"[|/]", intel_raw) + ["5.0", "分析中", "建议检查"])[:3]
        cve_html += f"""
        <div class="cve-card">
            <div class="cve-top">
                <a class="cve-link" href="{repo['html_url']}" target="_blank">{clean(repo['full_name'])}</a>
                <span class="cve-tag">SC: {clean(intel[0])}</span>
            </div>
            <div class="cve-body">{clean(intel[1])}</div>
            <div class="cve-hint">💡 {clean(intel[2])}</div>
        </div>"""
except: cve_html = "<p>Feed Offline</p>"

# ========= 4. 生成 HTML (极致 UI 优化版) =========

full_html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><meta http-equiv="refresh" content="600">
<style>
* {{ box-sizing: border-box; }}
:root {{ 
    --p: #ff007f; /* 粉色 */
    --b: #00d4ff; /* 荧光蓝 */
    --bg: rgba(15, 15, 25, 0.45); /* 调低透明度，让背景图透出来 */
}}
body {{ 
    margin:0; padding:20px; background:#05050a; color:#fff; font-family: sans-serif;
    background-image: linear-gradient(rgba(0,0,0,0.3), rgba(0,0,0,0.6)), url('{mv_bg}');
    background-size:cover; background-position:center; background-attachment:fixed;
    height:100vh; overflow:hidden;
}}
/* 极致毛玻璃效果 */
.glass {{ 
    background: var(--bg); 
    backdrop-filter: blur(20px); 
    -webkit-backdrop-filter: blur(20px); 
    border: 1px solid rgba(255, 255, 255, 0.15); 
    border-top: 1px solid rgba(255, 255, 255, 0.3); /* 顶部高光反射 */
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5); /* 立体阴影 */
    border-radius: 12px; 
    padding: 18px; 
}}
.header {{ height:100px; display:flex; align-items:center; gap:20px; margin-bottom:15px; border-bottom:1px solid rgba(255, 0, 127, 0.5); }}
.header img {{ width:75px; height:75px; border-radius:8px; border:1.5px solid var(--p); box-shadow: 0 0 10px rgba(255,0,127,0.4); }}
.container {{ display:grid; grid-template-columns:1fr 1.6fr; gap:15px; height:calc(100vh - 160px); }}
.scroll {{ overflow-y:auto; flex:1; scrollbar-width:none; }}
.scroll::-webkit-scrollbar {{ display:none; }}
.cve-card {{ margin-bottom:15px; padding-bottom:10px; border-bottom:1px solid rgba(255,255,255,0.08); }}
.cve-top {{ display:flex; justify-content:space-between; align-items:center; }}
.cve-link {{ color:var(--p); font-weight:bold; text-decoration:none; font-size:14px; text-shadow: 0 0 5px rgba(255,0,127,0.4); }}

/* 荧光蓝 发光效果 */
.neon-blue {{
    color: var(--b);
    text-shadow: 0 0 8px rgba(0, 212, 255, 0.7), 0 0 15px rgba(0, 212, 255, 0.4);
}}
.cve-tag {{ 
    border: 1px solid var(--b); 
    color: var(--b); 
    padding: 0 6px; 
    border-radius: 3px; 
    font-size: 10px; 
    font-weight: bold; 
    box-shadow: 0 0 5px rgba(0,212,255,0.4) inset, 0 0 5px rgba(0,212,255,0.4); /* 边框发光 */
    text-shadow: 0 0 5px rgba(0,212,255,0.8);
}}
.cve-body {{ font-size:12px; margin:6px 0; opacity:0.85; line-height:1.6; text-shadow: 1px 1px 2px rgba(0,0,0,0.8); }}
.cve-hint {{ font-size:11px; color:var(--b); opacity:0.9; text-shadow: 0 0 6px rgba(0,212,255,0.5); }}
.label {{ font-size:9px; color:var(--p); letter-spacing:2px; margin-bottom:8px; display:block; font-weight:bold; text-shadow: 0 0 5px rgba(255,0,127,0.4); }}
</style></head><body>
<div class="glass header">
    <img src="{cover}">
    <div>
        <h1 style="font-size:20px;margin:0;text-shadow: 0 0 10px rgba(255,255,255,0.5);">{clean(l_parts[0])}</h1>
        <p style="font-size:14px;color:var(--p);margin:4px 0 0 0;">{clean(l_parts[1])}</p>
        <div style="font-size:11px;opacity:0.5;">{clean(l_parts[2])}</div>
    </div>
</div>
<div class="container">
    <div style="display:flex;flex-direction:column;gap:15px;">
        <div class="glass" style="flex:1.5;display:flex;flex-direction:column;overflow:hidden;">
            <span class="label">VOCAL_INTEL</span>
            <div class="neon-blue" style="font-size:24px;font-weight:bold;margin-bottom:10px;">{word}</div>
            <div class="scroll" style="text-shadow: 1px 1px 2px rgba(0,0,0,0.8);">{desc}</div>
        </div>
        <div class="glass" style="flex:1;border-left:4px solid var(--p);">
            <span class="label">JAPAN_FEED</span>
            <div class="scroll" style="font-size:12.5px;line-height:1.6;text-shadow: 1px 1px 2px rgba(0,0,0,0.8);">{japan}</div>
        </div>
    </div>
    <div class="glass" style="display:flex;flex-direction:column;overflow:hidden;">
        <span class="label">CVE_MONITOR</span>
        <div class="scroll">{cve_html}</div>
    </div>
</div></body></html>"""

# 写入文件
with open(os.path.join(BASE_DIR, "index.html"), "w", encoding="utf-8") as f:
    f.write(full_html)

# ⚠️ 注意：网页快照功能 (Playwright) 已暂时禁用，防止群晖系统缺少库导致报错中断流程。
# take_snapshot(...)

# 执行 Git 备份到 GitHub
git_sync()

# 发送 Bark 推送
send_bark("TUYU_CyberIntel", f"情报站已更新！今日关键词: {word}")
print("全流程执行完毕！")
