"""
主程序 - 每日新闻语音生成
"""
from datetime import datetime
from pathlib import Path
import sys
import os
import json

# 添加当前目录到 path
sys.path.insert(0, str(Path(__file__).parent))

from scraper import fetch_news, format_news_for_speech, fetch_news_update_time
from tts import generate_speech_sync
from gdrive import upload_to_gdrive

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

def main():
    print(f"[{datetime.now()}] 开始生成新闻语音...")
    
    # 1. 抓取新闻 
    # compare the news update time with the last saved time to decide whether to proceed with generation and upload
    
    last_update_file = OUTPUT_DIR / "last_update.json"
    last_update_time = None
    if last_update_file.exists():
        with open(last_update_file, "r") as f:
            try:
                data = json.load(f)
                last_update_time = data.get("update_time")
            except json.JSONDecodeError:
                pass

    print("📰 抓取新闻...")
    news = fetch_news()
    news_update_t = fetch_news_update_time()
    print(f"   获取到 {len(news)} 条新闻 (更新时间: {news_update_t})")
    # save the news update time in a local json file for next comparison
    with open(last_update_file, "w") as f:
        json.dump({"update_time": news_update_t}, f, ensure_ascii=False, indent=2)
    
    # 2. 格式化文本
    print("✍️  格式化文本...")
    text = format_news_for_speech(news, max_items=len(news))
    print(f"   文本长度: {len(text)} 字符")
    
    # 3. 生成语音
    print("🎙️  生成语音...")
    # convert date like "2026年03月02日" to "2026-03-02" for filename
    date_str = news_update_t.replace("年", "-").replace("月", "-").replace("日", "")
    output_path = OUTPUT_DIR / f"{date_str}.mp3"
    mp3_path = generate_speech_sync(text, str(output_path))
    print(f"   已保存: {mp3_path}")
    # ensure we treat it as a Path for subsequent operations
    mp3_path = Path(mp3_path)

    
    
    # 4. 上传到 Google Drive
    # print("☁️  上传至 Google Drive...")
    # try:
    #     path = upload_to_gdrive(str(mp3_path))
    #     print(f"   已上传: {path}")
    # except Exception as e:
    #     print(f"   上传失败: {e}")
    
    # print(f"[{datetime.now()}] 完成!")

    # 5. copy mp3 to public/audio for Vercel hosting
    public_audio_dir = Path(__file__).parent / "public" / "audio"
    public_audio_dir.mkdir(parents=True, exist_ok=True)
    target_path = public_audio_dir / mp3_path.name
    target_path.write_bytes(mp3_path.read_bytes())
    print(f"   已复制到: {target_path}")

    # 6. deploy to Vercel (optional)
    # print("🚀 部署到 Vercel...")
    # uncomment the following line when you want to auto-deploy
    # don't deploy if there are no new items to avoid unnecessary redeployments
    if len(news) > 0:
        os.system("vercel --prod")  # this line is indented to run under the if


if __name__ == "__main__":
    main()
