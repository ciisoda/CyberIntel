import os
import requests
import urllib.parse
from openai import OpenAI
from datetime import datetime, date
from bs4 import BeautifulSoup

# ===== 1. 核心配置 =====
API_KEY = os.getenv("DEEPSEEK_API_KEY")
BARK_KEY = os.getenv("BARK_KEY")
client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

# 🚩 核心资产库：必须确保文件名与 NAS 对应
TUYU_SONGS = ["《くらべられっ子》", "《泥の分際で私だけの大切を奪おうだなんて》", "《終点へと向かう楽曲》", "《いつかオトナになれるといいね。》", "《過去に囚われている》", "《ロックな君とはお别れだ》"]

ASSET_MAPPING = {
    "くらべられっ子": {"bg": "mv_kurabe.png", "cover": "cover_kurabe.jpg"},
    "泥の分际で": {"bg": "mv_doro.png", "cover": "cover_doro.jpg"},
    "终点へと": {"bg": "mv_shuten.png", "cover": "cover_shuten.jpg"},
    "オトナになれると": {"bg": "mv_otona.png", "cover": "cover_otona.jpg"},
    "过去に囚われている": {"bg": "mv_kako.png", "cover": "cover_kako.jpg"},
    "ロックな君": {"bg": "mv_rock.png", "cover": "cover_rock.jpg"}
}

# ===== 2. 强力清洗与 AI 解析 =====
def clean_text(text):
    for char in ['#', '*', '`', '>', '-', '1.', '2.', '3.']:
        text = text.replace(char, '')
    return text.strip()

def get_ai_intel(text, intel_type="cve"):
    prompts = {
        "cve": f"分析漏洞并返回格式：评分 | 摘要 | 风险点。禁止Markdown：{text}",
        "japan": f"简述日本留学/IT动态，3行内。禁止Markdown：{text}",
        "word": "选网安或音游日语词，回 单词+假名。",
        "desc": f"解释词语 '{text}' 并给出一个简短例句。禁止Markdown。",
        "lyric": f"严格选一段歌词。格式必须为：歌名 | 日语 | 中文。禁止任何额外文字：[{', '.join(TUYU_SONGS)}]"
    }
    try:
        res = client.chat.completions.create(model="deepseek-chat", messages=[{"role": "user", "content": prompts[intel_type]}], stream=False)
        content = clean_text(res.choices[0].message.content)
        return content
    except: return "未知 | 解析错误 | 离线"

# ===== 3. 爬虫模块 =====
def sync_security():
    results = []
    try:
        res = requests.get("https://api.github.com/search/repositories?q=CVE-2026+OR+Exploit&sort=updated", timeout=15).json()
        for repo in res.get('items', [])[:4]:
            raw_intel = get_ai_intel(repo['description'] or "No desc", "cve")
            parts = (raw_intel.split('|') + ["5.0", "分析失败", "未知"])[:3]
            results.append({"name": repo['full_name'], "url": repo['html_url'], "score": parts[0].strip(), "summary": parts[1].strip(), "risk": parts[2].strip()})
    except: pass
    return results

