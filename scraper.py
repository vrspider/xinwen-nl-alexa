"""
新闻爬虫模块
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict

URL = "https://xinwen.nl/"

def fetch_news() -> List[Dict[str, str]]:
    """获取新闻列表"""
    response = requests.get(URL, timeout=30)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, "html.parser")
    news_list = []
    
    # 查找所有文章 - 基于实际页面结构调整选择器
    articles = soup.select("main article")
    
    for article in articles:
        # 尝试多种选择器获取标题
        title_elem = (
            article.select_one("h3") or 
            article.select_one("header h3") or
            article.select_one("[class*='title']")
        )
        
        # 尝试多种选择器获取内容
        content_elem = (
            article.select_one("div[itemprop='articleBody']") or
            article.select_one(".excerpt")
        )
        
        if title_elem:
            title = title_elem.get_text(strip=True)
            content = content_elem.get_text(strip=True) if content_elem else ""
            
            if title:
                news_list.append({
                    "title": title,
                    "content": content
                })
    
    return news_list

def format_news_for_speech(news_list: List[Dict[str, str]], max_items: int = 10) -> str:
    """将新闻格式化为语音文本"""
    today = datetime.now().strftime("%Y年%m月%d日")
    text = f"欢迎收听{today}的荷兰新闻精选。\n\n"
    
    for i, news in enumerate(news_list[:max_items], 1):
        text += f"第{i}条：{news['title']}。"
        if news['content']:
            # 取内容前100字
            content_short = news['content'][:100]
            text += f"{content_short}。\n"
        text += "\n"
    
    text += "以上就是今天的新闻精选，感谢收听。"
    return text

def fetch_news_update_time() -> str:
    """获取新闻的更新时间"""
    response = requests.get(URL, timeout=30)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, "html.parser")
    
    # 尝试多种选择器获取更新时间 
    # body > div.container > div.container.tm-container-2 > div:nth-child(1) > div > p
    # string will be like "更新时间: 2026年03月02日"
    time_elem = (
        soup.select_one("body > div.container > div.container.tm-container-2 > div:nth-child(1) > div > p") or
        soup.select_one("time[datetime]") or
        soup.select_one(".update-time")
    )
    
    if time_elem:
        time_text = time_elem.get_text(strip=True)
        # 提取日期部分 - 假设格式为 "更新时间: 2026年03月02日 星期 1 23:46"
        if "更新时间" in time_text:
            date_part = time_text.split("更新时间:")[-1].strip().split()[0]
            return date_part
    
    return "未知时间"   

if __name__ == "__main__":
    news = fetch_news()
    print(f"获取到 {len(news)} 条新闻")
    for n in news[:3]:
        print(f"- {n['title']}")
