import os
import requests
import re
import time
from openai import OpenAI
from datetime import datetime
from html import escape

# ========= 1. 环境初始化 =========
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
API_KEY = os.getenv("DEEPSEEK_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# 🚩 修正：Timeout 挂载在 Client
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

# ========= 2. 核心清洗逻辑 (GPT 修正加强版) =========
def clean(text):
    if not text:
        return ""
    text = str(text)
    # 过滤可能破坏布局的特殊 Markdown 符号
    text = re.sub(r'[#*`>\-「」]', '', text)
    # 🚩 转义 HTML 字符防止代码注入
    text = escape(text)
    # 🚩 修正 1：保留换行符并转为 HTML <br>
    return text.strip().replace("\n", "<br>")

def get_ai(prompt_type, ctx=""):
    prompts = {
        "word": "选一个网络安全相关的日语词，标注假名，只返回词。",
        "desc": f"简单解释'{ctx}'并给个例句，换行分隔。",
        "japan": "三句总结日本IT或留学动态。",
        "lyric": f"格式：歌名 | 日语歌词 | 中文翻译。选一首: {list(ASSETS.keys())}",
        "cve": f"评分|简述|建议。内容: {ctx}"
    }
    try:
        res = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompts[prompt_type]}]
        )
        return res.choices[0].message.content.strip()
    except Exception as e:
        print(f"AI ERROR ({prompt_type}):", e)
        return ""

# ========= 3. 数据处理 =========

# 🚩 修正 2：更稳健的歌词解析逻辑
lyric_raw = get_ai("lyric")
parts = re.split(r"[|\n｜]", lyric_raw) # 兼容中英文竖线及换行
l_parts = [p.strip() for p in parts if p.strip()]
l_parts = (l_parts + ["TUYU", "あの子になりたかった", "我曾想成为那个孩子"])[:3]

mv_bg, cover = "mv_default.png", "cover_default.jpg"
for k, v in ASSETS.items():
    if k in l_parts[0]:
        mv_bg, cover = v[0], v[1]
        break

word = clean(get_ai("word"))
desc = clean(get_ai("desc", word))
japan = clean(get_ai("japan"))

# CVE 模块 (加入频率控制)
cve_html = ""
try:
    headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
    url = "https://api.github.com/search/repositories?q=CVE-2026&sort=updated"
    r = requests.get(url, headers=headers, timeout=10)
    repos = r.json().get("items", [])[:6]
    
    for repo in repos:
        intel_raw = get_ai("cve", repo.get("description", ""))
        intel = (re.split(r"[|/]", intel_raw) + ["5.0", "分析中", "建议检查系统"])[:3]
        
        cve_html += f"""
        <div class="cve-card">
            <div class="cve-top">
                <a class="cve-link" href="{repo['html_url']}" target="_blank">{clean(repo['full_name'])}</a>
                <span class="cve-score">SCORE: {clean(intel[0])}</span>
            </div>
            <div class="cve-body">{clean(intel[1])}</div>
            <div class="cve-footer">💡 {clean(intel[2])}</div>
        </div>"""
except Exception as e:
    cve_html = f"<p style='color:var(--p)'>Intelligence Stream Offline: {e}</p>"

# ========= 4. 极致 HTML (解决溢出与“丑”的问题) =========

full_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta http-equiv="refresh" content="600">
    <style>
        * {{ box-sizing: border-box; }}
        :root {{ --p: #ff007f; --b: #00d4ff; --bg: rgba(15, 18, 25, 0.9); }}
        
        body {{
            margin: 0; padding: 25px;
            background: #05050a; color: #fff;
            font-family: 'Inter', -apple-system, sans-serif;
            background: linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), url('{mv_bg}') center/cover fixed no-repeat;
            height: 100vh; overflow: hidden;
        }}

        .glass {{
            background: var(--bg); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 16px; padding: 20px;
        }}

        /* 🚩 顶部修正：对齐不混乱 */
        .header {{ height: 100px; display: flex; align-items: center; gap: 20px; margin-bottom: 20px; }}
        .header img {{ width: 85px; height: 85px; border-radius: 12px; border: 1.5px solid var(--p); flex-shrink: 0; }}
        .song-box {{ line-height: 1.4; word-break: break-all; }}
        .song-box h1 {{ font-size: 22px; margin: 0; }}
        .song-box p {{ font-size: 14px; color: var(--p); margin: 5px 0 0 0; font-weight: 500; }}

        /* 🚩 栅格控制：彻底解决溢出 */
        .container {{ display: grid; grid-template-columns: 1fr 1.8fr; gap: 20px; height: calc(100vh - 165px); }}
        .col {{ display: flex; flex-direction: column; gap: 20px; height: 100%; }}
        
        /* 🚩 溢出关键修复 */
        .scroll-area {{ 
            flex: 1; overflow-y: auto; overflow-x: hidden; 
            scrollbar-width: none; -ms-overflow-style: none;
        }}
        .scroll-area::-webkit-scrollbar {{ display: none; }}

        .news-panel {{ border-left: 4px solid var(--p); background: rgba(255,0,127,0.05); margin-top: auto; }}
        
        /* 🚩 视觉降噪：更精致的 CVE 卡片 */
        .cve-card {{ margin-bottom: 20px; padding-bottom: 12px; border-bottom: 1px solid rgba(255,255,255,0.05); }}
        .cve-top {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }}
        .cve-link {{ color: var(--p); text-decoration: none; font-weight: bold; font-size: 15px; }}
        .cve-score {{ font-size: 10px; color: var(--b); font-weight: 900; letter-spacing: 1px; }}
        .cve-body {{ font-size: 13px; opacity: 0.85; line-height: 1.6; margin: 8px 0; }}
        .cve-footer {{ font-size: 11px; color: var(--b); font-style: italic; }}

        .label {{ font-size: 9px; letter-spacing: 3px; color: var(--p); margin-bottom: 10px; display: block; opacity: 0.7; }}
    </style>
</head>
<body>

<div class="glass header">
    <img src="{cover}">
    <div class="song-box">
        <h1>{clean(l_parts[0])}</h1>
        <p>{clean(l_parts[1])}</p>
        <div style="font-size: 11px; opacity: 0.4;">{clean(l_parts[2])}</div>
    </div>
</div>

<div class="container">
    <div class="col">
        <div class="glass" style="flex: 1.5; display: flex; flex-direction: column; overflow: hidden;">
            <span class="label">VOCAL_INTEL</span>
            <div style="font-size: 26px; color: var(--b); font-weight: bold; margin-bottom: 10px;">{word}</div>
            <div class="scroll-area">{desc}</div>
        </div>
        <div class="glass news-panel">
            <span class="label">JAPAN_FEED</span>
            <div style="font-size: 13px; line-height: 1.6;">{japan}</div>
        </div>
    </div>

    <div class="glass" style="display: flex; flex-direction: column; overflow: hidden;">
        <span class="label">CVE_THREAT_MONITOR</span>
        <div class="scroll-area">
            {cve_html}
        </div>
    </div>
</div>

</body>
</html>
"""

# ========= 5. 安全写入 (解决 SCP 报错) =========
output_path = os.path.join(BASE_DIR, "index.html")

try:
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(full_html)
    
    # 🚩 核心：物理确认文件存在且不为空，否则抛出异常终止 CI
    if os.path.getsize(output_path) > 0:
        print(f"SUCCESS: {output_path} generated ({os.path.getsize(output_path)} bytes)")
    else:
        raise Exception("Generated file is empty!")

except Exception as e:
    print(f"WRITE ERROR: {e}")
    exit(1) # 强制异常退出，阻止 SCP 运行
