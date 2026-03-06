import os
import requests
import urllib.parse
import re
import math
import time
from openai import OpenAI
from datetime import datetime, date
from bs4 import BeautifulSoup
from functools import lru_cache

# ===== 1. 环境与路径加固 =====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
API_KEY = os.getenv("DEEPSEEK_API_KEY")
BARK_KEY = os.getenv("BARK_KEY")
client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")

GITHUB_HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "marble-soda-intel-v27-1"
}

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

# TUYU 核心资产字典 (强锁定)
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
    if not text: return ""
    prompts = {
        "cve": f"分析此漏洞评分(0-10)|摘要|建议。禁止Markdown：{text}",
        "japan": f"简述日本留学/IT动态，3行内。禁止Markdown：{text}",
        "word": "选网安或音游日语词，回 单词+假名。",
        "desc": f"解释词语 '{text}' 并给出一个短例句。禁止Markdown。",
        "lyric": f"严格选一段歌词。格式：歌名 | 日语 | 中文。禁止多余文字：{list(TUYU_ASSETS.keys())}"
    }
    try:
        res = client.chat.completions.create(model="deepseek-chat", messages=[{"role": "user", "content": prompts[intel_type]}], stream=False)
        content = res.choices[0].message.content.strip()
        # 语义安全过滤：只去 Markdown 符号，不动正文内容
        return re.sub(r"[#>*`\-]", "", content)
    except Exception as e:
        log(f"⚠️ AI 调用失败: {e}")
        return "5.0 | 解析超时 | 建议手动检查"

def sync_security():
    log("📡 研判 GitHub 武器库...")
    results = []
    try:
        url = "https://api.github.com/search/repositories?q=CVE-2026+OR+Exploit&sort=updated"
        res = requests.get(url, headers=GITHUB_HEADERS, timeout=15)
        if res.status_code != 200: return []
        
        for repo in res.json().get('items', [])[:4]:
            raw = get_ai_intel(repo['description'] or "No desc", "cve")
            parts = (raw.split('|') + ["5.0", "分析失败", "未知"])[:3]
            
            # 正则提取数字评分
            score_match = re.search(r"\d+(\.\d+)?", parts[0])
            score = float(score_match.group()) if score_match else 5.0
            score = min(score, 10.0)
            
            # 热度计算公式
            stars = repo.get('stargazers_count', 0)
            heat = score + math.log(stars + 1)
            
            results.append({
                "name": repo['full_name'], "url": repo['html_url'], 
                "score": score, "summary": parts[1].strip(), "heat": round(heat, 2)
            })
    except Exception as e:
        log(f"❌ 安全同步异常: {e}")
    return sorted(results, key=lambda x: x['heat'], reverse=True)

# ===== 3. UI 渲染与持久化 =====

