import os
import requests
import urllib.parse
from openai import OpenAI
from datetime import datetime, date # 🚩 引入日期函数用于快照存档
from bs4 import BeautifulSoup

# ===== 1. 核心配置区 =====
API_KEY = os.getenv("DEEPSEEK_API_KEY")
BARK_KEY = os.getenv("BARK_KEY")
client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

# 🚩 TUYU 核心资产映射 (PNG背景 + JPG封面)
TUYU_SONGS = ["《くらべられっ子》", "《泥の分際で私だけの大切を奪おうだなんて》", "《終点へと向かう楽曲》", "《いつかオトナになれるといいね。》", "《過去に囚われている》", "《ロックな君とはお别れだ》"]
ASSET_MAPPING = {
    "くらべられっ子": {"bg": "mv_kurabe.png", "cover": "cover_kurabe.jpg"},
    "泥の分际で": {"bg": "mv_doro.png", "cover": "cover_doro.jpg"},
    "终点へと": {"bg": "mv_shuten.png", "cover": "cover_shuten.jpg"},
    "オトナになれると": {"bg": "mv_otona.png", "cover": "cover_otona.jpg"},
    "过去に囚われている": {"bg": "mv_kako.png", "cover": "cover_kako.jpg"},
    "ロックな君": {"bg": "mv_rock.png", "cover": "cover_rock.jpg"}
}

# ===== 2. 文本清洗与 AI 深度研判 =====
def clean_content(text):
    # 🚩 核心修复：强行移除所有 Markdown 符号，防止 UI 混乱
    for char in ['#', '*', '`', '>', '-', '1.', '2.', '3.']:
        text = text.replace(char, '')
    return text.strip()

def get_ai_intel(text, intel_type="cve"):
    prompts = {
        "cve": f"分析漏洞评分(0-10)|摘要|风险。禁止Markdown：{text}",
        "japan": f"简述日本留学/IT动态，3行内。禁止Markdown：{text}",
        "word": "选网安或音游日语词，回 单词+假名。",
        "desc": f"解释 '{text}' 并给出一个短例句。禁止Markdown。",
        "lyric": f"严格选一段歌词。格式：歌名 | 日语 | 中文。禁止多余文字：[{', '.join(TUYU_SONGS)}]"
    }
    try:
        res = client.chat.completions.create(model="deepseek-chat", messages=[{"role": "user", "content": prompts[intel_type]}], stream=False)
        return clean_content(res.choices[0].message.content)
    except: return "5.0 | 解析失败 | 链接失效"

# ===== 3. 多维抓取模块 =====
def sync_security():
    log("📡 深度扫描 GitHub Exploit...")
    results = []
    try:
        res = requests.get("https://api.github.com/search/repositories?q=CVE-2026+OR+Exploit&sort=updated", timeout=15).json()
        for repo in res.get('items', [])[:4]:
            raw = get_ai_intel(repo['description'] or "No desc", "cve")
            parts = (raw.split('|') + ["5.0", "分析失败", "未知"])[:3]
            results.append({"name": repo['full_name'], "url": repo['html_url'], "score": parts[0].strip(), "summary": parts[1].strip()})
    except: pass
    return results

