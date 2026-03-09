"""
生成荷兰博物馆每周报告
支持多种 LLM: openai, gemini, minimax, groq
支持多种搜索: googlesearch, serpapi
用法: python local-report.py [llm] [model] [--search PROVIDER]
示例: python local-report.py groq --search serpapi
       python local-report.py groq --search googlesearch
       python local-report.py gemini
"""
import os
import sys
import re
import shutil
import argparse
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# 加载 .env.local
PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / ".env.local")


def get_search_results_googlesearch(query: str) -> list:
    """使用 googlesearch 获取搜索结果"""
    try:
        from googlesearch import search
    except ImportError:
        print("googlesearch-python not installed")
        return []
    
    results = []
    print(f"🔍 Google 搜索: {query}")
    for j in search(query, num_results=5, sleep_interval=2):
        results.append(j)
        print(f"   - {j}")
    return results


def get_search_results_serpapi(query: str) -> list:
    """使用 SerpAPI 获取搜索结果"""
    try:
        from serpapi import Client
    except ImportError:
        print("serpapi not installed")
        return []
    
    api_key = os.environ.get("SerpAPI_KEY")
    if not api_key:
        print("错误: 未找到 SerpAPI_KEY")
        return []
    
    print(f"🔍 SerpAPI 搜索: {query}")
    
    client = Client(api_key=api_key)
    result = client.search({"q": query, "num": 10})
    
    search_results = []
    if "organic_results" in result:
        for item in result["organic_results"][:5]:
            if "link" in item:
                search_results.append(item["link"])
                title = item.get("title", item["link"])
                print(f"   - {title}")
    
    return search_results


def get_search_results(query: str, provider: str = "googlesearch") -> list:
    """根据 provider 获取搜索结果"""
    if provider == "serpapi":
        return get_search_results_serpapi(query)
    else:
        return get_search_results_googlesearch(query)


def generate_with_openai(prompt: str, model: str = "gpt-4o-mini") -> str:
    """使用 OpenAI 生成内容"""
    from openai import OpenAI
    
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("错误: 未找到 OPENAI_API_KEY")
        sys.exit(1)
    
    client = OpenAI(api_key=api_key)
    print(f"🤖 使用 OpenAI ({model})...")
    
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content


def generate_with_gemini(prompt: str, model: str = "gemini-2.0-flash") -> str:
    """使用 Gemini 生成内容"""
    from google import genai
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("错误: 未找到 GEMINI_API_KEY")
        sys.exit(1)
    
    client = genai.Client(api_key=api_key)
    print(f"🤖 使用 Gemini ({model})...")
    
    response = client.models.generate_content(
        model=model,
        contents=prompt
    )
    return response.text


def generate_with_minimax(prompt: str, model: str = "MiniMax-Text-01") -> str:
    """使用 Minimax 生成内容"""
    import requests
    
    api_key = os.environ.get("MINIMAX_API_KEY")
    if not api_key:
        print("错误: 未找到 MINIMAX_API_KEY")
        sys.exit(1)
    
    print(f"🤖 使用 Minimax ({model})...")
    
    url = "https://api.minimax.chat/v1/text/chatcompletion_pro"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": "你是一个有用的助手。"},
            {"role": "user", "content": prompt}
        ]
    }
    
    response = requests.post(url, headers=headers, json=data, timeout=60)
    result = response.json()
    
    if "choices" in result:
        return result["choices"][0]["message"]["content"]
    else:
        print(f"错误: {result}")
        sys.exit(1)


def generate_with_groq(prompt: str, model: str = "llama-3.1-8b-instant") -> str:
    """使用 Groq 生成内容"""
    from groq import Groq
    
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("错误: 未找到 GROQ_API_KEY")
        sys.exit(1)
    
    client = Groq(api_key=api_key)
    print(f"🤖 使用 Groq ({model})...")
    
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content


def clean_text_for_speech(text: str) -> str:
    """清理文本，移除 markdown 特殊字符，转换为语音友好格式"""
    # 移除 # ## 等标题标记（保留标题文字）
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
    
    # 移除 ** 粗体标记（保留文字）
    text = re.sub(r'\*\*', '', text)
    
    # 移除 * 斜体/列表标记
    text = re.sub(r'(?<=[^\n])\*(?=[^\n])', '', text)  # 行内 * 
    text = re.sub(r'^\s*\*\s+', '', text, flags=re.MULTILINE)  # 列表 * 
    text = re.sub(r'^\s*-\s+', '', text, flags=re.MULTILINE)  # 列表 - 
    
    # 移除多余空白
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()


