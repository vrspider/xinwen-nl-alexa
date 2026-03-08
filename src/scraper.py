"""
新闻爬虫模块 - 支持多站点配置
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict, Any
import re


def fetch_news(site_config: Dict[str, Any]) -> List[Dict[str, str]]:
    """根据配置获取新闻列表"""
    url = site_config["url"]
    selectors = site_config.get("selectors", {})
    
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, "html.parser")
    news_list = []
    
    # 获取文章列表选择器
    articles_selector = selectors.get("articles", "article")
    articles = soup.select(articles_selector)
    
    # 获取标题选择器 (逗号分隔的多个选择器)
    title_selectors = selectors.get("title", "h3").split(",")
    # 获取内容选择器
    content_selectors = selectors.get("content", "").split(",")
    
    for article in articles:
        # 尝试多个标题选择器
        title = ""
        for sel in title_selectors:
            title_elem = article.select_one(sel.strip())
            if title_elem:
                title = title_elem.get_text(strip=True)
                break
        
        # 尝试多个内容选择器
        content = ""
        for sel in content_selectors:
            if sel.strip():
                content_elem = article.select_one(sel.strip())
                if content_elem:
                    content = content_elem.get_text(strip=True)
                    break
        
        if title:
            news_list.append({
                "title": title,
                "content": content
            })
    
    return news_list


def format_news_for_speech(news_list: List[Dict[str, str]], max_items: int = 10) -> str:
    """将新闻格式化为语音文本"""
    today = datetime.now().strftime("%Y年%m月%d日")
    text = f"欢迎收听{today}的新闻精选。\n\n"
    
    for i, news in enumerate(news_list[:max_items], 1):
        text += f"{i}：{news['title']}。"
        if news['content']:
            # 取内容前100字
            content_short = news['content'][:100]
            text += f"{content_short}。\n"
        text += "\n"
    
    text += "以上就是今天的新闻精选，感谢收听。"
    return text


def fetch_news_update_time(site_config: Dict[str, Any]) -> str:
    """根据配置获取新闻的更新时间"""
    url = site_config["url"]
    selectors = site_config.get("selectors", {})
    
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, "html.parser")
    
    # 获取更新时间选择器
    time_selectors = selectors.get("updateTime", "").split(",")
    
    for sel in time_selectors:
        if sel.strip():
            time_elem = soup.select_one(sel.strip())
            if time_elem:
                time_text = time_elem.get_text(strip=True)
                # 格式: "更新时间: 2026年03月08日 星期 日 19:46" -> "2026-03-08-19:46"
                match = re.search(r"(\d{4})年(\d{2})月(\d{2})日.*?(\d{2}):(\d{2})", time_text)
                if match:
                    return f"{match.group(1)}-{match.group(2)}-{match.group(3)}-{match.group(4)}:{match.group(5)}"
                return time_text
    
    return "未知时间"


if __name__ == "__main__":
    import json
    with open("sites.json", "r") as f:
        config = json.load(f)
    
    for site in config["sites"]:
        news = fetch_news(site)
        print(f"[{site['name']}] 获取到 {len(news)} 条新闻")
        for n in news[:3]:
            print(f"  - {n['title']}")
