import os, requests, re, subprocess, random
from openai import OpenAI
from datetime import datetime
from html import escape

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
API_KEY = os.getenv("DEEPSEEK_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# 🚩 你的 Bark Key 和 GitHub 仓库 (保持不变)
BARK_KEY = "Eda3xELXUYRR8eeQ4gWam8"
GH_REPO = "ciisoda/CyberIntel"

# 增加超时时间并给默认占位符，防止初始化崩溃
client = OpenAI(api_key=API_KEY or "dummy_key", base_url="https://api.deepseek.com", timeout=60.0)

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
    text = str(text).replace('*', '').replace('#', '').replace('「', '').replace('」', '')
    return escape(text).strip().replace("\n", "<br>")

def get_real_rss(url):
    try:
        r = requests.get(url, timeout=10)
        items = re.findall(r'<item>.*?<title>(.*?)</title>.*?<link>(.*?)</link>', r.text, re.S)
        news_data = []
        for t, l in items[:3]:
            print(f"   [抓取新闻] 正在用 AI 总结: {t[:10]}...", end="", flush=True)
            try:
                summary = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "user", "content": f"将此标题翻译并改写为10字内网安情报风格: {t}"}]
                ).choices[0].message.content.strip()
                print(" ✅")
            except:
                summary = t[:15] + "..."
                print(" ❌(超时或欠费，使用原标题)")
            news_data.append(f"{clean(summary)}|{l}")
        return "\n".join(news_data)
    except: return "Intel Feed Offline|#"

def get_ai(prompt_type, ctx=""):
    # 🌟 随机盲盒：打破 AI 的词汇复读机限制
    domains = ["恶意软件", "密码学", "渗透测试", "社会工程学", "零信任架构", "红蓝对抗", "暗网情报", "网络取证"]
    rnd_domain = random.choice(domains)
    
    prompts = {
        "word": f"作为网安专家，在【{rnd_domain}】领域随机选一个极度冷门的日语专业词汇，标注假名，只回词。绝不要输出 ゼロデイ 或 エクスプロイト。",
        "desc": f"简单解释'{ctx}'并给个例句。不要废话。",
        "lyric": f"提供一句TUYU歌曲《{ctx}》的日文歌词和中文翻译。格式严格为: 歌词|翻译 。",
        "cve": f"""你是一个没有感情的网安API接口。
严格按照此格式输出：评分|漏洞简述|修复建议。
绝不允许出现“好的”、“根据”、“作为专家”等任何解释性废话！如果没数据就输出 0.0|暂无详情|请人工核对。
内容:{ctx}"""
    }
    print(f"   [AI请求] 正在生成 {prompt_type} ...", end="", flush=True)
    try:
        res = client.chat.completions.create(model="deepseek-chat", messages=[{"role": "user", "content": prompts[prompt_type]}])
        print(" ✅")
        return res.choices[0].message.content.strip()
    except Exception as e:
        print(f" ❌(兜底数据)")
        fallbacks = {
            "word": "エクスプロイト",
            "desc": "利用漏洞进行攻击的代码或程序。",
            "lyric": "世界は美しくなんかない|世界才不是那么美丽",
            "cve": "9.8|核心组件远程代码执行漏洞|建议立即隔离复现环境"
        }
        return fallbacks.get(prompt_type, "")

def send_bark(title, content):
    if not BARK_KEY or BARK_KEY == "你的_BARK_KEY_在这里": return
    url = f"https://api.day.app/{BARK_KEY}/{title}/{content}?group=CyberIntel&icon=https://raw.githubusercontent.com/tuyu/assets/main/icon.png"
    try: requests.get(url, timeout=5)
    except: pass

def git_sync():
    if not GITHUB_TOKEN or GH_REPO == "ciisoda/你的仓库名": return
    try:
        os.chdir(BASE_DIR)
        subprocess.run(["git", "add", "."], check=True)
        msg = f"NAS Auto Sync: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        subprocess.run(["git", "commit", "-m", msg], check=True)
        remote_url = f"https://{GITHUB_TOKEN}@github.com/{GH_REPO}.git"
        print("   [Git] 正在推送到 GitHub... (可能需要几秒钟)")
        subprocess.run(["git", "push", remote_url, "main", "--force"], check=True)
    except Exception as e: print(f"Git Error: {e}")

# --- 执行流程 ---
print(f"[{datetime.now()}] 正在启动 2026 深度情报审计...")
chosen_song = random.choice(list(ASSETS.keys()))
mv_bg, cover = ASSETS[chosen_song][0], ASSETS[chosen_song][1]

word = clean(get_ai("word"))
desc = clean(get_ai("desc", word))
lyric_raw = get_ai("lyric", chosen_song)
parts = (re.split(r"[|\n｜]", lyric_raw) + ["どんなに努力しても", "无论怎么努力"])[:2]
l_parts = [chosen_song, parts[0], parts[1]]

