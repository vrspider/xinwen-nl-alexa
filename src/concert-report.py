"""
生成荷兰演出每周报告
支持多种 LLM: openai, gemini, minimax, groq
用法: python concert-report.py [llm] [model] [--voice VOICE]
示例: python concert-report.py groq --voice zh-CN-YunxiNeural
"""
import os
import sys
import re
import shutil
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

# 加载 .env.local
PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / ".env.local")


def get_week_dates() -> tuple:
    """获取本周的开始和结束日期
    
    Returns:
        (current_date, end_date) 格式 YYYY-MM-DD
    """
    today = datetime.now()
    current_date = today.strftime("%Y-%m-%d")
    end_date = (today + timedelta(days=7)).strftime("%Y-%m-%d")
    return current_date, end_date


def resolve_concert_urls(concerts: list) -> list:
    """解析演出场馆 URL，替换日期占位符
    
    Args:
        concerts: 演出场馆列表
        
    Returns:
        更新后的场馆列表
    """
    current_date, end_date = get_week_dates()
    
    for concert in concerts:
        url = concert.get("url", "")
        if "{current_date}" in url:
            url = url.replace("{current_date}", current_date)
        if "{end_date}" in url:
            url = url.replace("{end_date}", end_date)
        concert["url"] = url
    
    return concerts


def load_concerts_config() -> list:
    """加载演出场馆配置"""
    config_path = PROJECT_ROOT / "config" / "concerts.json"
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    concerts = config.get("concerts", [])
    # 解析 URL 中的日期占位符
    return resolve_concert_urls(concerts)


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


def generate_speech(text: str, output_path: str, voice: str = "zh-CN-XiaoxiaoNeural") -> str:
    """生成语音 MP3
    
    Args:
        text: 要转换的文本
        output_path: 输出文件路径
        voice: TTS 语音角色 (默认: zh-CN-XiaoxiaoNeural)
    
    Returns:
        生成的 MP3 文件路径
    """
    import asyncio
    import edge_tts
    
    async def generate():
        communicate = edge_tts.Communicate(text, voice=voice)
        await communicate.save(str(output_path))
    
    asyncio.run(generate())
    return str(output_path)


def generate_concert_weekly_audio(report_text: str, voice: str = "zh-CN-XiaoxiaoNeural"):
    """生成演出周报语音
    
    Args:
        report_text: 报告文本内容
        voice: TTS 语音角色 (默认: zh-CN-XiaoxiaoNeural)
    """
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
        # 尝试匹配日期范围
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
    intro = "欢迎收听荷兰演出周报。我是 XiaXia，为您播报。"
    full_text = intro + "\n\n" + clean_content
    
    # 输出文件名
    filename = f"concert-weekly-report-{date_str}.mp3"
    
    # 保存到 public/audio/concerts
    audio_dir = PROJECT_ROOT / "public" / "audio" / "concerts"
    audio_dir.mkdir(parents=True, exist_ok=True)
    output_path = audio_dir / filename
    
    print(f"\n🎙️  正在生成语音: {filename}")
    print(f"   文本长度: {len(full_text)} 字符")
    print(f"   使用语音: {voice}")
    
    generate_speech(full_text, output_path, voice)
    
    print(f"✅ 已生成: {output_path}")
    
    # 同时复制到 output 目录
    output_dir = PROJECT_ROOT / "output" / "concerts"
    output_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(str(output_path), output_dir / filename)
    print(f"   已复制到: {output_dir / filename}")


def get_weekly_concert_report(llm: str, model: str = None, voice: str = "zh-CN-YunxiNeural"):
    """生成每周演出报告"""
    # 加载演出场馆配置
    concerts = load_concerts_config()
    
    # 获取日期范围
    current_date, end_date = get_week_dates()
    print(f"📅 日期范围: {current_date} ~ {end_date}")
    
    # 获取当前周信息
    today = datetime.now()
    current_week = f"{today.year}年{today.month}月第{(today.day - 1) // 7 + 1}周"
    
    # 构建场馆列表信息（包含解析后的 URL）
    venues_info = "\n".join([
        f"- {c['name']} ({c['city']}): {c['url']}"
        for c in concerts
    ])
    
    # 构造 Prompt
    prompt = f"""
    以下是荷兰主要的演出场馆列表及其本周的演出页面 URL：
    
    {venues_info}
    
    请根据以上场馆的 URL，搜索或访问获取{current_week}期间的演出信息，生成一份荷兰演出活动的周报。
    
    输出格式：
    ## [演出名称] - [场馆名]
    - **城市**: 
    - **亮点**: (一句话描述为什么值得去看)
    - **日期**: 
    - **类型**: (音乐会/芭蕾/戏剧/流行音乐等)
    ---
    
    请使用中文。确保信息准确。
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
    output_file = PROJECT_ROOT / "public" / "concerts" / "concert_weekly.md"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(report_text)
    
    print(f"✅ 本周演出周报已生成: {output_file}")
    print("\n--- 报告内容 ---")
    print(report_text)
    
    # 生成语音 (使用指定的语音角色)
    generate_concert_weekly_audio(report_text, voice)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="生成荷兰演出每周报告")
    parser.add_argument("llm", choices=["openai", "gemini", "minimax", "groq"], help="LLM 类型")
    parser.add_argument("model", nargs="?", default=None, help="模型名称")
    parser.add_argument("--voice", dest="voice", default="zh-CN-YunxiNeural",
                       help="TTS 语音角色 (默认: zh-CN-YunxiNeural)")
    
    args = parser.parse_args()
    
    get_weekly_concert_report(args.llm, args.model, args.voice)
