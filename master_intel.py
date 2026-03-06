import os, requests, urllib.parse, re, math, time
from openai import OpenAI
from datetime import datetime

# ===== 1. 基础配置与硬核容错 =====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
API_KEY = os.getenv("DEEPSEEK_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")

# 离线兜底数据 (防止 API 崩溃)
OFFLINE_DATA = {
    "word": "脆弱性 (ぜいじゃくせい)",
    "desc": "指系统、网络或软件中存在的安全漏洞。\n例：この脆弱性は早急に修正が必要です。",
    "japan": "1. 日本IT行业高度关注网络安全。\n2. 留学签证政策保持稳定。\n3. 东京地区IT人才需求持续增加。",
    "lyric": ["くらべられっ子", "あの子になりたかった", "我曾想成为那个孩子"]
}

TUYU_ASSETS = {
    "くらべられっ子": {"bg": "mv_kurabe.png", "cover": "cover_kurabe.jpg"},
    "泥の分際で私だけの大切を奪おうだなんて": {"bg": "mv_doro.png", "cover": "cover_doro.jpg"},
    "終点へと向かう楽曲": {"bg": "mv_shuten.png", "cover": "cover_shuten.jpg"},
    "いつかオトナになれるといいね。": {"bg": "mv_otona.png", "cover": "cover_otona.jpg"},
    "過去に囚われている": {"bg": "mv_kako.png", "cover": "cover_kako.jpg"},
    "ロックな君とはお别れだ": {"bg": "mv_rock.png", "cover": "cover_rock.jpg"}
}

def clean(t): return re.sub(r'[#*`>\-：:]', '', str(t)).strip() if t else ""

# 模块化 AI 调用，带超时保护
def safe_ai_get(ptype, ctx="", default=""):
    prompts = {
        "word": "选个网安或TUYU歌词日语单词+假名。",
        "desc": f"解释'{ctx}'并给个短例句，换行分隔。",
        "japan": "三句总结日本IT/留学动态。",
        "lyric": f"格式：歌名 | 日语 | 中文。选一首：{list(TUYU_ASSETS.keys())}",
        "cve": f"评分|简述|建议。内容：{ctx}"
    }
    try:
        res = client.chat.completions.create(
            model="deepseek-chat", 
            messages=[{"role":"user","content":prompts[ptype]}],
            timeout=15
        )
        return res.choices[0].message.content.strip()
    except Exception as e:
        print(f"⚠️ AI 模块 [{ptype}] 异常: {e}")
        return default

# ===== 2. 核心数据调度 =====
print("🚀 执行 V37.0 工业级采集流...")

# 获取单词与描述 (解耦)
word_raw = safe_ai_get("word", default=OFFLINE_DATA["word"])
word = clean(word_raw)
desc = safe_ai_get("desc", word, default=OFFLINE_DATA["desc"])

# 获取新闻
japan = safe_ai_get("japan", default=OFFLINE_DATA["japan"])

# 获取歌词与资源匹配
lyric_raw = safe_ai_get("lyric", default=" | ".join(OFFLINE_DATA["lyric"]))
l_parts = (lyric_raw.split('|') + ["TUYU", "...", "..."])[:3]
song_title = clean(l_parts[0])

# 资源强锁定
mv_bg, cover = "mv_default.png", "cover_default.jpg"
for k, v in TUYU_ASSETS.items():
    if k in song_title:
        mv_bg, cover = v["bg"], v["cover"]
        break

# GitHub CVE 采集 (独立线程感逻辑)
cve_html = ""
try:
    headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
    r = requests.get("https://api.github.com/search/repositories?q=CVE-2026&sort=updated", headers=headers, timeout=10)
    items = r.json().get('items', [])[:5]
    if not items: cve_html = "<p style='opacity:0.5;'>暂无最新 CVE 动态</p>"
    for repo in items:
        intel_raw = safe_ai_get("cve", repo.get('description', 'No desc'), default="5.0|分析中|暂无建议")
        intel = (intel_raw.split('|') + ["5.0","分析中","检查"])[:3]
        cve_html += f"""
        <div class='cve-card'>
            <div style='display:flex;justify-content:space-between;align-items:center;'>
                <a class='cve-link' href='{repo['html_url']}' target='_blank'>{repo['full_name']}</a>
                <span class='badge'>{intel[0]}</span>
            </div>
            <p class='cve-sub'>{clean(intel[1])}</p>
            <p class='cve-adv'>💡 {clean(intel[2])}</p>
        </div>"""
