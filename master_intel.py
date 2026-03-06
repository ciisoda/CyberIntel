import os
import requests
import re
from openai import OpenAI
from datetime import datetime
from html import escape

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

API_KEY = os.getenv("DEEPSEEK_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

client = OpenAI(
    api_key=API_KEY,
    base_url="https://api.deepseek.com",
    timeout=20.0
)

ASSETS = {
    "くらべられっ子": ["mv_kurabe.png", "cover_kurabe.jpg"],
    "泥の分際で私だけの大切を夺おうだなんて": ["mv_doro.png", "cover_doro.jpg"],
    "终点へと向かう楽曲": ["mv_shuten.png", "cover_shuten.jpg"],
    "いつかオトナになれるといいね。": ["mv_otona.png", "cover_otona.jpg"],
    "过去に囚われている": ["mv_kako.png", "cover_kako.jpg"],
    "ロックな君とはお别れだ": ["mv_rock.png", "cover_rock.jpg"]
}


# ========= 文本清理 =========

def clean(text):
    if not text:
        return ""
    text = str(text)
    text = re.sub(r'[#*`>\-「」]', '', text)
    text = escape(text)
    return text.strip().replace("\n", "<br>")


# ========= AI 调用 =========

def get_ai(prompt_type, ctx=""):
    prompts = {
        "word": "选一个网络安全或IT相关的日语词，并标注假名，只返回词。",
        "desc": f"解释'{ctx}'并给一个简单例句，换行分隔。",
        "japan": "用三句话总结最近日本IT或留学动态。",
        "lyric": f"格式：歌名 | 日语歌词 | 中文翻译。从这些歌选一首: {list(ASSETS.keys())}",
        "cve": f"格式：评分|漏洞简述|防御建议。内容: {ctx}"
    }

    try:
        res = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{
                "role": "user",
                "content": prompts[prompt_type]
            }]
        )

        return res.choices[0].message.content.strip()

    except Exception as e:
        print("AI ERROR:", e)
        return ""


# ========= 歌词模块 =========

lyric_raw = get_ai("lyric")

parts = re.split(r"[|\n]", lyric_raw.replace('｜', '|'))
l_parts = [p.strip() for p in parts if p.strip()]
l_parts = (l_parts + ["TUYU", "...", "..."])[:3]

mv_bg = "mv_default.png"
cover = "cover_default.jpg"

for k, v in ASSETS.items():
    if k in l_parts[0]:
        mv_bg = v[0]
        cover = v[1]
        break


# ========= 单词模块 =========

word = clean(get_ai("word"))
desc = clean(get_ai("desc", word))
japan = clean(get_ai("japan"))


# ========= CVE模块 =========

cve_html = ""

try:

    headers = {}

    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"

    url = "https://api.github.com/search/repositories?q=CVE-2026&sort=updated"

    r = requests.get(url, headers=headers, timeout=10)

    data = r.json()

    for repo in data.get("items", [])[:6]:

        desc_text = repo.get("description", "")

        intel_raw = get_ai("cve", desc_text)

        intel = (re.split(r"[|/]", intel_raw) + ["5.0", "分析中", "建议检查系统"])[:3]

        cve_html += f"""
        <div class="cve-card">
            <div class="cve-top">
                <a class="cve-link" href="{repo['html_url']}" target="_blank">
                    {clean(repo['full_name'])}
                </a>
                <span class="cve-score">
                    SCORE: {clean(intel[0])}
                </span>
            </div>

            <div class="cve-body">
                {clean(intel[1])}
            </div>

            <div class="cve-footer">
                💡 {clean(intel[2])}
            </div>
        </div>
        """

except Exception as e:

    print("CVE ERROR:", e)

    cve_html = "<p>Intelligence Stream Offline</p>"


# ========= HTML =========

full_html = f"""
<!DOCTYPE html>
<html>

<head>

<meta charset="utf-8">
<meta http-equiv="refresh" content="600">

<style>

* {{
box-sizing: border-box;
}}

:root {{
--p: #ff007f;
--b: #00d4ff;
--bg: rgba(15,15,25,0.9);
}}

body {{

margin:0;
padding:20px;

background:#05050a;
color:#fff;

font-family:Inter, -apple-system, sans-serif;

background:
linear-gradient(rgba(0,0,0,0.6),rgba(0,0,0,0.6)),
url('{mv_bg}') center/cover fixed no-repeat;

height:100vh;
overflow:hidden;

}}

.glass {{

background:var(--bg);

backdrop-filter:blur(20px);
-webkit-backdrop-filter:blur(20px);

border:1px solid rgba(255,255,255,0.08);

border-radius:12px;
padding:18px;

}}

.header {{

height:100px;
display:flex;
align-items:center;
gap:20px;
margin-bottom:20px;

}}

.header img {{

width:80px;
height:80px;

border-radius:10px;

border:1.5px solid var(--p);

}}

.song-box h1 {{

font-size:20px;
margin:0;

}}

.song-box p {{

font-size:13px;
color:var(--p);
margin:4px 0 0 0;
opacity:0.9;

}}

.container {{

display:grid;
grid-template-columns:1fr 1.8fr;
gap:20px;

height:calc(100vh - 160px);

}}

.col-left {{

display:flex;
flex-direction:column;
gap:20px;

}}

.scroll-box {{

flex:1;
overflow-y:auto;

}}

.cve-card {{

margin-bottom:20px;
padding-bottom:12px;
border-bottom:1px solid rgba(255,255,255,0.05);

}}

.cve-top {{

display:flex;
justify-content:space-between;
margin-bottom:6px;

}}

.cve-link {{

color:var(--p);
text-decoration:none;
font-weight:bold;

}}

.cve-score {{

font-size:10px;
color:var(--b);
font-weight:900;

}}

.cve-body {{

font-size:12px;
opacity:0.85;

}}

.cve-footer {{

font-size:11px;
color:var(--b);
font-style:italic;

}}

.label {{

font-size:9px;
letter-spacing:3px;
color:var(--p);
margin-bottom:10px;
display:block;

}}

</style>

</head>


<body>


<div class="glass header">

<img src="{cover}">

<div class="song-box">

<h1>{clean(l_parts[0])}</h1>

<p>{clean(l_parts[1])}</p>

<div style="font-size:11px;opacity:0.4;">
{clean(l_parts[2])}
</div>

</div>

</div>


<div class="container">

<div class="col-left">

<div class="glass">

<span class="label">VOCAL_INTEL</span>

<div style="font-size:24px;color:var(--b);font-weight:bold;">
{word}
</div>

<div class="scroll-box">
{desc}
</div>

</div>


<div class="glass">

<span class="label">JAPAN_FEED</span>

<div>
{japan}
</div>

</div>

</div>


<div class="glass">

<span class="label">CVE_THREAT_MONITOR</span>

<div class="scroll-box">

{cve_html}

</div>

</div>

</div>


</body>
</html>
"""


# ========= 写入文件 =========

output = os.path.join(BASE_DIR, "dashboard.html")

with open(output, "w", encoding="utf-8") as f:
    f.write(full_html)

print("Dashboard generated:", output)