def render_links(raw_text, color):
    out = ""
    for line in raw_text.split('\n'):
        if '|' in line:
            t, u = line.split('|', 1)
            out += f'<div style="margin-bottom:12px;">• {clean(t)} <a href="{u.strip()}" target="_blank" style="color:{color};font-size:10px;text-decoration:none;text-shadow:0 0 5px {color};">[LINK]</a></div>'
    return out if out else "<div>Data Syncing...</div>"

print("   [抓取] 正在获取黑客新闻源...")
market_html = render_links(get_real_rss("https://feeds.feedburner.com/TheHackersNews"), "var(--b)")
print("   [抓取] 正在获取日本 IT 新闻源...")
japan_html = render_links(get_real_rss("https://news.yahoo.co.jp/rss/categories/it.xml"), "var(--p)")

cve_html = ""
top_cve_name = "Unknown"  # 🌟 用于记忆判断的变量

try:
    headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
    print("   [抓取] 正在搜寻最新 CVE 仓库...")
    r = requests.get("https://api.github.com/search/repositories?q=CVE-2026+OR+CVE-2025&sort=updated", headers=headers, timeout=10)
    
    items = r.json().get("items", [])
    if items:
        top_cve_name = items[0]["full_name"]  # 记录最新的头条CVE名称
        
    for repo in items[:8]:
        ai_res = get_ai("cve", repo.get("description", ""))
        
        # 🛡️ 核心防御：防止 AI 废话撑爆你的 UI
        if "|" not in ai_res and "｜" not in ai_res:
            intel = ["N/A", "AI未返回标准格式", "建议点击SOURCE核对"]
        else:
            intel = (re.split(r"[|｜]", ai_res) + ["0.0", "分析中", "请交叉核对"])[:3]

        # 🛡️ 二次防御：切断超长分数
        sc_score = clean(intel[0])
        if len(sc_score) > 10:
            sc_score = "Err"

        is_poc = any(x in repo["full_name"].lower() for x in ["poc", "exploit", "bypass"])
        tag_style = "border: 1px solid #ff007f; color: #ff007f; box-shadow: 0 0 5px #ff007f;" if is_poc else ""
        
        cve_html += f'''
        <div class="cve-card">
            <div class="cve-top">
                <a class="cve-link" href="{repo["html_url"]}" target="_blank">{clean(repo["full_name"])}{" [WEAPONIZED]" if is_poc else ""}</a>
                <span class="cve-tag" style="{tag_style}">SC: {sc_score}</span>
            </div>
            <div class="cve-body" style="line-height:1.6; margin-top:5px; opacity:0.85;">{clean(intel[1])}</div>
            <div class="cve-hint">
                <a href="{repo["html_url"]}" target="_blank" style="color:inherit; text-decoration:none;">📡 SOURCE: {clean(repo["owner"]["login"])}</a> | 💡 {clean(intel[2])}
            </div>
        </div>'''
except: cve_html = "<p>External Feed Offline</p>"

# --- 严格还原的 HTML 模板 ---
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
        <div class="glass" style="flex:1;border-left:4px solid var(--b);"><span class="label">MARKET_RECON</span><div class="scroll" style="font-size:11.5px;line-height:1.7;color:#99f1ff;">{market_html}</div></div>
        <div class="glass" style="flex:1;border-left:4px solid var(--p);"><span class="label">JAPAN_FEED</span><div class="scroll" style="font-size:11.5px;line-height:1.7;">{japan_html}</div></div>
    </div>
    <div class="glass" style="display:flex;flex-direction:column;overflow:hidden;"><span class="label">CVE_MONITOR</span><div class="scroll">{cve_html}</div></div>
</div></body></html>'''

with open(os.path.join(BASE_DIR, "index.html"), "w", encoding="utf-8") as f:
    f.write(full_html)

git_sync()

# 🌟 智能防打扰：读取本地记忆文件
memory_file = os.path.join(BASE_DIR, ".last_cve_memory.txt")
last_cve = ""
if os.path.exists(memory_file):
    with open(memory_file, "r", encoding="utf-8") as f:
        last_cve = f.read().strip()

# 🌟 智能通知逻辑：只有第一条漏洞变了，才弹窗！
if top_cve_name != "Unknown" and top_cve_name != last_cve:
    send_bark("TUYU_CyberIntel", f"🚨 新情报更新: 发现 {clean(top_cve_name)}。当前歌曲:《{chosen_song}》")
    with open(memory_file, "w", encoding="utf-8") as f:
        f.write(top_cve_name)
else:
    print("   [通知] 情报无重大更新，已静默拦截 Bark 打扰。")

print("自动化流程圆满结束。")
