# agents/data_processor.py
# 行数: 13行
# データ役エージェント

from langchain_core.messages import HumanMessage, SystemMessage
from config import get_data_processor
from utils import extract_content

def call_data_processor(text_data: str) -> str:
    """データ役に依頼"""
    model = get_data_processor()
    messages = [
        SystemMessage(content="あなたは優秀なデータ処理係です。テキストを分析し、重要なポイントを要約して整理してください。日本語で回答。"),
        HumanMessage(content=text_data)
    ]
    return extract_content(model.invoke(messages))
