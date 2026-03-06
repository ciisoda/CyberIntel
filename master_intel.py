import os
import requests
import urllib.parse
import re
import math
from openai import OpenAI
from datetime import datetime, date
from bs4 import BeautifulSoup
from functools import lru_cache

# ===== 1. 环境初始化与路径加固 =====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
API_KEY = os.getenv("DEEPSEEK_API_KEY")
BARK_KEY = os.getenv("BARK_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN") # 🚩 建议在 GitHub Secrets 中添加
client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")

# 完善 Headers，降低 403 风险
GITHUB_HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "marble-soda-intel-v29",
    "Authorization": f"Bearer {GITHUB_TOKEN}" if GITHUB_TOKEN else None
}

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

# TUYU 核心资产映射 (锁定真货曲库)
TUYU_ASSETS = {
    "くらべられっ子": {"bg": "mv_kurabe.png", "cover": "cover_kurabe.jpg"},
    "泥の分際で私だけの大切を奪おうだなんて": {"bg": "mv_doro.png", "cover": "cover_doro.jpg"},
    "終点へと向かう楽曲": {"bg": "mv_shuten.png", "cover": "cover_shuten.jpg"},
    "いつかオトナになれるといいね。": {"bg": "mv_otona.png", "cover": "cover_otona.jpg"},
    "過去に囚われている": {"bg": "mv_kako.png", "cover": "cover_kako.jpg"},
    "ロックな君とはお别れだ": {"bg": "mv_rock.png", "cover": "cover_rock.jpg"}
}

# ===== 2. 逻辑加固模块 =====

@lru_cache(maxsize=128)
def get_ai_intel(text, intel_type="cve"):
    # 🚩 修复 1：防止空字符串递归失效，只过滤 None
    if text is None: return ""
    
    prompts = {
        "cve": f"分析漏洞返回：评分|研判总结(80字内)|风险建议。禁止Markdown：{text}",
        "japan": f"简述日本留学/IT动态(3行内)。禁止Markdown：{text}",
        "word": "选网安或音游日语词，回 单词+假名。",
        "desc": f"详细解释 '{text}' 并给出一个短例句。禁止Markdown。",
        "lyric": f"严格选一段歌词：歌名 | 日语 | 中文。禁止多余文字：{list(TUYU_ASSETS.keys())}"
    }
    try:
        res = client.chat.completions.create(model="deepseek-chat", messages=[{"role": "user", "content": prompts[intel_type]}], stream=False)
        content = res.choices[0].message.content.strip()
        # 🚩 修复 2：安全过滤，保留内容语义，只去 Markdown 符号
        return re.sub(r"[#>*`\-]", "", content)
    except Exception as e:
        log(f"⚠️ AI 调用异常: {e}")
        return "5.0 | 解析超时 | 建议手动检查日志"

def sync_security():
    log("📡 正在抓取 GitHub 武器库...")
    results = []
    try:
        url = "https://api.github.com/search/repositories?q=CVE-2026+OR+Exploit&sort=updated"
        res = requests.get(url, headers=GITHUB_HEADERS, timeout=15)
        if res.status_code != 200:
            log(f"❌ GitHub API 403/Limit: {res.status_code}")
            return []
        
        for repo in res.json().get('items', [])[:5]:
            raw = get_ai_intel(repo['description'] or "No description", "cve")
            # 🚩 修复 3：弹性解析，防止 split 炸裂
            parts = (raw.split('|') + ["5.0", "无内容", "无建议"])[:3]
            
            # 🚩 修复 4：更稳的评分解析与热度权重
            score_match = re.search(r"\d+(\.\d+)?", parts[0])
            score = float(score_match.group()) if score_match else 5.0
            score = min(score, 10.0)
            
            stars = repo.get('stargazers_count', 0)
            # 公式：Score + log(Stars + 1) * 0.6
            heat = round(score + math.log(stars + 1) * 0.6, 2)
            
            results.append({
                "name": repo['full_name'], "url": repo['html_url'], 
                "score": score, "summary": parts[1].strip(), "advice": parts[2].strip(), "heat": heat
            })
    except Exception as e:
        log(f"❌ 漏洞抓取环节崩溃: {e}")
    return sorted(results, key=lambda x: x['heat'], reverse=True)

# ===== 3. UI 渲染、快照存档与推送 =====