def generate_museum_weekly_audio(report_text: str):
    """生成博物馆周报语音"""
    import asyncio
    import edge_tts
    
    # 从内容中提取日期
    date_match = re.search(r'(\d{1,2})月(\d{1,2})日', report_text)
    if date_match:
        month = date_match.group(1)
        day = date_match.group(2)
        # 尝试获取年份
        year_match = re.search(r'(\d{4})年', report_text)
        year = year_match.group(1) if year_match else str(datetime.now().year)
        date_str = f"{year}-{month}-{day}"
    else:
        # 尝试匹配日期范围 "2026年3月8日至"
        range_match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日至', report_text)
        if range_match:
            year = range_match.group(1)
            month = range_match.group(2)
            day = range_match.group(3)
            date_str = f"{year}-{month}-{day}"
        else:
            now = datetime.now()
            date_str = f"{now.year}-{now.month}-{now.day}"
    
    # 清理文本用于语音
    clean_content = clean_text_for_speech(report_text)
    
    # 添加开头语
    intro = "欢迎收听荷兰博物馆周报。我是 XiaXia，为您播报。"
    full_text = intro + "\n\n" + clean_content
    
    # 输出文件名
    filename = f"museum-weekly-report-{date_str}.mp3"
    
    # 保存到 public/audio/exhibitions
    audio_dir = PROJECT_ROOT / "public" / "audio" / "exhibitions"
    audio_dir.mkdir(parents=True, exist_ok=True)
    output_path = audio_dir / filename
    
    print(f"\n🎙️  正在生成语音: {filename}")
    print(f"   文本长度: {len(full_text)} 字符")
    
    async def generate():
        communicate = edge_tts.Communicate(full_text, voice="zh-CN-XiaoxiaoNeural")
        await communicate.save(str(output_path))
    
    asyncio.run(generate())
    
    print(f"✅ 已生成: {output_path}")
    
    # 同时复制到 output 目录
    output_dir = PROJECT_ROOT / "output" / "exhibitions"
    output_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(str(output_path), output_dir / filename)
    print(f"   已复制到: {output_dir / filename}")


def get_weekly_museum_report(llm: str, model: str = None, search_provider: str = "googlesearch"):
    from pathlib import Path
    
    # 检查 exhibitions-light.md 是否存在
    exhibitions_md_path = PROJECT_ROOT / "output" / "exhibitions" / "exhibitions-light.md"
    if exhibitions_md_path.exists():
        print(f"📄 读取现有展览信息: {exhibitions_md_path}")
        with open(exhibitions_md_path, "r", encoding="utf-8") as f:
            exhibitions_content = f.read()
    else:
        # 如果不存在，爬取并生成轻量版
        print("📄 exhibitions-light.md 不存在，正在生成...")
        from exhibition_scraper import save_light_exhibitions_markdown
        save_light_exhibitions_markdown()
        with open(exhibitions_md_path, "r", encoding="utf-8") as f:
            exhibitions_content = f.read()

    # 搜索本周荷兰展览信息 (可选)
    # query = "exhibitions Netherlands 2026 this month"
    # search_results = get_search_results(query, search_provider)

    # 获取当前周信息
    today = datetime.now()
    current_week = f"{today.year}年{today.month}月第{(today.day - 1) // 7 + 1}周"
    
    # 构造 Prompt
    prompt = f"""
    以下是荷兰各大博物馆的最新展览信息：
    
    {exhibitions_content}

    如果有明确的展览起止日期，请显示出来；如果没有，请根据 Now on、Coming soon、End date 等关键词判断展览是否在本周内正在展出。
    
    --- 
    
    请根据以上展览信息，生成一份关于{current_week}荷兰展览的周报。

    输出要求：
    核实展览的起止日期，确保本周未依然可看。
    简述展览主题和亮点，突出为什么值得去看。
    如果信息来自特定新闻稿或网页，请注明来源。
    严禁根据历史记忆虚构展览名称

    整理出本周最值得看的展览。
    
    输出格式：
    ## [展览名称] - [博物馆名]
    - **城市**: 
    - **亮点**: (一句话描述为什么值得去)
    - **日期**: (展出起止时间)
    ---
    请使用中文。
    """

    # 根据 LLM 类型调用
    if llm == "openai":
        model = model or "gpt-4o-mini"
        report_text = generate_with_openai(prompt, model)
    elif llm == "gemini":
        model = model or "gemini-2.5-flash"
        report_text = generate_with_gemini(prompt, model)
    elif llm == "minimax":
        model = model or "MiniMax-Text-01"
        report_text = generate_with_minimax(prompt, model)
    elif llm == "groq":
        model = model or "llama-3.1-8b-instant"
        report_text = generate_with_groq(prompt, model)
    else:
        print(f"未知 LLM 类型: {llm}")
        sys.exit(1)
    
    # 保存到文件
    output_file = PROJECT_ROOT / "public" / "exhibitions" / "museum_weekly.md"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(report_text)
    
    print(f"✅ 本周博物馆周报已生成: {output_file}")
    print("\n--- 报告内容 ---")
    print(report_text)
    
    # 生成语音
    generate_museum_weekly_audio(report_text)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="生成荷兰博物馆每周报告")
    parser.add_argument("llm", choices=["openai", "gemini", "minimax", "groq"], help="LLM 类型")
    parser.add_argument("model", nargs="?", default=None, help="模型名称")
    parser.add_argument("--search", dest="search", default="googlesearch", 
                       choices=["googlesearch", "serpapi"], help="搜索 provider")
    
    args = parser.parse_args()
    
    get_weekly_museum_report(args.llm, args.model, args.search)
