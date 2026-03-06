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

client = OpenAI(
    api_key=API_KEY,
    base_url="https://api.deepseek.com",
    timeout=25.0
)

# 确保这些文件名在你的服务器目录下真实存在
ASSETS = {
    "くらべられっ子": ["mv_kurabe.png", "cover_kurabe.jpg"],
    "泥の分際で私だけの大切を夺おうだなんて": ["mv_doro.png", "cover_doro.jpg"],
    "终点へと向かう楽曲": ["mv_shuten.png", "cover_shuten.jpg"],
    "いつかオトナになれるといいね。": ["mv_otona.png", "cover_otona.jpg"],
    "过去に囚われている": ["mv_kako.png", "cover_kako.jpg"],
    "ロックな君とはお别れだ": ["mv_rock.png", "cover_rock.jpg"]
}

def clean(text):
    if not text: return ""
    text = str(text)
    text = re.sub(r'[#*`>\-「」]', '', text)
    text = escape(text)
    return text.strip().replace("\n", "<br>")

def get_ai(prompt_type, ctx=""):
    prompts = {
        "word": "选一个网络安全相关的日语词，标注假名，只返回词。",
        "desc": f"简单解释'{ctx}'并给个例句，换行分隔。",
        "japan": "三句总结日本IT或留学动态。",
        "lyric": f"直接返回这一行格式，不要解释：歌名 | 日语歌词 | 中文翻译。选一首: {list(ASSETS.keys())}",
        "cve": f"评分|简述|建议。内容: {ctx}"
    }
    try:
        res = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompts[prompt_type]}]
        )
        return res.choices[0].message.content.strip()
    except Exception:
        return ""

# ========= 2. 歌词与背景逻辑加固 =========
lyric_raw = get_ai("lyric")
# 🚩 改进解析：兼容更多奇怪的分割符
parts = re.split(r"[|\n｜]", lyric_raw)
l_parts = [p.strip() for p in parts if p.strip()]

# 强制保底，防止 l_parts[0] 越界或为空
if len(l_parts) < 2:
    l_parts = ["くらべられっ子", "あの子になりたかった", "我曾想成为那个孩子"]

mv_bg = "mv_default.png"
cover = "cover_default.jpg"

# 🚩 修正背景匹配：只要包含关键词就锁定背景
for k, v in ASSETS.items():
    if k in l_parts[0] or l_parts[0] in k:
        mv_bg, cover = v[0], v[1]
        break

word = clean(get_ai("word"))
desc = clean(get_ai("desc", word))
japan = clean(get_ai("japan"))

# CVE 模块
cve_html = ""
try:
    headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
    url = "