def run():
    log("🏁 启动 V27.1 终极版...")
    word = get_ai_intel("Word", "word")
    desc = get_ai_intel(word, "desc")
    lyric_raw = get_ai_intel("Lyric", "lyric")
    
    parts = lyric_raw.split('|')
    song_name_raw = parts[0].strip() if len(parts) > 0 else "TUYU"
    
    # 图片资源路径逻辑
    mv_bg = "mv_default.png"
    album_cover = "cover_default.jpg"
    for key in TUYU_ASSETS:
        if key in song_name_raw:
            mv_bg = TUYU_ASSETS[key]["bg"]
            album_cover = TUYU_ASSETS[key]["cover"]
            break

    security_data = sync_security()
    japan_intel = get_ai_intel("日本IT动态", "japan")
    
    sec_html = "".join([f"""
        <div class='item-card-p'>
            <div style='display:flex; justify-content:space-between; align-items:center;'>
                <a href='{s['url']}' target='_blank' style='font-size:14px; color:#ff007f;'>{s['name']}</a>
                <span class='score-tag' style='background:{"#ff4d4d" if s['score']>8.5 else "#00d4ff"}'>
                    {s['score']} | 🔥 {s['heat']}
                </span>
            </div>
            <p class='summary-text'>{s['summary']}</p>
        </div>""" for s in security_data])

    html = f"""
    <html><head><meta charset='utf-8'><meta http-equiv="refresh" content="600">
    <style>
        body {{ 
            margin: 0; padding: 25px; background-color: #05050a; color: #e1e1e6; font-family: 'Segoe UI', sans-serif;
            background: linear-gradient(rgba(5,5,10,0.8), rgba(5,5,10,0.8)), url('{mv_bg}') center/cover fixed no-repeat;
        }}
        .score-tag {{ padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: bold; color: white; }}
        .lyric-box-final {{ 
            background: rgba(25, 25, 40, 0.7); backdrop-filter: blur(15px); border: 1px solid rgba(255, 0, 127, 0.4); 
            padding: 22px; border-radius: 15px; margin-bottom: 25px; display: flex; align-items: center; gap: 25px;
        }}
        .album-art {{ width: 110px; height: 110px; border-radius: 10px; object-fit: cover; border: 1px solid #444; flex-shrink: 0; }}
        .grid {{ display: grid; grid-template-columns: 1fr 1.6fr; gap: 25px; }}
        .section-box {{ background: rgba(10, 10, 20, 0.75); backdrop-filter: blur(12px); padding: 25px; border-radius: 15px; border: 1px solid rgba(255,255,255,0.08); height: fit-content; }}
        
        /* 🚩 核心修复：防止挤压，允许自然换行 */
        .desc-text {{ 
            font-size: 15px; line-height: 1.8; color: #d1d1d6; margin-top: 15px; 
            white-space: pre-wrap; background: rgba(255,255,255,0.03); padding: 15px; border-radius: 8px;
        }}
        .japan-card {{ 
            margin-top: 20px; padding: 15px; background: rgba(255, 0, 127, 0.08); 
            border-left: 3px solid #ff007f; border-radius: 4px; font-size: 13px; line-height: 1.6;
        }}
        .summary-text {{ font-size: 13px; color: #aaa; margin-top: 8px; line-height: 1.5; }}
        h3 {{ color: #ff007f; font-size: 11px; text-transform: uppercase; letter-spacing: 2.5px; margin-bottom: 15px; }}
    </style></head><body>
        <div class="lyric-box-final">
            <img src="{album_cover}" class="album-art">
            <div style="flex:1;">
                <span style="color:#ff007f; font-size:11px; letter-spacing:2px; font-weight:bold;">♫ TUYU_SYSTEM // V27.1</span>
                <p style="font-size:24px; font-style:italic; margin:10px 0; color:#fff;">{parts[1].strip() if len(parts)>1 else "..."}</p>
                <p style="color:#ff007f; font-size:14px; margin:0;">{parts[2].strip() if len(parts)>2 else "..."}</p>
            </div>
        </div>
        <div class="grid">
            <div class="section-box">
                <h3>Vocabulary & Japan_Study</h3>
                <div style="font-size:38px; color:#00d4ff; font-weight:bold;">{word}</div>
                <div class="desc-text">{desc}</div>
                <div class="japan-card">🎌 <b>Japan_Study_Log:</b><br>{japan_intel}</div>
            </div>
            <div class="section-box">
                <h3>🔥 High Heat Vulnerability</h3>
                {sec_html}
            </div>
        </div>
    </body></html>
    """
    # 写入主文件
    with open(os.path.join(BASE_DIR, "index.html"), "w", encoding="utf-8") as f: f.write(html)
    
    # 写入历史存档
    history_dir = os.path.join(BASE_DIR, "history")
    if not os.path.exists(history_dir): os.makedirs(history_dir)
    with open(os.path.join(history_dir, f"{date.today()}.html"), "w", encoding="utf-8") as f: f.write(html)
    log(f"💾 存档已生成: {date.today()}")

    # 智能化推送
    if BARK_KEY and security_data:
        try:
            top = security_data[0]
            title = urllib.parse.quote(f"🚨 高风险漏洞: {top['score']}")
            body = urllib.parse.quote(f"项目: {top['name']}\n热度: {top['heat']}\n今日词: {word[:10]}")
            requests.get(f"https://api.day.app/{BARK_KEY}/{title}/{body}?group=TuyuIntel", timeout=12)
            log("🔔 推送成功")
        except: pass

if __name__ == "__main__":
    run()
