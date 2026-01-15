import os
import streamlit as st
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

# 環境変数を読み込む（最初に実行）
load_dotenv()

# ==========================================
# ページ設定
# ==========================================
st.set_page_config(
    page_title="Multi-Agent System",
    page_icon="🤖",
    layout="wide"
)

# ==========================================
# APIキー設定（ローカル.env優先）
# ==========================================
GEMINI_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY")
GROQ_KEY = os.getenv("GROQ_API_KEY")

# Google APIキーを環境変数にセット
if GEMINI_KEY:
    os.environ["GOOGLE_API_KEY"] = GEMINI_KEY

# ==========================================
# モデル初期化
# ==========================================
@st.cache_resource
def get_commander():
    """司令塔 (Gemini 3 Pro)"""
    return ChatGoogleGenerativeAI(
        model="gemini-3-pro-preview",
        temperature=0.5,
    )

@st.cache_resource
def get_auditor():
    """監査役 (GPT-5.2)"""
    return ChatOpenAI(
        model="gpt-5.2",
        temperature=0,
        api_key=OPENAI_KEY
    )

@st.cache_resource
def get_coder():
    """コード役 (Claude Sonnet 4.5)"""
    return ChatAnthropic(
        model="claude-sonnet-4-5-20250929",
        temperature=0,
        api_key=ANTHROPIC_KEY
    )

@st.cache_resource
def get_data_processor():
    """データ役 (Llama 3.3 70B)"""
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0,
        api_key=GROQ_KEY
    )

# ==========================================
# エージェント関数
# ==========================================
def call_auditor(plan_text: str) -> str:
    """監査役に依頼"""
    model = get_auditor()
    messages = [
        SystemMessage(content="あなたは冷徹な監査役です。計画に対し、技術的リスク、コスト超過リスク、実現可能性の懸念点を厳しく指摘してください。日本語で回答。"),
        HumanMessage(content=plan_text)
    ]
    response = model.invoke(messages)
    return response.content

def call_coder(requirement_text: str) -> str:
    """コード役に依頼"""
    model = get_coder()
    messages = [
        HumanMessage(content=f"あなたは世界最高峰のソフトウェアエンジニアです。要件に基づき高品質なコードを書いてください。\n\n要件:\n{requirement_text}")
    ]
    response = model.invoke(messages)
    return response.content

def call_data_processor(text_data: str) -> str:
    """データ役に依頼"""
    model = get_data_processor()
    messages = [
        SystemMessage(content="あなたは優秀なデータ処理係です。テキストを分析し、重要なポイントを要約して整理してください。日本語で回答。"),
        HumanMessage(content=text_data)
    ]
    response = model.invoke(messages)
    return response.content

def call_commander(user_input: str, chat_history: list) -> str:
    """司令塔に依頼（タスク振り分け）"""
    model = get_commander()
    
    system_prompt = """あなたは優秀なプロジェクトマネージャー（司令塔）です。
ユーザーの依頼を分析し、適切な部下を選んでタスクを実行してください。

利用可能な部下:
1. 監査役（GPT-5.2）- 計画のリスク分析、懸念点の指摘 → [AUDITOR]タグで呼び出し
2. コード役（Claude Sonnet 4.5）- コード実装、プログラミング → [CODER]タグで呼び出し
3. データ役（Llama 3.3 70B）- データ要約、情報整理 → [DATA]タグで呼び出し

回答形式:
- 部下を使う場合: [AUDITOR], [CODER], [DATA]のいずれかのタグと依頼内容を返す
- 自分で回答する場合: [SELF]タグと回答を返す

例:
- 「コードを書いて」→ [CODER] Pythonでフィボナッチ数列を計算する関数
- 「この計画のリスクは？」→ [AUDITOR] ECサイト構築計画のリスク分析
- 「要約して」→ [DATA] 以下のテキストを要約...
- 「こんにちは」→ [SELF] こんにちは！何かお手伝いできることはありますか？"""

    messages = [SystemMessage(content=system_prompt)]
    
    # チャット履歴を追加
    for msg in chat_history[-6:]:  # 直近6件のみ
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        else:
            messages.append(SystemMessage(content=msg["content"]))
    
    messages.append(HumanMessage(content=user_input))
    
    response = model.invoke(messages)
    return response.content

