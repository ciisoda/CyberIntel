import os, requests, urllib.parse, re, math, time
from openai import OpenAI
from datetime import datetime

# ===== 1. 配置注入 =====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
API_KEY = os.getenv("DEEPSEEK_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")

# 资源映射表 (严禁修改 Key 名)
ASSETS = {
    "くらべられっ子": ["mv_kurabe.png", "cover_kurabe.jpg"],
    "泥の分際で私だけの大切を奪おうだなんて": ["mv_doro.png", "cover_doro.jpg"],
    "終点へと向かう楽曲": ["mv_shuten.png", "cover_shuten.jpg"],
    "いつかオトナになれるといいね。": ["mv_otona.png", "cover_otona.jpg"],
    "過去に囚われている": ["mv_kako.png", "cover_kako.jpg"],
    "ロックな君とはお别れだ": ["mv_rock.png", "cover_rock.jpg"]
}

def strict_clean(text):
    """最强清洗：确保 HTML 安全且无 Markdown 杂质"""
    if not text: return "N/A"
    text = re.sub(r'[#*`>\-\[\]]', '', str(text)) # 删掉所有 Markdown 符号
    text = text.replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
    return text.strip()

def fetch_ai(ptype, context=""):
    """带重试机制的 AI 获取"""
    prompts = {
        "word": "回一个网安或TUYU歌词日语词+假名。直接回词，别废话。",
        "desc": f"解释'{context}'并给个短例句，用<br>换行。",
        "japan": "三句总结日本IT/留学/签证动态。",
        "lyric": f"格式: 歌名 | 日语 | 中文。备选: {list(ASSETS.keys())}",
        "cve": f"评分|简述|建议。内容: {context}"
    }
    for _ in range(2): # 失败重试一次
        try:
            res = client.chat.completions.create(
                model="deepseek-chat", 
                messages=[{"role":"user","content":prompts[ptype]}],
                timeout=20
            )
            return res.choices[0].message.content.strip()
        except: time.sleep(1)
    return "Service Unavailable | 暂无动态 | 检查网络"

# ===== 2. 数据流执行 =====
print("🛡️ V39.0 稳健逻辑启动...")

# 1. 抓取歌词与背景匹配
lyric_raw = fetch_ai("lyric")
l_parts = (lyric_raw.split('|') + ["TUYU", "...", "..."])[:3]
song_name = strict_clean(l_parts[0])

mv_bg, cover = "mv_default.png", "cover_default.jpg"
for k, v in ASSETS.items():
    if k in song_name:
        mv_bg, cover = v[0], v[1]
        break

# 2. 抓取单词与描述
word = strict_clean(fetch_ai("word"))
desc = fetch_ai("desc", word) # 这里不 clean，因为保留了 <br>

# 3. 抓取日本动态
japan = fetch_ai("japan")

# 4. 抓取 CVE (带 API 频率限制保护)
cve_list_html = ""
try:
    h = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
    r = requests.get("https://api.github.com/search/repositories?q=CVE-2026&sort=updated", headers=h, timeout=10)
    repos = r.json().get('items', [])[:5]
    for repo in repos:
        intel = (fetch_ai("cve", repo.get('description','')).split('|') + ["5.0","分析中","检查"])[:3]
        cve_list_html += f"""
        <div class="cve-card">
            <div class="cve-header">
                <a class="cve-link" href="{repo['html_url']}" target="_blank">{repo['full_name']}</a>
                <span class="capsule">{strict_clean(intel[0])}</span>
            </div>
            <p class="cve-text">{strict_clean(intel[1])}</p>
            <p class="cve-hint">💡 {strict_clean(intel[2])}</p>
        </div>"""
except Exception as e:
    cve_list_html = f"<p style='color:var(--pink)'>GitHub Feed Offline: {e}</p>"

