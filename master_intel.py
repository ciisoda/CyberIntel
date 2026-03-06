import os
import requests
import urllib.parse
from openai import OpenAI
from datetime import datetime, date
from bs4 import BeautifulSoup

# ===== 1. 配置区 =====
API_KEY = os.getenv("DEEPSEEK_API_KEY")
BARK_KEY = os.getenv("BARK_KEY")
client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

# TUYU 曲库与 PNG 背景映射 (锁定核心资产)
TUYU_SONGS = ["《くらべられっ子》", "《泥の分際で私だけの大切を奪おうだなんて》", "《終点へと向かう楽曲》", "《いつかオトナになれるといいね。》", "《過去に囚われている》", "《ロックな君とはお别れだ》"]
ASSET_MAPPING = {"くらべられっ子": "mv_kurabe.png", "泥の分际で": "mv_doro.png", "终点へと": "mv_shuten.png", "オトナになれると": "mv_otona.png", "过去に囚われている": "mv_kako.png", "ロックな君": "mv_rock.png"}

# ===== 2. 深度过滤与 AI 解析 =====
def clean_text(text):
    # 🚩 核心修复：强行移除所有 Markdown 符号，防止 UI 混乱和推送报错
    for char in ['#', '*', '`', '>', '-']:
        text = text.replace(char, '')
    return text.strip()

def get_ai_intel(text, intel_type="cve"):
    prompts = {
        "cve": f"分析漏洞并返回格式：评分(0-10) | 摘要(40字内) | 风险点。禁止Markdown符号：{text}",
        "japan": f"简述日本留学或IT签证动态，3行以内。禁止Markdown：{text}",
        "word": "选网安或音游日语词，回 单词+假名。",
        "desc": f"解释词语 '{text}' 并给出一个简短例句。禁止Markdown。",
        "lyric": f"严格从曲库 [{', '.join(TUYU_SONGS)}] 选一段歌词。格式：歌名 | 日语 | 中文翻译。"
    }
    try:
        res = client.chat.completions.create(model="deepseek-chat", messages=[{"role": "user", "content": prompts[intel_type]}], stream=False)
        content = res.choices[0].message.content.strip()
        return clean_text(content)
    except: return "5.0 | 解析超时 | 暂时无法获取"

# ===== 3. 多维爬虫模块 =====
def get_japan_news():
    try:
        raw_news = "高度人才签证评分项增加；早稻田大学及东大 CS 专攻夏季入试时间公布。"
        return get_ai_intel(raw_news, "japan")
    except: return "暂无留学情报"

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

# ===== 4. 主流程与 UI 构建 =====
def run():
    log("🏁 启动 V22.0 纯净修复版...")
    word = get_ai_intel(None, "word")
    desc = get_ai_intel(word, "desc")
    lyric_raw = get_ai_intel(None, "lyric")
    
    parts = lyric_raw.split('|')
    song_name = parts[0].strip() if len(parts) > 0 else "TUYU"
    lyric_jp = parts[1].strip() if len(parts) > 1 else "解析失败"
    lyric_cn = parts[2].strip() if len(parts) > 2 else ""

    mv_bg = "mv_default.png"
    for key in ASSET_MAPPING:
        if key in song_name:
            mv_bg = ASSET_MAPPING[key]
            break

    security_data = sync_security()
    japan_intel = get_japan_news()
    
    sec_html = "".join([f"""
        <div class='item-card-p'>
            <div style='display:flex; justify-content:space-between;'>
                <a href='{s['url']}' target='_blank' style='font-size:14px; color:#ff007f;'>{s['name']}</a>
                <span class='score-tag' style='background:{"#ff4d4d" if float(s['score'])>8 else "#00d4ff"}'>{s['score']}</span>
            </div>
            <p class='summary-text'>{s['summary']}</p>
            <p style='font-size:11px; color:#666;'>⚠️ {s['risk']}</p>
        </div>""" for s in security_data])

    html = f"""
    <html><head><meta charset='utf-8'><meta http-equiv="refresh" content="600">
    <style>
        body {{ background-color: #05050a; color: #e1e1e6; font-family: 'Segoe UI', sans-serif; margin: 0; padding: 25px;
               background-image: linear-gradient(rgba(5, 5, 10, 0.78), rgba(5, 5, 10, 0.78)), url('{mv_bg}');
               background-size: cover; background-position: center; background-attachment: fixed; }}
        .score-tag {{ padding: 1px 6px; border-radius: 4px; font-size: 10px; font-weight: bold; color: white; }}
        .lyric-box {{ background: rgba(20, 20, 35, 0.65); backdrop-filter: blur(12px); border: 1px solid rgba(255, 0, 127, 0.3); padding: 20px; border-radius: 12px; margin-bottom: 25px; }}
        .grid {{ display: grid; grid-template-columns: 1fr 1.6fr; gap: 20px; }}
        .section-box {{ background: rgba(10, 10, 20, 0.7); backdrop-filter: blur(10px); padding: 25px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.06); height: fit-content; }}
        
        /* 🚩 核心修复：左侧文字间距与高度控制 */
        .desc-box {{ font-size: 14px; line-height: 1.8; color: #d1d1d6; margin-top: 15px; max-height: 300px; overflow-y: auto; }}
        .japan-card {{ margin-top: 15px; padding: 12px; background: rgba(255, 0, 127, 0.08); border-left: 3px solid #ff007f; font-size: 13px; line-height: 1.6; }}
        
        .summary-text {{ font-size: 13px; color: #aaa; margin: 5px 0; line-height: 1.4; }}
        h3 {{ color: #ff007f; font-size: 11px; text-transform: uppercase; letter-spacing: 2.5px; margin-bottom: 15px; border-bottom: 1px solid rgba(255,0,127,0.2); padding-bottom: 5px; }}
    </style></head><body>
        <h1 style="color:#ff007f; font-size:22px; margin-bottom:20px;">TUYU_INTEL_SOC // V22.0</h1>
        <div class="lyric-box">
            <span style="color:#ff007f; font-size:11px; letter-spacing:2px; font-weight:bold;">♫ NOW PLAYING: {song_name}</span>
            <p style="font-size:22px; font-style:italic; margin:10px 0; color:#fff;">{lyric_jp}</p>
            <p style="color:#ff007f; font-size:14px; margin:0; font-weight:300;">{lyric_cn}</p>
        </div>
        <div class="grid">
            <div class="section-box">
                <h3>Vocabulary & Study_Abroad</h3>
                <div style="font-size:38px; color:#00d4ff; font-weight:bold;">{word}</div>
                <div class="desc-box">{desc}</div>
                <div class="japan-card">🎌 <b>Japan_Study:</b><br>{japan_intel}</div>
            </div>
            <div class="section-box">
                <h3>Vulnerability_研判_Exploitability</h3>
                {sec_html}
            </div>
        </div>
    </body></html>
    """
    with open("index.html", "w", encoding="utf-8") as f: f.write(html)
    
    # 🚩 核心修复：推送环节彻底脱敏
    if BARK_KEY:
        try:
            # 只取前 15 个纯净字符，防止 URL 断裂
            safe_word = "".join(c for c in word if c.isalnum())[:15]
            title = urllib.parse.quote("终端数据已刷新")
            body = urllib.parse.quote(f"新词: {safe_word}\n歌名: {song_name[:12]}")
            requests.get(f"https://api.day.app/{BARK_KEY}/{title}/{body}?group=TuyuIntel&autoCopy=1", timeout=12)
            log(f"🔔 推送成功: {song_name}")
        except: log("❌ 推送链路异常")

if __name__ == "__main__":
    run()
