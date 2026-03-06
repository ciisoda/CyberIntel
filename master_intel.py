import os, requests, re, subprocess, random
from openai import OpenAI
from datetime import datetime
from html import escape

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
API_KEY = os.getenv("DEEPSEEK_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# 🚩 填入你的 Bark Key 和 GitHub 仓库
BARK_KEY = "Eda3xELXUYRR8eeQ4gWam8"
GH_REPO = "ciisoda/CyberIntel"

client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com", timeout=25.0)

ASSETS = {
    "くらべられっ子": ["mv_kurabe.png", "cover_kurabe.jpg"],
    "泥の分際で私だけの大切を夺おうだなんて": ["mv_doro.png", "cover_doro.jpg"],
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
        "lyric": f"提供一句TUYU歌曲《{ctx}》的日文歌词和中文翻译。格式严格为: 歌词|翻译 。切勿包含其他废话。",
        "cve": f"提取内容格式严格为: 评分|一句话简述|一句话建议。内容:{ctx}"
    }
    try:
        res = client.chat.completions.create(model="deepseek-chat", messages=[{"role": "user", "content": prompts[prompt_type]}])
        return res.choices[0].message.content.strip()
    except: return ""

def send_bark(title, content):
    if BARK_KEY == "你的_BARK_KEY_在这里": return
    url = f"https://api.day.app/{BARK_KEY}/{title}/{content}?group=CyberIntel&icon=https://raw.githubusercontent.com/tuyu/assets/main/icon.png"
    try: requests.get(url, timeout=5)
    except: pass

def git_sync():
    if not GITHUB_TOKEN or GH_REPO == "ciisoda/你的仓库名": return
    try:
        os.chdir(BASE_DIR)
        subprocess.run(["git", "config", "--global", "--add", "safe.directory", BASE_DIR], check=False)
        subprocess.run(["git", "add", "."], check=True)
        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if not status.stdout.strip():
            print("Git Sync: 网页内容无变化，无需重复备份。")
            return
        msg = f"NAS Auto Sync: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        subprocess.run(["git", "commit", "-m", msg], check=True)
        remote_url = f"https://{GITHUB_TOKEN}@github.com/{GH_REPO}.git"
        try:
            subprocess.run(["git", "push", remote_url, "main", "--force"], check=True, capture_output=True)
            print("GitHub Sync Success (main 分支)")
        except subprocess.CalledProcessError:
            subprocess.run(["git", "push", remote_url, "master", "--force"], check=True)
            print("GitHub Sync Success (master 分支)")
    except Exception as e: print(f"Git Error: {e}")

print(f"[{datetime.now()}] 正在连线获取情报...")

# 🌟 核心修改：Python 亲自当 DJ 随机切歌和换壁纸
chosen_song = random.choice(list(ASSETS.keys()))
mv_bg, cover = ASSETS[chosen_song][0], ASSETS[chosen_song][1]

# 告诉 AI 查这首歌的歌词
lyric_raw = get_ai("lyric", chosen_song)
parts = re.split(r"[|\n｜]", lyric_raw)
parts = [p.strip() for p in parts if p.strip() and "歌" not in p and "译" not in p]

if len(parts) >= 2:
    l_parts = [chosen_song, parts[0], parts[1]]
else:
    l_parts = [chosen_song, "どんなに努力しても", "无论怎么努力"] # 备用歌词

word = clean(get_ai("word"))
desc = clean(get_ai("desc", word))
japan = clean(get_ai("japan"))

cve_html = ""
try:
    headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
    r = requests.get("https://api.github.com/search/repositories?q=CVE-2026&sort=updated", headers=headers, timeout=10)
    for repo in r.json().get("items", [])[:6]:
        intel_raw = get_ai("cve", repo.get("description", ""))
        intel = (re.split(r"[|/]", intel_raw) + ["5.0", "分析中", "建议检查"])[:3]
        cve_html += f'<div class="cve-card"><div class="cve-top"><a class="cve-link" href="{repo["html_url"]}" target="_blank">{clean(repo["full_name"])}</a><span class="cve-tag">SC: {clean(intel[0])}</span></div><div class="cve-body">{clean(intel[1])}</div><div class="cve-hint">💡 {clean(intel[2])}</div></div>'
except: cve_html = "<p>Feed Offline</p>"

full_html = f'''<!DOCTYPE html><html><head><meta charset="utf-8"><meta http-equiv="refresh" content="600">
<style>
* {{ box-sizing: border-box; }}
:root {{ --p: #ff007f; --b: #00d4ff; --bg: rgba(15, 15, 25, 0.45); }}
body {{ margin:0; padding:20px; background:#05050a; color:#fff; font-family: sans-serif; background-image: linear-gradient(rgba(0,0,0,0.3), rgba(0,0,0,0.6)), url('{mv_bg}'); background-size:cover; background-position:center; background-attachment:fixed; height:100vh; overflow:hidden; }}
.glass {{ background: var(--bg); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.15); border-top: 1px solid rgba(255, 255, 255, 0.3); box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5); border-radius: 12px; padding: 18px; }}
.header {{ height:100px; display:flex; align-items:center; gap:20px; margin-bottom:15px; border-bottom:1px solid rgba(255, 0, 127, 0.5); }}
.header img {{ width:75px; height:75px; border-radius:8px; border:1.5px solid var(--p); box-shadow: 0 0 10px rgba(255,0,127,0.4); }}
.container {{ display:grid; grid-template-columns:1fr 1.6fr; gap:15px; height:calc(100vh - 160px); }}
.scroll {{ overflow-y:auto; flex:1; scrollbar-width:none; }}
.scroll::-webkit-scrollbar {{ display:none; }}
.cve-card {{ margin-bottom:15px; padding-bottom:10px; border-bottom:1px solid rgba(255,255,255,0.08); }}
.cve-top {{ display:flex; justify-content:space-between; align-items:center; }}
.cve-link {{ color:var(--p); font-weight:bold; text-decoration:none; font-size:14px; text-shadow: 0 0 5px rgba(255,0,127,0.4); }}
.neon-blue {{ color: var(--b); text-shadow: 0 0 8px rgba(0, 212, 255, 0.7), 0 0 15px rgba(0, 212, 255, 0.4); }}
.cve-tag {{ border: 1px solid var(--b); color: var(--b); padding: 0 6px; border-radius: 3px; font-size: 10px; font-weight: bold; box-shadow: 0 0 5px rgba(0,212,255,0.4) inset, 0 0 5px rgba(0,212,255,0.4); text-shadow: 0 0 5px rgba(0,212,255,0.8); }}
.cve-body {{ font-size:12px; margin:6px 0; opacity:0.85; line-height:1.6; text-shadow: 1px 1px 2px rgba(0,0,0,0.8); }}
.cve-hint {{ font-size:11px; color:var(--b); opacity:0.9; text-shadow: 0 0 6px rgba(0,212,255,0.5); }}
.label {{ font-size:9px; color:var(--p); letter-spacing:2px; margin-bottom:8px; display:block; font-weight:bold; text-shadow: 0 0 5px rgba(255,0,127,0.4); }}
</style></head><body>
<div class="glass header"><img src="{cover}"><div><h1 style="font-size:20px;margin:0;text-shadow: 0 0 10px rgba(255,255,255,0.5);">{clean(l_parts[0])}</h1><p style="font-size:14px;color:var(--p);margin:4px 0 0 0;">{clean(l_parts[1])}</p><div style="font-size:11px;opacity:0.5;">{clean(l_parts[2])}</div></div></div>
<div class="container"><div style="display:flex;flex-direction:column;gap:15px;"><div class="glass" style="flex:1.5;display:flex;flex-direction:column;overflow:hidden;"><span class="label">VOCAL_INTEL</span><div class="neon-blue" style="font-size:24px;font-weight:bold;margin-bottom:10px;">{word}</div><div class="scroll" style="text-shadow: 1px 1px 2px rgba(0,0,0,0.8);">{desc}</div></div><div class="glass" style="flex:1;border-left:4px solid var(--p);"><span class="label">JAPAN_FEED</span><div class="scroll" style="font-size:12.5px;line-height:1.6;text-shadow: 1px 1px 2px rgba(0,0,0,0.8);">{japan}</div></div></div><div class="glass" style="display:flex;flex-direction:column;overflow:hidden;"><span class="label">CVE_MONITOR</span><div class="scroll">{cve_html}</div></div></div></body></html>'''

with open(os.path.join(BASE_DIR, "index.html"), "w", encoding="utf-8") as f:
    f.write(full_html)

git_sync()
send_bark("TUYU_CyberIntel", f"情报站更新！壁纸切到了: 《{chosen_song}》")
print("全流程执行完毕！")
