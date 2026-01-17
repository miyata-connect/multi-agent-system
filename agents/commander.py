# agents/commander.py
# 行数: 29行
# 司令塔エージェント

from langchain_core.messages import HumanMessage, SystemMessage
from config import get_commander
from utils import extract_content

def call_commander(user_input: str, chat_history: list) -> str:
    """コンシェルジュに依頼（タスク振り分け・即答）"""
    model = get_commander()
    
    system_prompt = """あなたは優秀なコンシェルジュです。
ユーザーの依頼を分析し、最適な対応を選んでください。

利用可能なエージェント:
1. コード役（Claude Sonnet 4.5）- コード実装、プログラミング → [CODER]タグ
2. 検索役（Grok 4.1 Thinking）- リアルタイム情報検索、最新ニュース、X検索 → [SEARCH]タグ
3. データ役（Llama 3.3 70B）- データ要約、情報整理 → [DATA]タグ

判断基準:
- 簡単な質問、雑談、一般的な知識 → [SELF]で自分が即答
- コードを書く依頼 → [CODER]でコード役に依頼
- 最新情報、ニュース、検索が必要 → [SEARCH]で検索役に依頼
- データ分析、要約 → [DATA]でデータ役に依頼

回答形式:
- エージェントを使う場合: [CODER], [SEARCH], [DATA]のいずれかのタグと依頼内容を返す
- 自分で回答する場合: [SELF]タグと回答を返す

重要: 簡単な質問には無駄にエージェントを使わず、[SELF]で即答してください。
コードを書く依頼の場合は必ず[CODER]を使ってください。"""

    messages = [SystemMessage(content=system_prompt)]
    for msg in chat_history[-6:]:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        else:
            messages.append(SystemMessage(content=msg["content"]))
    messages.append(HumanMessage(content=user_input))
    
    return extract_content(model.invoke(messages))