# ===== 4. 主流程与 UI 构建 (找回图片) =====
def run():
    log("🏁 启动 V23.0 极乐修复流程...")
    word = get_ai_intel(None, "word")
    desc = get_ai_intel(word, "desc")
    lyric_raw = get_ai_intel(None, "lyric")
    
    # 🚩 加固解析逻辑：确保图片映射正常
    parts = lyric_raw.split('|')
    song_name = parts[0].strip() if len(parts) > 0 else "TUYU"
    lyric_jp = parts[1].strip() if len(parts) > 1 else "解析失败"
    lyric_cn = parts[2].strip() if len(parts) > 2 else ""

    mv_bg = "mv_default.png"
    album_cover = "cover_default.jpg"
    for key, assets in ASSET_MAPPING.items():
        if key in song_name:
            mv_bg = assets["bg"]
            album_cover = assets["cover"]
            break

    security_data = sync_security()
    japan_intel = get_ai_intel("日本IT人才签证/SGU入试动态", "japan")
    
    sec_html = "".join([f"""
        <div class='item-card-p'>
            <div style='display:flex; justify-content:space-between;'>
                <a href='{s['url']}' target='_blank' style='font-size:14px; color:#ff007f;'>{s['name']}</a>
                <span class='score-tag' style='background:{"#ff4d4d" if float(s['score'].replace('评分',''))>8 else "#00d4ff"}'>{s['score']}</span>
            </div>
            <p class='summary-text'>{s['summary']}</p>
        </div>""" for s in security_data])

    html = f"""
    <html><head><meta charset='utf-8'><meta http-equiv="refresh" content="600">
    <style>
        body {{ background-color: #05050a; color: #e1e1e6; font-family: 'Segoe UI', sans-serif; margin: 0; padding: 25px;
               background-image: linear-gradient(rgba(5, 5, 10, 0.75), rgba(5, 5, 10, 0.75)), url('{mv_bg}');
               background-size: cover; background-position: center; background-attachment: fixed; }}
        .score-tag {{ padding: 1px 6px; border-radius: 4px; font-size: 10px; font-weight: bold; color: white; }}
        
        /* 🚩 找回封面框布局 */
        .lyric-box-new {{ 
            background: rgba(25, 25, 40, 0.65); backdrop-filter: blur(15px); border: 1px solid rgba(255, 0, 127, 0.4); 
            padding: 20px; border-radius: 15px; margin-bottom: 30px; display: flex; align-items: center; gap: 25px;
        }}
        .album-art {{ width: 110px; height: 110px; border-radius: 8px; object-fit: cover; flex-shrink: 0; border: 1px solid #444; }}
        
        .grid {{ display: grid; grid-template-columns: 1fr 1.6fr; gap: 25px; }}
        .section-box {{ background: rgba(10, 10, 20, 0.7); backdrop-filter: blur(10px); padding: 25px; border-radius: 15px; border: 1px solid rgba(255,255,255,0.06); height: fit-content; }}
        .desc-box {{ font-size: 14px; line-height: 1.8; color: #d1d1d6; margin-top: 15px; max-height: 350px; overflow-y: auto; }}
        .summary-text {{ font-size: 13px; color: #aaa; margin: 5px 0; line-height: 1.4; }}
        h3 {{ color: #ff007f; font-size: 11px; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 15px; border-bottom: 1px solid rgba(255,0,127,0.2); padding-bottom: 5px; }}
    </style></head><body>
        <div class="lyric-box-new">
            <img src="{album_cover}" class="album-art">
            <div style="flex:1;">
                <span style="color:#ff007f; font-size:11px; letter-spacing:2px; font-weight:bold;">♫ NOW PLAYING: {song_name}</span>
                <p style="font-size:22px; font-style:italic; margin:8px 0; color:#fff;">{lyric_jp}</p>
                <p style="color:#ff007f; font-size:14px; margin:0;">{lyric_cn}</p>
            </div>
        </div>
        <div class="grid">
            <div class="section-box">
                <h3>Vocabulary & Japan_Study</h3>
                <div style="font-size:38px; color:#00d4ff; font-weight:bold;">{word}</div>
                <div class="desc-box">{desc}<br><br><div style="padding:10px; background:rgba(255,0,127,0.1); border-radius:5px;">🎌 {japan_intel}</div></div>
            </div>
            <div class="section-box">
                <h3>CVE_Vulnerability_SOC</h3>
                {sec_html}
            </div>
        </div>
    </body></html>
    """
    with open("index.html", "w", encoding="utf-8") as f: f.write(html)
    
    # 推送逻辑
    if BARK_KEY:
        try:
            safe_word = "".join(c for c in word if c.isalnum())[:15]
            title = urllib.parse.quote("TUYU终端刷新成功")
            body = urllib.parse.quote(f"♫ {song_name[:12]}\n新词: {safe_word}")
            requests.get(f"https://api.day.app/{BARK_KEY}/{title}/{body}?group=TuyuIntel", timeout=12)
        except: log("❌ 推送失败")

if __name__ == "__main__":
    run()
