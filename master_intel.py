import os, requests, re, time
from openai import OpenAI
from datetime import datetime

# ===== 1. 生产级环境配置 =====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
API_KEY = os.getenv("DEEPSEEK_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# 🚩 修正 5: 将 timeout 挂载在 client 初始化
client = OpenAI(
    api_key=API_KEY, 
    base_url="https://api.deepseek.com",
    timeout=20.0 
)

ASSETS = {
    "くらべられっ子": ["mv_kurabe.png", "cover_kurabe.jpg"],
    "泥の分際で私だけの大切を奪おうだなんて": ["mv_doro.png", "cover_doro.jpg"],
    "終点へと向かう楽曲": ["mv_shuten.png", "cover_shuten.jpg"],
    "いつかオトナになれるといいね。": ["mv_otona.png", "cover_otona.jpg"],
    "過去に囚われている": ["mv_kako.png", "cover_kako.jpg"],
    "ロックな君とはお别れだ": ["mv_rock.png", "cover_rock.jpg"]
}

# 🚩 修正 1 & 4: 增强型清洗，保留换行，过滤日文引号
def clean(t):
    if not t: return ""
    # 过滤 Markdown 符号及日文括号「」
    t = re.sub(r'[#"*`>\-：:「」]', '', str(t))
    # 🚩 修正 1: 将换行符转为 HTML 换行
    return t.strip().replace("\n", "<br>")

def get_ai(ptype, ctx=""):
    prompts = {
        "word": "选个网安或TUYU日语词+假名。直接回单词，别废话。",
        "desc": f"解释'{ctx}'并给个短例句，换行分隔。",
        "japan": "三句总结日本IT/留学动态。",
        "lyric": f"格式: 歌名 | 日语歌词 | 中文翻译。选一首: {list(ASSETS.keys())}",
        "cve": f"评分|简述|建议。内容: {ctx}"
    }
    try:
        res = client.chat.completions.create(model="deepseek-chat", messages=[{"role":"user","content":prompts[ptype]}])
        return res.choices[0].message.content.strip()
    except: return ""

# ===== 2. 数据流 (GPT 修正逻辑) =====
print("🛠️ 执行 V40.0 神谕版本数据流...")

# 🚩 修正 2: 稳定解析歌词 (支持 | 或 换行)
lyric_raw = get_ai("lyric")
parts = re.split(r"[|\n]", lyric_raw)
l_parts = [p.strip() for p in parts if p.strip()] # 过滤空字符串
l_parts = (l_parts + ["TUYU", "...", "..."])[:3]

song_name = l_parts[0]
mv_bg, cover = "mv_default.png", "cover_default.jpg"
for k, v in ASSETS.items():
    if k in song_name:
        mv_bg, cover = v[0], v[1]
        break

word = clean(get_ai("word"))
desc = clean(get_ai("desc", word))
japan = clean(get_ai("japan"))

# CVE 采集
cve_html = ""
try:
    headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
    r = requests.get("https://api.github.com/search/repositories?q=CVE-2026&sort=updated", headers=headers, timeout=10)
    for repo in r.json().get('items', [])[:5]:
        intel_raw = get_ai("cve", repo.get('description',''))
        intel = (re.split(r"[|]", intel_raw) + ["5.0","分析中","检查"])[:3]
        cve_html += f"""
        <div class="item">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <a class="link" href="{repo['html_url']}" target="_blank">{repo['full_name']}</a>
                <span class="tag">{clean(intel[0])}</span>
            </div>
            <p class="sub">{clean(intel[1])}</p>
            <p class="hint">💡 {clean(intel[2])}</p>
        </div>"""
except: cve_html = "<p>Feed Error</p>"

# ===== 3. HTML (视觉与对齐优化) =====
full_html = f"""
<!DOCTYPE html><html><head><meta charset="utf-8"><meta http-equiv="refresh" content="600">
<style>
    :root {{ --p: #ff007f; --b: #00d4ff; --g: rgba(15, 18, 25, 0.8); }}
    body {{ 
        margin:0; padding:25px; background:#05050a; color:#fff; font-family: 'Inter', sans-serif;
        background: linear-gradient(rgba(0,0,0,0.4), rgba(0,0,0,0.4)), url('{mv_bg}') center/cover fixed no-repeat;
    }}
    .glass {{ background:var(--g); backdrop-filter:blur(15px); border:1px solid rgba(255,255,255,0.1); border-radius:20px; padding:20px; }}
    
    /* 🚩 修正 3: 解决高度不一致与错位 */
    .header {{ display:flex; align-items:center; gap:25px; margin-bottom:20px; border-bottom:1px solid var(--p); }}
    .header img {{ width:90px; height:90px; border-radius:15px; border:1.5px solid var(--p); }}
    .song-box {{ 
        line-height:1.4; 
        word-break:break-word; 
    }}
    
    .grid {{ display:grid; grid-template-columns: 1fr 1.7fr; gap:20px; height: 75vh; }}
    .col {{ display:flex; flex-direction:column; gap:20px; }}
    .scroll {{ overflow-y:auto; }}
    
    .title {{ font-size:26px; color:var(--b); font-weight:bold; margin-bottom:10px; }}
    .news {{ border-left:4px solid var(--p); background:rgba(255,0,127,0.05); margin-top:auto; }}
    
    .item {{ margin-bottom:15px; padding-bottom:10px; border-bottom:1px solid rgba(255,255,255,0.05); }}
    .link {{ color:var(--p); font-weight:bold; text-decoration:none; font-size:15px; }}
    .tag {{ border:1px solid var(--b); color:var(--b); padding:1px 8px; border-radius:50px; font-size:11px; font-weight:bold; }}
    .sub {{ font-size:13.5px; margin:8px 0; opacity:0.85; line-height:1.6; }}
    .hint {{ font-size:12px; color:var(--b); }}
</style></head><body>
    <div class="glass header">
        <img src="{cover}">
        <div class="song-box">
            <div style="font-size:22px; font-weight:bold; margin-bottom:5px;">{clean(song_name)}</div>
            <div style="font-size:15px; color:var(--p); font-weight:500;">{clean(l_parts[1])}</div>
            <div style="font-size:12px; opacity:0.6;">{clean(l_parts[2])}</div>
        </div>
    </div>
    <div class="grid">
        <div class="col">
            <div class="glass">
                <div style="font-size:10px;color:var(--p);letter-spacing:2px;margin-bottom:10px;">VOCAL_INTEL</div>
                <div class="title">{word}</div>
                <div style="font-size:14.5px; line-height:1.7;">{desc}</div>
            </div>
            <div class="glass news">
                <div style="font-size:10px;color:var(--p);margin-bottom:8px;">JAPAN_STUDY_FEED</div>
                <div style="font-size:13px; line-height:1.6;">{japan}</div>
            </div>
        </div>
        <div class="glass scroll" style="padding:20px;">
            <div style="font-size:10px;color:var(--p);margin-bottom:15px;letter-spacing:2px;">THREAT_INTELLIGENCE</div>
            {cve_html}
        </div>
    </div>
</body></html>
"""
with open(os.path.join(BASE_DIR, "index.html"), "w", encoding="utf-8") as f: f.write(full_html)
print("✅ V40.0 封盘版已生成。逻辑与视觉完美闭环。")
