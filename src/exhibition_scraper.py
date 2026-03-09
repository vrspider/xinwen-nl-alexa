"""
展览网站爬虫 - 使用 Firecrawl 爬取博物馆展览信息
用法: from exhibition_scraper import scrape_exhibitions
"""
import json
import os
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / ".env.local")


def load_exhibitions_config(config_path: str = None) -> List[Dict[str, Any]]:
    """加载展览网站配置"""
    if config_path is None:
        config_path = PROJECT_ROOT / "config" / "exhibitions.json"
    
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    
    return config.get("exhibitions", [])


def scrape_exhibition(url: str) -> str:
    """使用 Firecrawl 爬取单个展览页面"""
    try:
        from firecrawl import FirecrawlApp
    except ImportError:
        print("firecrawl not installed. Run: pip install firecrawl-py")
        return ""
    
    api_key = os.environ.get("FIRECRAWL_API_KEY")
    if not api_key:
        print("错误: 未找到 FIRECRAWL_API_KEY")
        return ""
    
    app = FirecrawlApp(api_key=api_key)
    
    # 爬取并转换为 markdown
    # 等待页面加载
    actions = [
        {"action": "wait", "milliseconds": 2000},
    ]
    
    try:
        result = app.scrape(
            url=url, 
            formats=['markdown'],
            block_ads=True,
            actions=actions
        )
        if result and hasattr(result, 'markdown'):
            return result.markdown
        elif isinstance(result, dict):
            return result.get('markdown', '')
        return ""
    except Exception as e:
        print(f"爬取失败 {url}: {e}")
        return ""


def scrape_all_exhibitions(config_path: str = None) -> Dict[str, str]:
    """爬取所有配置的展览网站，返回 {site_id: markdown}"""
    exhibitions = load_exhibitions_config(config_path)
    results = {}
    
    for exhibition in exhibitions:
        site_id = exhibition.get("id")
        url = exhibition.get("url")
        name = exhibition.get("name")
        
        print(f"🔍 爬取: {name} ({url})")
        
        markdown = scrape_exhibition(url)
        if markdown:
            results[site_id] = markdown
            print(f"   ✓ 获取到 {len(markdown)} 字符")
        else:
            print(f"   ✗ 爬取失败")
    
    return results


def save_exhibitions_markdown(output_path: str = None, config_path: str = None):
    """爬取所有展览并保存到 markdown 文件"""
    if output_path is None:
        output_path = PROJECT_ROOT / "output" / "exhibitions" / "exhibitions.md"
    
    results = scrape_all_exhibitions(config_path)
    exhibitions = load_exhibitions_config(config_path)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# 荷兰博物馆展览信息\n\n")
        
        for exhibition in exhibitions:
            site_id = exhibition.get("id")
            name = exhibition.get("name")
            city = exhibition.get("city")
            
            f.write(f"## {name} - {city}\n\n")
            
            if site_id in results:
                f.write(results[site_id])
            else:
                f.write("(爬取失败)\n")
            
            f.write("\n\n---\n\n")
    
    print(f"✅ 展览信息已保存: {output_path}")
    return output_path


def get_exhibitions_markdown(config_path: str = None) -> str:
    """获取所有展览的 markdown 内容（用于 LLM prompt）"""
    results = scrape_all_exhibitions(config_path)
    exhibitions = load_exhibitions_config(config_path)
    
    markdown = "# 荷兰博物馆展览信息\n\n"
    
    for exhibition in exhibitions:
        site_id = exhibition.get("id")
        name = exhibition.get("name")
        city = exhibition.get("city")
        
        markdown += f"## {name} - {city}\n\n"
        
        if site_id in results:
            markdown += results[site_id]
        else:
            markdown += "(爬取失败)\n"
        
        markdown += "\n\n---\n\n"
    
    return markdown



if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="爬取荷兰博物馆展览信息")
    parser.add_argument("--config", default=None, help="展览配置文件路径")
    parser.add_argument("--output", default=None, help="输出 markdown 文件路径")
    
    args = parser.parse_args()
    
    # 生成完整版
    save_exhibitions_markdown(args.output, args.config)
    
    # 同时生成轻量版
    print("\n生成轻量版...")
    light_path = args.output.replace('.md', '-light.md') if args.output else None
    save_light_exhibitions_markdown(light_path, args.config)


def clean_exhibitions_markdown(markdown: str) -> str:
    """清理 markdown，移除不必要的链接和图片，只保留文字内容"""
    import re
    
    # 移除图片链接 ![](url)
    markdown = re.sub(r'!\[.*?\]\(.*?\)', '', markdown)
    
    # 移除超链接 [text](url) 但保留文字
    markdown = re.sub(r'\[([^\]]+)\]\(https?://[^)]+\)', r'\1', markdown)
    
    # 移除 cookie 相关内容
    cookie_patterns = [
        r'We use cookies.*?(?=\n\n|\n[A-Z]|$)',
        r'Cookie notice.*?(?=\n\n|\n[A-Z]|$)',
        r'Accept all.*?(?=\n\n|\n[A-Z]|$)',
        r'Cookie policy.*?(?=\n\n|\n[A-Z]|$)',
        r'This website uses cookies.*?(?=\n\n|\n[A-Z]|$)',
        r'By clicking.*?accept.*?(?=\n\n|\n[A-Z]|$)',
    ]
    for pattern in cookie_patterns:
        markdown = re.sub(pattern, '', markdown, flags=re.IGNORECASE | re.DOTALL)
    
    # 移除多余的空行
    markdown = re.sub(r'\n{3,}', '\n\n', markdown)
    
    return markdown.strip()


def extract_exhibition_info(markdown: str) -> str:
    """从 markdown 中提取展览关键信息"""
    import re
    
    # 清理 markdown
    markdown = clean_exhibitions_markdown(markdown)
    
    lines = markdown.split('\n')
    result_lines = []
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if re.match(r'^[\-\*\#\=]+$', line):
            continue
        result_lines.append(line)
    
    return '\n'.join(result_lines[:50])


def save_light_exhibitions_markdown(output_path: str = None, config_path: str = None):
    """爬取并保存轻量级展览信息（去除了链接和图片）"""
    if output_path is None:
        output_path = PROJECT_ROOT / "output" / "exhibitions" / "exhibitions-light.md"
    
    results = scrape_all_exhibitions(config_path)
    exhibitions = load_exhibitions_config(config_path)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# 荷兰博物馆展览信息 (轻量版)\n\n")
        
        for exhibition in exhibitions:
            site_id = exhibition.get("id")
            name = exhibition.get("name")
            city = exhibition.get("city")
            
            f.write(f"## {name} - {city}\n\n")
            
            if site_id in results:
                info = extract_exhibition_info(results[site_id])
                f.write(info)
            else:
                f.write("(爬取失败)\n")
            
            f.write("\n\n---\n\n")
    
    print(f"✅ 轻量版展览信息已保存: {output_path}")
    return output_path
