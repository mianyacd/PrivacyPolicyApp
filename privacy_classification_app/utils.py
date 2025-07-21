import requests
from bs4 import BeautifulSoup
import re

def extract_last_updated(url):
    """
    从隐私政策页面提取“Last Updated”或类似字段。
    返回 YYYY-MM-DD 格式 或 None。
    """
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text().lower()

        for keyword in ["last updated", "effective date", "last modified"]:
            idx = text.find(keyword)
            if idx != -1:
                snippet = text[idx: idx + 100]
                match = re.search(r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})', snippet)
                if match:
                    return match.group(1)
        return None
    except Exception:
        return None

def is_real_span(span, sentence):
    """
    检查 span 是否在 sentence 中，避免无效预测
    """
    if not span or not sentence:
        return False
    return span.lower() in sentence.lower()
