"""
语音合成模块 - 使用 edge-tts
"""
import asyncio
import edge_tts
from datetime import datetime
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

async def generate_speech(text: str, output_path: str = None) -> str:
    """生成语音 MP3"""
    if output_path is None:
        date_str = datetime.now().strftime("%Y-%m-%d")
        output_path = OUTPUT_DIR / f"{date_str}.mp3"
    
    # 使用中文女声
    communicate = edge_tts.Communicate(text, voice="zh-CN-XiaoxiaoNeural")
    await communicate.save(str(output_path))
    
    return str(output_path)

def generate_speech_sync(text: str, output_path: str = None) -> str:
    """同步版本的语音生成"""
    return asyncio.run(generate_speech(text, output_path))

if __name__ == "__main__":
    test_text = "欢迎收听今天的荷兰新闻精选。我是 XiaXia，为您播报。"
    output = generate_speech_sync(test_text)
    print(f"已生成: {output}")
