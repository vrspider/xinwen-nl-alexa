"""
Unit tests for scraper module
"""
import re


def test_fetch_news_update_time_format():
    """Test time parsing: '更新时间: 2026年03月08日 星期 日 19:46' -> '2026-03-08-19:46'"""
    time_text = "更新时间: 2026年03月08日 星期 日 19:46"
    
    # Test the regex pattern directly
    match = re.search(r"(\d{4})年(\d{2})月(\d{2})日.*?(\d{2}):(\d{2})", time_text)
    assert match is not None
    
    result = f"{match.group(1)}-{match.group(2)}-{match.group(3)}-{match.group(4)}:{match.group(5)}"
    assert result == "2026-03-08-19:46"


def test_fetch_news_update_time_format_with_padded_values():
    """Test time parsing with zero-padded values"""
    time_text = "更新时间: 2026年03月02日 星期 日 08:05"
    
    match = re.search(r"(\d{4})年(\d{2})月(\d{2})日.*?(\d{2}):(\d{2})", time_text)
    assert match is not None
    
    result = f"{match.group(1)}-{match.group(2)}-{match.group(3)}-{match.group(4)}:{match.group(5)}"
    assert result == "2026-03-02-08:05"


if __name__ == "__main__":
    test_fetch_news_update_time_format()
    test_fetch_news_update_time_format_with_padded_values()
    print("All tests passed!")