# ===== 4. 主流程、快照存档与 UI 渲染 =====
def run():
    log("🏁 启动 V25.0 终极存档版流程...")
    word = get_ai_intel(None, "word")
    desc = get_ai_intel(word, "desc")
    lyric_raw = get_ai_intel(None, "lyric")
    
    parts = lyric_raw.split('|')
    song_name = parts[0].strip() if len(parts) > 0 else "TUYU"
    lyric_jp = parts[1].strip() if len(parts) > 1 else "解析失败"
    lyric_cn = parts[2].strip() if len(parts) > 2 else ""

    # 🚩 找回图片资源映射
    mv_bg = "mv_default.png"
    album_cover = "cover_default.jpg"
    for key, assets in ASSET_MAPPING.items():
        if key in song_name:
            mv_bg = assets["bg"]
            album_cover = assets["cover"]
            break

    security_data = sync_security()
    japan_intel = get_ai_intel("日本高度人才签证 IT 类别评分更新与 CS 专攻入试情报", "japan")
    
    sec_html = "".join([f"""
        <div class='item-card-p'>
            <div style='display:flex; justify-content:space-between; align-items:center;'>
                <a href='{s['url']}' target='_blank' style='font-size:14px; color:#ff007f;'>{s['name']}</a>
                <span class='score-tag' style='background:{"#ff4d4d" if float(s['score'].replace('评分',''))>8 else "#00d4ff"}'>{s['score']}</span>
            </div>
            <p class='summary-text'>{s['summary']}</p>
        </div>""" for s in security_data])

    html = f"""
    <html><head><meta charset='utf-8'><meta http-equiv="refresh" content="600">
    <style>
        body {{ 
            background-color: #05050a; color: #e1e1e6; font-family: 'Segoe UI', sans-serif; margin: 0; padding: 25px;
            /* 🚩 确保背景图片显示，不透明度 0.75 */
            background-image: linear-gradient(rgba(5, 5, 10, 0.75), rgba(5, 5, 10, 0.75)), url('{mv_bg}');
            background-size: cover; background-position: center; background-attachment: fixed;
        }}
        .score-tag {{ padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: bold; color: white; }}
        
        /* 歌词栏布局修复 */
        .lyric-box-v25 {{ 
            background: rgba(25, 25, 40, 0.6); backdrop-filter: blur(15px); border: 1px solid rgba(255, 0, 127, 0.4); 
            padding: 20px; border-radius: 15px; margin-bottom: 30px; display: flex; align-items: center; gap: 25px;
        }}
        .album-art {{ width: 115px; height: 115px; border-radius: 10px; object-fit: cover; flex-shrink: 0; border: 1px solid #444; }}
        
        .grid {{ display: grid; grid-template-columns: 1fr 1.6fr; gap: 25px; }}
        .section-box {{ background: rgba(10, 10, 20, 0.7); backdrop-filter: blur(12px); padding: 25px; border-radius: 15px; border: 1px solid rgba(255,255,255,0.06); }}
        
        /* 🚩 文本解压修复 */
        .desc-text {{ 
            font-size: 15px; line-height: 1.8; color: #d1d1d6; 
            margin-top: 15px; padding: 15px; background: rgba(255,255,255,0.03); border-radius: 8px;
        }}
        .japan-info {{ 
            margin-top: 20px; padding: 15px; border-top: 2px solid rgba(255, 0, 127, 0.3); 
            background: rgba(255, 0, 127, 0.05); font-size: 13px; line-height: 1.6;
        }}
        .summary-text {{ font-size: 13px; color: #aaa; margin-top: 8px; line-height: 1.5; }}
        h3 {{ color: #ff007f; font-size: 12px; text-transform: uppercase; letter-spacing: 2.5px; margin-bottom: 15px; }}
    </style></head><body>
        <div class="lyric-box-v25">
            <img src="{album_cover}" class="album-art">
            <div style="flex:1;">
                <span style="color:#ff007f; font-size:11px; font-weight:bold; letter-spacing:2px;">♫ TUYU_TERMINAL // V25.0</span>
                <p style="font-size:22px; font-style:italic; margin:10px 0; color:#fff;">{lyric_jp}</p>
                <p style="color:#ff007f; font-size:14px; margin:0;">{lyric_cn}</p>
            </div>
        </div>
        <div class="grid">
            <div class="section-box">
                <h3>Daily Vocabulary & Japan Study</h3>
                <div style="font-size:38px; color:#00d4ff; font-weight:bold;">{word}</div>
                <div class="desc-text">{desc}</div>
                <div class="japan-info">🎌 <b>Japan_Study_Log:</b><br>{japan_intel}</div>
            </div>
            <div class="section-box">
                <h3>Vulnerability_研判_SOC</h3>
                {sec_html}
            </div>
        </div>
        <footer style="margin-top:20px; font-size:10px; color:#444; text-align:center;">SNAPSHOT_DATE: {date.today()}</footer>
    </body></html>
    """
    # 🚩 核心逻辑：双向写入 (实时网页 + 历史快照)
    with open("index.html", "w", encoding="utf-8") as f: f.write(html)
    
    if not os.path.exists('history'): os.makedirs('history')
    snapshot_path = f"history/{date.today()}.html"
    with open(snapshot_path, "w", encoding="utf-8") as f: f.write(html)
    log(f"💾 网页快照已存档: {snapshot_path}")
    
    # 🚩 手机推送逻辑 (安全编码版)
    if BARK_KEY:
        try:
            safe_song = "".join(c for c in song_name if c.isalnum())[:12]
            title = urllib.parse.quote("终端数据同步成功")
            body = urllib.parse.quote(f"新歌: {safe_song}\n快照已存入 History")
            requests.get(f"https://api.day.app/{BARK_KEY}/{title}/{body}?group=TuyuIntel", timeout=12)
            log(f"🔔 推送成功: {song_name}")
        except: log("❌ 推送失败")

if __name__ == "__main__":
    run()