# ===== 3. HTML 声明式渲染 =====
full_html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="refresh" content="600">
    <style>
        :root {{
            --pink: #ff007f;
            --blue: #00d4ff;
            --glass: rgba(15, 15, 25, 0.78);
            --border: rgba(255, 255, 255, 0.12);
        }}
        
        body {{
            margin: 0; padding: 30px;
            background: #05050a;
            background-image: linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.5)), url('{mv_bg}');
            background-size: cover; background-position: center; background-attachment: fixed;
            color: #f0f0f5; font-family: 'Inter', system-ui, -apple-system, sans-serif;
            overflow: hidden;
        }}

        .glass {{
            background: var(--glass);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid var(--border);
            border-radius: 24px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.5);
        }}

        /* 顶部版块：解决混乱的关键 */
        .header {{
            display: grid; grid-template-columns: 100px 1fr; gap: 25px;
            padding: 25px; margin-bottom: 25px; align-items: center;
            border-bottom: 2px solid var(--pink);
        }}
        .header img {{ width: 100px; height: 100px; border-radius: 16px; border: 1px solid var(--pink); object-fit: cover; }}
        .song-info h1 {{ font-size: 26px; margin: 0 0 8px 0; color: #fff; font-weight: 800; }}
        .song-info p {{ font-size: 15px; margin: 0; color: var(--pink); opacity: 0.9; font-weight: 500; }}

        .main-layout {{ display: grid; grid-template-columns: 1fr 1.8fr; gap: 25px; height: 72vh; }}
        .left-col {{ display: flex; flex-direction: column; gap: 25px; }}
        
        .section-title {{ font-size: 10px; color: var(--pink); letter-spacing: 3px; text-transform: uppercase; margin-bottom: 15px; opacity: 0.7; }}
        .word-display {{ font-size: 30px; color: var(--blue); font-weight: bold; margin-bottom: 12px; }}
        .scroll-v {{ overflow-y: auto; padding-right: 10px; }}
        .scroll-v::-webkit-scrollbar {{ width: 4px; }}
        .scroll-v::-webkit-scrollbar-thumb {{ background: rgba(255,255,255,0.15); border-radius: 10px; }}

        .news-panel {{ 
            margin-top: auto; padding: 20px; border-left: 4px solid var(--pink); 
            background: rgba(255, 0, 127, 0.08); border-radius: 0 16px 16px 0;
        }}

        /* 右侧 CVE 列表优化 */
        .cve-card {{ margin-bottom: 22px; padding-bottom: 15px; border-bottom: 1px solid rgba(255,255,255,0.06); }}
        .cve-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }}
        .cve-link {{ color: var(--pink); font-weight: bold; text-decoration: none; font-size: 15px; }}
        .capsule {{ border: 1px solid var(--blue); color: var(--blue); padding: 2px 10px; border-radius: 50px; font-size: 11px; font-weight: 800; }}
        .cve-text {{ font-size: 13.5px; line-height: 1.6; opacity: 0.85; margin: 0 0 6px 0; }}
        .cve-hint {{ font-size: 12px; color: var(--blue); font-style: italic; }}
    </style>
</head>
<body>
    <div class="glass header">
        <img src="{cover}" alt="Cover">
        <div class="song-info">
            <h1>{song_name}</h1>
            <p>{strict_clean(l_parts[1])}</p>
            <div style="font-size: 11px; opacity: 0.5; margin-top: 5px;">{strict_clean(l_parts[2])}</div>
        </div>
    </div>

    <div class="main-layout">
        <div class="left-col">
            <div class="glass" style="padding: 25px; flex: 1;">
                <div class="section-title">Vocal Intel</div>
                <div class="word-display">{word}</div>
                <div class="scroll-v" style="max-height: 220px; font-size: 14px; line-height: 1.8;">{desc}</div>
            </div>
            <div class="glass news-panel">
                <div class="section-title" style="opacity: 1;">Japan Study Feed</div>
                <div style="font-size: 13px; line-height: 1.7; opacity: 0.9;">{strict_clean(japan)}</div>
            </div>
        </div>

        <div class="glass scroll-v" style="padding: 25px;">
            <div class="section-title">Threat Intelligence Feed</div>
            {cve_list_html}
        </div>
    </div>
</body>
</html>
"""
with open(os.path.join(BASE_DIR, "index.html"), "w", encoding="utf-8") as f: f.write(full_html)
print(f"✅ V39.0 最终稳定版已在 {datetime.now().strftime('%H:%M:%S')} 部署。")
