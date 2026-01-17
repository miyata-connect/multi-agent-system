# utils/helpers.py
# 行数: 15行
# ヘルパー関数

def extract_content(response):
    """レスポンスからテキストを抽出"""
    content = response.content
    if isinstance(content, list):
        texts = []
        for c in content:
            if isinstance(c, dict) and 'text' in c:
                texts.append(c['text'])
            else:
                texts.append(str(c))
        return " ".join(texts)
    return content
