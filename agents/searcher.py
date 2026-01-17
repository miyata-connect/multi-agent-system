# agents/searcher.py
# 行数: 13行
# 検索役エージェント（Grok）

from langchain_core.messages import HumanMessage, SystemMessage
from config import get_searcher
from utils import extract_content

def call_searcher(query: str) -> str:
    """検索役（Grok）に依頼"""
    model = get_searcher()
    messages = [
        SystemMessage(content="あなたは世界最高峰のリアルタイム情報検索エージェントです。深い推論を用いて最新情報を正確に検索し、X（Twitter）の最新データも活用して回答してください。日本語で回答。"),
        HumanMessage(content=query)
    ]
    return extract_content(model.invoke(messages))