def run():
    log("🏁 启动 V29.0 指挥中心加固流程...")
    word = get_ai_intel("DailyWord", "word")
    desc = get_ai_intel(word, "desc")
    lyric_raw = get_ai_intel("RandomLyric", "lyric")
    
    # 🚩 修复 5：歌词解析加固
    lyric_parts = (lyric_raw.split('|') + ["TUYU", "...", "..."])[:3]
    song_name_raw = lyric_parts[0].strip()
    
    # 图片资源路径硬锁定
    mv_bg = "mv_default.png"
    album_cover = "cover_default.jpg"
    for key in TUYU_ASSETS:
        if key in song_name_raw:
            mv_bg = TUYU_ASSETS[key]["bg"]
            album_cover = TUYU_ASSETS[key]["cover"]
            break

    security_data = sync_security()
    japan_intel = get_ai_intel("日本IT及签证情报", "japan")
    
    sec_html = "".join([f"""
        <div class='item-card-p'>
            <div style='display:flex; justify-content:space-between; align-items:center;'>
                <a href='{s['url']}' target='_blank' class='cve-title'>{s['name']}</a>
                <span class='score-tag' style='background:{"#ff4d4d" if s['score']>8.5 else "#00d4ff"}'>
                    {s['score']} | 🔥 {s['heat']}
                </span>
            </div>
            <p class='summary-text'><b>研判：</b>{s['summary']}</p>
            <p class='advice-text'>💡 {s['advice']}</p>
        </div>""" for s in security_data])

    html = f"""
    <html><head><meta charset='utf-8'><meta http-equiv="refresh" content="600">
    <style>
        body {{ 
            margin: 0; padding: 25px; background-color: #05050a; color: #e1e1e6; font-family: 'Segoe UI', system-ui, sans-serif;
            background: linear-gradient(rgba(5,5,10,0.8), rgba(5,5,10,0.8)), url('{mv_bg}') center/cover fixed no-repeat;
        }}
        .score-tag {{ padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: bold; color: white; white-space: nowrap; }}
        .lyric-box {{ background: rgba(25, 25, 40, 0.7); backdrop-filter: blur(15px); border: 1px solid rgba(255, 0, 127, 0.4); 
                     padding: 22px; border-radius: 15px; margin-bottom: 25px; display: flex; align-items: center; gap: 25px; }}
        .album-art {{ width: 110px; height: 110px; border-radius: 10px; object-fit: cover; flex-shrink: 0; border: 1px solid #444; }}
        .grid {{ display: grid; grid-template-columns: 1fr 1.6fr; gap: 25px; }}
        .section-box {{ background: rgba(10, 10, 20, 0.75); backdrop-filter: blur(12px); padding: 25px; border-radius: 15px; border: 1px solid rgba(255,255,255,0.08); height: fit-content; }}
        .desc-text {{ font-size: 14px; line-height: 1.7; color: #d1d1d6; white-space: pre-wrap; background: rgba(255,255,255,0.04); padding: 15px; border-radius: 8px; }}
        .cve-title {{ font-size: 15px; color: #ff007f; font-weight: bold; text-decoration: none; }}
        .item-card-p {{ margin-bottom: 20px; padding-bottom: 15px; border-bottom: 1px solid rgba(255,255,255,0.05); }}
        .summary-text {{ font-size: 13px; color: #f0f0f5; margin-top: 8px; line-height: 1.5; opacity: 0.9; }}
        .advice-text {{ font-size: 12px; color: #00d4ff; margin-top: 5px; opacity: 0.8; font-style: italic; }}
        h3 {{ color: #ff007f; font-size: 11px; text-transform: uppercase; letter-spacing: 2.5px; margin-bottom: 15px; }}
        .japan-card {{ margin-top: 20px; padding: 15px; background: rgba(255, 0, 127, 0.08); border-left: 3px solid #ff007f; border-radius: 4px; font-size: 13px; }}
    </style></head><body>
        <div class="lyric-box">
            <img src="{album_cover}" class="album-art">
            <div style="flex:1;">
                <span style="color:#ff007f; font-size:11px; letter-spacing:2px;">♫ TUYU_SYSTEM // V29.0</span>
                <p style="font-size:24px; font-style:italic; margin:10px 0;">{lyric_parts[1].strip()}</p>
                <p style="color:#ff007f; font-size:14px; margin:0;">{lyric_parts[2].strip()}</p>
            </div>
        </div>
        <div class="grid">
            <div class="section-box">
                <h3>Vocabulary & Japan_Study</h3>
                <div style="font-size:28px; color:#00d4ff; font-weight:bold; margin-bottom:12px;">{word}</div>
                <div class="desc-text">{desc}</div>
                <div class="japan-card">🎌 <b>Japan_Study_Log:</b><br>{japan_intel}</div>
            </div>
            <div class="section-box">
                <h3>🔥 High Heat Vulnerability</h3>
                {sec_html}
            </div>
        </div>
        <footer style="margin-top:20px; font-size:10px; color:#444; text-align:center;">STATION: HUIZHOU_UNIVERSITY // SNAPSHOT: {date.today()}</footer>
    </body></html>
    """
    
    # 🚩 快照与存档：物理路径加固
    target_path = os.path.join(BASE_DIR, "index.html")
    with open(target_path, "w", encoding="utf-8") as f: f.write(html)
    
    history_dir = os.path.join(BASE_DIR, "history")
    if not os.path.exists(history_dir): os.makedirs(history_dir)
    with open(os.path.join(history_dir, f"{date.today()}.html"), "w", encoding="utf-8") as f: f.write(html)
    log(f"💾 存档与主页更新完成: {date.today()}")

    # 🚩 智能化推送：只推送热度最高的一个
    if BARK_KEY and security_data:
        try:
            top = security_data[0]
            title = urllib.parse.quote(f"🚨 高风险漏洞: {top['score']}")
            body = urllib.parse.quote(f"项目: {top['name']}\n热度: {top['heat']}\n研判: {top['summary'][:30]}...")
            requests.get(f"https://api.day.app/{BARK_KEY}/{title}/{body}?group=TuyuIntel", timeout=12)
            log(f"🔔 Bark 推送成功: {top['name']}")
        except Exception as e:
            log(f"❌ 推送失败: {e}")

if __name__ == "__main__":
    run()
