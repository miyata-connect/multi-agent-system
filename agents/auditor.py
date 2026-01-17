# agents/auditor.py
# 行数: 32行
# 監査役エージェント

from langchain_core.messages import HumanMessage, SystemMessage
from config import get_auditor
from utils import extract_content

def call_auditor(plan_text: str) -> str:
    """監査役に依頼"""
    model = get_auditor()
    messages = [
        SystemMessage(content="あなたは冷徹な監査役です。計画に対し、技術的リスク、コスト超過リスク、実現可能性の懸念点を厳しく指摘してください。日本語で回答。"),
        HumanMessage(content=plan_text)
    ]
    return extract_content(model.invoke(messages))

def call_code_review(code: str) -> dict:
    """監査役にコードレビュー依頼"""
    model = get_auditor()
    messages = [
        SystemMessage(content="""あなたは厳格なコードレビュアーです。
コードを分析し、以下の形式で回答してください：

【判定】OK または 要修正
【問題点】（要修正の場合のみ）具体的な問題点を列挙
【推奨修正】（要修正の場合のみ）修正方法の提案

バグ、セキュリティ問題、エッジケース未対応、パフォーマンス問題を重点的にチェックしてください。
日本語で回答。"""),
        HumanMessage(content=f"以下のコードをレビューしてください：\n\n{code}")
    ]
    review = extract_content(model.invoke(messages))
    
    # 判定を抽出
    is_ok = "【判定】OK" in review or "判定】OK" in review
    return {"approved": is_ok, "feedback": review}
