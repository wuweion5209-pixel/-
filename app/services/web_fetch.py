import requests
from bs4 import BeautifulSoup
import re


def extract_main_content(url: str) -> str:
    """
    抓取网页有效内容，清理噪音后返回主要内容
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # 移除脚本和样式
        for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            tag.decompose()

        # 尝试提取主要内容区域
        main_content = (
            soup.find('article') or
            soup.find('main') or
            soup.find('div', class_=re.compile(r'content|article|post|main', re.I)) or
            soup.find('div', id=re.compile(r'content|article|post|main', re.I)) or
            soup.body
        )

        if not main_content:
            return ""

        # 提取文本
        text = main_content.get_text(separator='\n', strip=True)

        # 清理：去除多余空白行
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        cleaned_text = '\n'.join(lines)

        # 限制长度，避免过长
        max_length = 8000
        if len(cleaned_text) > max_length:
            cleaned_text = cleaned_text[:max_length] + "\n...（内容过长，已截断）"

        return cleaned_text

    except Exception as e:
        return f"抓取失败: {str(e)}"