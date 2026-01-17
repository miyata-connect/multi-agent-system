# agents/coder.py
# 行数: 28行
# コード役エージェント

from langchain_core.messages import HumanMessage
from config import get_coder
from utils import extract_content

def call_coder(requirement_text: str) -> str:
    """コード役に依頼"""
    model = get_coder()
    messages = [
        HumanMessage(content=f"あなたは世界最高峰のソフトウェアエンジニアです。要件に基づき高品質なコードを書いてください。\n\n要件:\n{requirement_text}")
    ]
    return extract_content(model.invoke(messages))

def call_coder_fix(original_code: str, feedback: str) -> str:
    """コード役に修正依頼"""
    model = get_coder()
    messages = [
        HumanMessage(content=f"""あなたは世界最高峰のソフトウェアエンジニアです。
以下のコードに対するレビュー指摘を受けて、修正版を作成してください。

【元のコード】
{original_code}

【レビュー指摘】
{feedback}

修正版のコードを出力してください。""")
    ]
    return extract_content(model.invoke(messages))