def process_command(commander_response: str, original_input: str) -> tuple:
    """司令塔の指示を処理"""
    if "[AUDITOR]" in commander_response:
        task = commander_response.split("[AUDITOR]")[-1].strip()
        if not task:
            task = original_input
        return "auditor", call_auditor(task)
    elif "[CODER]" in commander_response:
        task = commander_response.split("[CODER]")[-1].strip()
        if not task:
            task = original_input
        return "coder", call_coder(task)
    elif "[DATA]" in commander_response:
        task = commander_response.split("[DATA]")[-1].strip()
        if not task:
            task = original_input
        return "data", call_data_processor(task)
    else:
        # [SELF]または判定不能の場合は司令塔の回答をそのまま使う
        clean_response = commander_response.replace("[SELF]", "").strip()
        return "self", clean_response

# ==========================================
# UI
# ==========================================
st.title("🤖 Multi-Agent System")
st.markdown("**2026年1月版 - 4つのLLMが協力してタスクを実行**")

# サイドバー: チーム紹介
with st.sidebar:
    st.header("👥 エージェントチーム")
    st.markdown("""
    | 役割 | モデル |
    |------|--------|
    | 👑 司令塔 | Gemini 3 Pro |
    | 👮‍♂️ 監査役 | GPT-5.2 |
    | 👨‍💻 コード役 | Claude Sonnet 4.5 |
    | 🦙 データ役 | Llama 3.3 70B |
    """)
    
    st.divider()
    
    # APIキー状態表示
    st.header("🔑 APIキー状態")
    st.markdown(f"- Gemini: {'✅' if GEMINI_KEY else '❌'}")
    st.markdown(f"- OpenAI: {'✅' if OPENAI_KEY else '❌'}")
    st.markdown(f"- Anthropic: {'✅' if ANTHROPIC_KEY else '❌'}")
    st.markdown(f"- Groq: {'✅' if GROQ_KEY else '❌'}")
    
    st.divider()
    
    if st.button("🗑️ チャット履歴をクリア"):
        st.session_state.messages = []
        st.rerun()

# APIキーチェック
missing_keys = []
if not GEMINI_KEY:
    missing_keys.append("GEMINI_API_KEY")
if not OPENAI_KEY:
    missing_keys.append("OPENAI_API_KEY")
if not ANTHROPIC_KEY:
    missing_keys.append("ANTHROPIC_API_KEY")
if not GROQ_KEY:
    missing_keys.append("GROQ_API_KEY")

if missing_keys:
    st.error(f"❌ 以下のAPIキーが設定されていません: {', '.join(missing_keys)}")
    st.info("💡 .envファイルにAPIキーを設定してください。")
    st.stop()

# チャット履歴初期化
if "messages" not in st.session_state:
    st.session_state.messages = []

# チャット履歴表示
for message in st.session_state.messages:
    with st.chat_message(message["role"], avatar=message.get("avatar")):
        st.markdown(message["content"])

# ユーザー入力
if prompt := st.chat_input("メッセージを入力してください..."):
    # ユーザーメッセージを追加
    st.session_state.messages.append({"role": "user", "content": prompt, "avatar": "👤"})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)
    
    # 司令塔が判断
    with st.chat_message("assistant", avatar="👑"):
        with st.spinner("🤔 Gemini司令塔が思考中..."):
            try:
                commander_response = call_commander(prompt, st.session_state.messages)
                agent_type, result = process_command(commander_response, prompt)
                
                # 使用したエージェントを表示
                agent_info = {
                    "auditor": ("👮‍♂️ 監査役(GPT-5.2)", "auditor"),
                    "coder": ("👨‍💻 コード役(Claude Sonnet 4.5)", "coder"),
                    "data": ("🦙 データ役(Llama 3.3 70B)", "data"),
                    "self": ("👑 司令塔(Gemini 3 Pro)", "self")
                }
                
                agent_name, _ = agent_info.get(agent_type, ("👑 司令塔", "self"))
                
                if agent_type != "self":
                    st.info(f"📋 {agent_name} に依頼しました")
                
                st.markdown(result)
                
                # 履歴に追加
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": result,
                    "avatar": "👑",
                    "agent": agent_type
                })
                
            except Exception as e:
                st.error(f"❌ エラー: {str(e)}")
                import traceback
                st.code(traceback.format_exc())
