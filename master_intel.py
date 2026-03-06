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

# TUYU 曲库映射 (保持原有的 6 首经典及 PNG 背景逻辑)
TUYU_SONGS = ["《くらべられっ子》", "《泥の分際で私だけの大切を夺おうだなんて》", "《终点へと向かう楽曲》", "《いつかオトナになれるといいね。》", "《过去に囚われている》", "《ロックな君とはお别れだ》"]
ASSET_MAPPING = {"くらべられっ子": "mv_kurabe.png", "泥の分际で": "mv_doro.png", "终点へと": "mv_shuten.png", "オトナになれると": "mv_otona.png", "过去に囚われている": "mv_kako.png", "ロックな君": "mv_rock.png"}

# ===== 2. 增强型 AI 研判逻辑 =====
def get_ai_intel(text, intel_type="cve"):
    prompts = {
        # 🚩 核心升级：增加漏洞评分逻辑
        "cve": f"分析漏洞并返回格式：评分(0-10) | 总结(50字内) | 风险点。内容：{text}",
        # 🚩 新增：日本留学/IT职场分析
        "japan": f"总结日本IT留学或签证动态，给出对计算机专业学生的建议：{text}",
        "word": "选一个网络安全或音游相关的日语词，回单词+假名。",
        "desc": f"解释词语 '{text}' 并给出一个关于音游或网安的简短例句。",
        "lyric": f"从 [{', '.join(TUYU_SONGS)}] 选一段歌词。格式：歌名 | 日语 | 中文翻译。"
    }
    try:
        res = client.chat.completions.create(model="deepseek-chat", messages=[{"role": "user", "content": prompts[intel_type]}], stream=False)
        return res.choices[0].message.content.strip().replace("*", "")
    except: return "5.0 | 解析失败 | 无法获取建议"

# ===== 3. 多维爬虫模块 (新增日本资讯) =====
def get_japan_news():
    log("🎌 采集日本 IT/留学情报...")
    try:
        # 模拟抓取最新 IT 签证或 SGU 项目资讯
        raw_news = "日本高度人才签证 IT 类别评分标准更新；东京大学/早稻田大学 CS 专攻 2026 年度入试概要发布。"
        analysis = get_ai_intel(raw_news, "japan")
        return analysis
    except: return "暂无最新日本留学情报"

def sync_security():
    log("📡 深度研判 CVE 武器库...")
    results = []
    try:
        res = requests.get("https://api.github.com/search/repositories?q=CVE-2026+OR+Exploit&sort=updated", timeout=15).json()
        for repo in res.get('items', [])[:4]:
            raw_intel = get_ai_intel(repo['description'] or "No description", "cve")
            score, summary, risk = (raw_intel.split('|') + ["5.0", "无总结", "未知"])[:3]
            results.append({"name": repo['full_name'], "url": repo['html_url'], "score": score.strip(), "summary": summary.strip(), "risk": risk.strip()})
    except: pass
    return results

# ===== 4. 主流程与 UI 构建 =====
def run():
    log("🏁 启动 V21.0 东京幻像版同步流程...")
    word = get_ai_intel(None, "word")
    desc = get_ai_intel(word, "desc")
    lyric_raw = get_ai_intel(None, "lyric")
    
    parts = lyric_raw.split('|')
    song_name = parts[0].strip() if len(parts) > 0 else "TUYU"
    lyric_jp = parts[1].strip() if len(parts) > 1 else "加载失败"
    lyric_cn = parts[2].strip() if len(parts) > 2 else ""

    mv_bg = "mv_default.png"
    for key in ASSET_MAPPING:
        if key in song_name:
            mv_bg = ASSET_MAPPING[key]
            break

    security_data = sync_security()
    japan_intel = get_japan_news()
    
    # 构建安全卡片 HTML
    sec_html = "".join([f"""
        <div class='item-card-p'>
            <div style='display:flex; justify-content:space-between;'>
                <a href='{s['url']}' target='_blank' style='font-size:14px; color:#ff007f;'>{s['name']}</a>
                <span class='score-tag' style='background:{"#ff4d4d" if float(s['score'])>8 else "#00d4ff"}'>{s['score']}</span>
            </div>
            <p class='summary-text'>{s['summary']}</p>
            <p style='font-size:11px; color:#666; margin-top:5px;'>⚠️ Risk: {s['risk']}</p>
        </div>""" for s in security_data])

    html = f"""
    <html><head><meta charset='utf-8'><meta http-equiv="refresh" content="600">
    <style>
        body {{ background-color: #05050a; color: #e1e1e6; font-family: 'Inter', sans-serif; margin: 0; padding: 25px;
               background-image: linear-gradient(rgba(5, 5, 10, 0.75), rgba(5, 5, 10, 0.75)), url('{mv_bg}');
               background-size: cover; background-position: center; background-attachment: fixed; }}
        .score-tag {{ padding: 1px 6px; border-radius: 4px; font-size: 10px; font-weight: bold; color: white; }}
        .lyric-box {{ background: rgba(20, 20, 35, 0.6); backdrop-filter: blur(12px); border: 1px solid rgba(255, 0, 127, 0.3); padding: 20px; border-radius: 12px; margin-bottom: 25px; }}
        .grid {{ display: grid; grid-template-columns: 1fr 1.5fr; gap: 20px; }}
        .section-box {{ background: rgba(10, 10, 20, 0.65); backdrop-filter: blur(10px); padding: 20px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.05); }}
        .japan-card {{ margin-top: 15px; padding: 15px; background: rgba(255, 0, 127, 0.05); border-left: 3px solid #ff007f; font-size: 13px; line-height: 1.6; color: #f0f0f5; }}
        .summary-text {{ font-size: 13px; color: #aaa; margin: 5px 0; line-height: 1.4; }}
        h3 {{ color: #ff007f; font-size: 11px; text-transform: uppercase; letter-spacing: 2px; }}
    </style></head><body>
        <div class="lyric-box">
            <span style="color:#ff007f; font-size:11px; letter-spacing:2px;">♫ NOW PLAYING: {song_name}</span>
            <p style="font-size:20px; font-style:italic; margin:10px 0;">{lyric_jp}</p>
            <p style="color:#ff007f; font-size:14px; margin:0;">{lyric_cn}</p>
        </div>
        <div class="grid">
            <div class="section-box">
                <h3>Vocabulary & Study_Abroad</h3>
                <div style="font-size:38px; color:#00d4ff; font-weight:bold; margin:10px 0;">{word}</div>
                <p style="color:#d1d1d6; font-size:14px;">{desc}</p>
                <div class="japan-card">🎌 <b>Japan_Study_Log:</b><br>{japan_intel}</div>
            </div>
            <div class="section-box">
                <h3>CVE_Vulnerability_Scoring</h3>
                {sec_html}
            </div>
        </div>
        <footer style="margin-top:20px; font-size:10px; color:#444; text-align:center;">V21.0 // Tokyo_Fantasy_Edition</footer>
    </body></html>
    """
    with open("index.html", "w", encoding="utf-8") as f: f.write(html)
    log(f"✅ V21.0 部署完成: {song_name}")

if __name__ == "__main__":
    run()
