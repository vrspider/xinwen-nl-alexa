"""
主程序 - 每日新闻语音生成 (支持多站点配置)
"""
from datetime import datetime
from pathlib import Path
import sys
import os
import json
import shutil

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# 添加 src 目录到 path
sys.path.insert(0, str(Path(__file__).parent))

from scraper import fetch_news, format_news_for_speech, fetch_news_update_time
from tts import generate_speech_sync
from gdrive import upload_to_gdrive

CONFIG_FILE = PROJECT_ROOT / "sites.json"
OUTPUT_DIR = PROJECT_ROOT / "output"
PUBLIC_DIR = PROJECT_ROOT / "public"


def load_config() -> dict:
    """加载站点配置"""
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def process_site(site: dict, last_update_data: dict) -> bool:
    """处理单个站点的新闻生成"""
    site_id = site["id"]
    site_name = site["name"]
    output_dir_name = site.get("outputDir", site_id)
    public_dir_name = site.get("publicDir", site_id)
    
    print(f"\n{'='*50}")
    print(f"📰 处理站点: {site_name}")
    print(f"{'='*50}")
    
    # 1. 抓取新闻
    print("🔍 抓取新闻...")
    news = fetch_news(site)
    news_update_t = fetch_news_update_time(site)
    print(f"   获取到 {len(news)} 条新闻 (更新时间: {news_update_t})")
    
    # 检查是否需要更新
    last_time = last_update_data.get(site_id, {}).get("update_time")
    if last_time == news_update_t and len(news) > 0:
        print(f"   ⏭️  新闻未更新，跳过生成")
        return False
    
    # 保存更新时间
    last_update_data[site_id] = {"update_time": news_update_t}
    
    if len(news) == 0:
        print(f"   ⚠️  没有获取到新闻")
        return False
    
    # 2. 格式化文本
    print("✍️  格式化文本...")
    text = format_news_for_speech(news, max_items=len(news))
    print(f"   文本长度: {len(text)} 字符")
    
    # 3. 生成语音
    print("🎙️  生成语音...")
    # 格式: "2026-03-08-19:46" -> "2026-3-8"
    date_part = news_update_t.split("-")[:3]
    date_str = f"{int(date_part[0])}-{int(date_part[1])}-{int(date_part[2])}"
    
    # 输出到 output 目录
    site_output_dir = OUTPUT_DIR / output_dir_name
    site_output_dir.mkdir(parents=True, exist_ok=True)
    output_path = site_output_dir / f"{date_str}.mp3"
    
    mp3_path = generate_speech_sync(text, str(output_path))
    print(f"   已保存: {mp3_path}")
    mp3_path = Path(mp3_path)
    
    # 4. 上传到 Google Drive
    print("☁️  上传至 Google Drive...")
    try:
        path = upload_to_gdrive(str(mp3_path))
        print(f"   已上传: {path}")
    except Exception as e:
        print(f"   上传失败: {e}")
    
    # 5. 复制到 public 目录
    public_audio_dir = PUBLIC_DIR / "audio" / public_dir_name
    public_audio_dir.mkdir(parents=True, exist_ok=True)
    target_path = public_audio_dir / mp3_path.name
    target_path.write_bytes(mp3_path.read_bytes())
    print(f"   已复制到: {target_path}")
    
    # 只保留最新5个文件
    mp3_files = sorted(public_audio_dir.glob("*.mp3"), key=lambda f: f.stat().st_mtime, reverse=True)
    for f in mp3_files[5:]:
        f.unlink()
        print(f"   已删除旧文件: {f}")
    
    return True


def main():
    print(f"[{datetime.now()}] 开始生成新闻语音...")
    
    # 加载配置
    config = load_config()
    sites = config.get("sites", [])
    
    if not sites:
        print("❌ 没有配置任何站点")
        return
    
    # 加载上次更新时间
    last_update_file = OUTPUT_DIR / "last_update.json"
    last_update_data = {}
    if last_update_file.exists():
        try:
            with open(last_update_file, "r", encoding="utf-8") as f:
                last_update_data = json.load(f)
        except json.JSONDecodeError:
            pass
    
    # 确保 output 目录存在
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    # 处理每个站点
    any_updated = False
    for site in sites:
        if process_site(site, last_update_data):
            any_updated = True
    
    # 保存更新时间
    with open(last_update_file, "w", encoding="utf-8") as f:
        json.dump(last_update_data, f, ensure_ascii=False, indent=2)
    
    # 6. 部署到 Vercel
    if any_updated:
        print(f"\n🚀 部署到 Vercel...")
        vercel_path = shutil.which("vercel") if shutil.which("vercel") else "npx vercel"
        os.system(f"{vercel_path} --prod")
    else:
        print(f"\n✅ 没有更新，跳过部署")
    
    print(f"\n[{datetime.now()}] 完成!")


if __name__ == "__main__":
    main()
