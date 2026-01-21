import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage
from conversation_memory import memory
from cross_context_manager import cross_context

load_dotenv()

# 🔄 グローバル変数：現在のクロスコンテキスト
_current_cross_context = None

def set_cross_context(cross_context_data):
    """現在のクロスコンテキストを設定"""
    global _current_cross_context
    _current_cross_context = cross_context_data

# ==========================================
# 1. 監査役 (ChatGPT GPT-5.2)
# ==========================================
def get_auditor_model():
    return ChatOpenAI(
        model="gpt-5.2",
        temperature=0,
        api_key=os.getenv("OPENAI_API_KEY")
    )

@tool
def call_auditor(plan_text: str) -> str:
    """
    監査役(ChatGPT GPT-5.2): 計画のリスクを指摘します。
    計画書や提案を受け取り、技術的リスク・コスト・実現可能性を厳しく監査します。
    """
    print(f"\n[System] 👮‍♂️ 監査役(GPT-5.2) リスクチェック中...")
    try:
        # 🤝 クロスコンテキスト取得
        context_text = ""
        if _current_cross_context:
            context_text = cross_context.format_for_subordinate(_current_cross_context, 'auditor')
        
        model = get_auditor_model()
        messages = [
            SystemMessage(content=f"""あなたは冷徹な監査役です。ユーザーの計画に対し、技術的リスク、コスト超過リスク、実現可能性の懸念点のみを厳しく指摘してください。褒める必要はありません。日本語で回答してください。

{context_text}"""),
            HumanMessage(content=plan_text)
        ]
        response = model.invoke(messages)
        
        # 🧠 回答を記憶に追加
        memory.add_session_message('assistant', response.content, 'auditor')
        
        return response.content
    except Exception as e:
        return f"監査役エラー: {str(e)}"

# ==========================================
# 2. コード役 (Claude Sonnet 4.5)
# ==========================================
def get_coder_model():
    return ChatAnthropic(
        model="claude-sonnet-4-5-20250929",
        temperature=0,
        api_key=os.getenv("ANTHROPIC_API_KEY")
    )

@tool
def call_coder(requirement_text: str) -> str:
    """
    コード役(Claude Sonnet 4.5): コードを実装します。
    要件を受け取り、高品質でバグのない完璧なコードを作成します。
    """
    print(f"\n[System] 👨‍💻 コード役(Claude Sonnet 4.5) 実装中...")
    try:
        # 🤝 クロスコンテキスト取得
        context_text = ""
        if _current_cross_context:
            context_text = cross_context.format_for_subordinate(_current_cross_context, 'coder')
        
        model = get_coder_model()
        messages = [
            HumanMessage(content=f"""あなたは世界最高峰のソフトウェアエンジニアです。渡された要件に基づき、実用的で高品質なコードを書いてください。解説は最小限にし、コードブロックをメインに出力してください。

{context_text}

【要件】
{requirement_text}""")
        ]
        response = model.invoke(messages)
        
        # 🧠 回答を記憶に追加
        memory.add_session_message('assistant', response.content, 'coder')
        
        return response.content
    except Exception as e:
        return f"コード役エラー: {str(e)}"

# ==========================================
# 3. データ役 (Llama 3.3 70B on Groq)
# ==========================================
def get_data_model():
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0,
        api_key=os.getenv("GROQ_API_KEY")
    )

@tool
def call_data_processor(text_data: str) -> str:
    """
    データ役(Llama 3.3 70B): データの要約・処理を行います。
    大量のテキストデータや資料を受け取り、高速に要約・整理して結果を返します。
    """
    print(f"\n[System] 🦙 データ役(Llama 3.3 70B) 高速処理中...")
    try:
        # 🤝 クロスコンテキスト取得
        context_text = ""
        if _current_cross_context:
            context_text = cross_context.format_for_subordinate(_current_cross_context, 'data_processor')
        
        model = get_data_model()
        messages = [
            SystemMessage(content=f"""あなたは優秀なデータ処理係です。渡されたテキストデータを分析し、重要なポイントを要約して整理してください。日本語で回答してください。

{context_text}"""),
            HumanMessage(content=text_data)
        ]
        response = model.invoke(messages)
        
        # 🧠 回答を記憶に追加
        memory.add_session_message('assistant', response.content, 'data_processor')
        
        return response.content
    except Exception as e:
        return f"データ役エラー: {str(e)}"
