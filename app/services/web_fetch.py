import requests
from bs4 import BeautifulSoup
import re


def extract_main_content(url: str) -> str:
    """
    抓取网页有效内容，清理噪音后返回主要内容
    优先使用 Jina Reader API（支持 JavaScript 渲染），失败时回退到直接抓取
    """
    # 优先使用 Jina Reader API
    try:
        jina_url = f"https://r.jina.ai/{url}"
        response = requests.get(jina_url, timeout=20)
        if response.status_code == 200:
            text = response.text
            if text:
                # 清理 Markdown 标记
                text = re.sub(r'!\[Image \d+\]\([^)]+\)', '', text)  # 删除图片
                text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)  # 链接转文本
                text = re.sub(r'#+ ', '', text)  # 删除标题标记
                text = re.sub(r'\*+', '', text)  # 删除加粗斜体标记

                # 清理多余空白
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                cleaned_text = '\n'.join(lines)

                max_length = 8000
                if len(cleaned_text) > max_length:
                    cleaned_text = cleaned_text[:max_length] + "\n...（内容过长，已截断）"

                return cleaned_text
    except Exception as e:
        # Jina 失败，继续尝试直接抓取
        pass

    # 回退方案：直接抓取（适用于纯 HTML）
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
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
            soup.find('section') or
            soup.find('div', class_=re.compile(r'content|article|post|main|hero', re.I)) or
            soup.find('div', id=re.compile(r'content|article|post|main|hero', re.I)) or
            soup.body
        )

        # 提取文本
        text = ""
        if main_content:
            text = main_content.get_text(separator='\n', strip=True)

        # 如果内容太少，尝试从 meta 标签获取
        if not text or len(text.strip()) < 100:
            meta_parts = []
            for meta in soup.find_all('meta'):
                content = meta.get('content', '')
                name = meta.get('name') or meta.get('property') or ''
                # 过滤无意义的 meta
                if content and len(content) > 20 and name not in [
                    'viewport', 'format-detection', 'msvalidate.01',
                    'google-site-verification', 'baidu-site-verification'
                ] and not content.replace('-', '').replace(' ', '').isalnum():
                    meta_parts.append(content)

            if meta_parts:
                text = "\n".join(meta_parts)

        # 清理：去除多余空白行
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        cleaned_text = '\n'.join(lines)

        # 如果仍然是空的，返回提示
        if not cleaned_text or len(cleaned_text) < 50:
            return f"该网页 ({url}) 为单页应用(SPA)，内容通过 JavaScript 动态渲染，无法直接抓取。\n\n网页标题: {soup.title.text if soup.title else '无'}"

        # 限制长度，避免过长
        max_length = 8000
        if len(cleaned_text) > max_length:
            cleaned_text = cleaned_text[:max_length] + "\n...（内容过长，已截断）"

        return cleaned_text

    except requests.exceptions.Timeout:
        return f"抓取超时: {url}"
    except requests.exceptions.RequestException as e:
        return f"抓取失败: {str(e)}"
    except Exception as e:
        return f"抓取失败: {str(e)}"