except Exception as e:
    cve_html = f"<p style='color:#ff007f;'>GitHub API 调用受限 ({e})</p>"

# ===== 3. UI 极致对齐渲染 =====
html = f"""
<!DOCTYPE html><html><head><meta charset='utf-8'><meta http-equiv="refresh" content="600">
<style>
    :root {{ --pink: #ff007f; --blue: #00d4ff; }}
    body {{ 
        margin:0; padding:25px; background:#05050a; color:#fff; font-family: 'Segoe UI', system-ui, sans-serif;
        background: linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.5)), url('{mv_bg}') center/cover fixed no-repeat;
    }}
    .glass {{ 
        background: rgba(18, 18, 30, 0.75); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 20px; padding: 25px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.4);
    }}
    .top-section {{ display:flex; align-items:center; gap:25px; margin-bottom:25px; border: 1px solid rgba(255,0,127,0.3); }}
    .layout {{ display:grid; grid-template-columns: 1fr 1.7fr; gap:25px; height: 75vh; }}
    .left-panel {{ display:flex; flex-direction:column; gap:25px; }}
    .scroll-area {{ overflow-y:auto; scrollbar-width: none; }}
    .scroll-area::-webkit-scrollbar {{ display:none; }}
    
    .word-box {{ color:var(--blue); font-size:28px; font-weight:bold; margin-bottom:10px; }}
    .news-box {{ border-left: 5px solid var(--pink); background: rgba(255,0,127,0.08); margin-top:auto; }}
    
    .cve-card {{ margin-bottom:20px; padding-bottom:12px; border-bottom: 1px solid rgba(255,255,255,0.06); }}
    .cve-link {{ color:var(--pink); font-weight:bold; text-decoration:none; font-size:15px; }}
    .badge {{ background:var(--blue); color:#000; padding:2px 8px; border-radius:4px; font-size:11px; font-weight:bold; }}
    .cve-sub {{ font-size:13px; margin:8px 0; opacity:0.85; line-height:1.6; }}
    .cve-adv {{ color:var(--blue); font-size:12px; }}
    
    h3 {{ font-size:11px; color:var(--pink); letter-spacing:2px; text-transform:uppercase; margin:0 0 15px 0; }}
</style></head><body>
    <div class="glass top-section">
        <img src="{cover}" style="width:90px;height:90px;border-radius:15px;border:2px solid var(--pink);">
        <div>
            <div style="font-size:10px; color:var(--pink); letter-spacing:3px; font-weight:bold;">TUYU_STATION // STABLE_V37</div>
            <div style="font-size:26px; font-style:italic; margin:8px 0;">{clean(l_parts[1])}</div>
            <div style="font-size:14px; color:var(--pink);">{clean(l_parts[2])}</div>
        </div>
    </div>
    <div class="layout">
        <div class="left-panel">
            <div class="glass">
                <h3>Vocal Intel</h3>
                <div class="word-box">{word}</div>
                <div style="font-size:14px; line-height:1.7; white-space:pre-wrap;">{clean(desc)}</div>
            </div>
            <div class="glass news-box">
                <h3 style="margin-bottom:8px;">Japan Study Log</h3>
                <div style="font-size:13px; line-height:1.6;">{clean(japan)}</div>
            </div>
        </div>
        <div class="glass scroll-area">
            <h3>Threat Intelligence Feed</h3>
            {cve_html}
        </div>
    </div>
</body></html>
"""
with open(os.path.join(BASE_DIR, "index.html"), "w", encoding="utf-8") as f: f.write(html)
print("✅ V37.0 部署成功：所有模块已进入隔离容错模式。")
