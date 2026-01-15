import os
import streamlit as st
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

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
# APIキー設定
# ==========================================
GEMINI_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY")
GROQ_KEY = os.getenv("GROQ_API_KEY")

if GEMINI_KEY:
    os.environ["GOOGLE_API_KEY"] = GEMINI_KEY

# ==========================================
# モデル初期化
# ==========================================
@st.cache_resource
def get_commander():
    return ChatGoogleGenerativeAI(model="gemini-3-pro-preview", temperature=0.5)

@st.cache_resource
def get_auditor():
    return ChatOpenAI(model="gpt-5.2", temperature=0, api_key=OPENAI_KEY)

@st.cache_resource
def get_coder():
    return ChatAnthropic(model="claude-sonnet-4-5-20250929", temperature=0, api_key=ANTHROPIC_KEY)

@st.cache_resource
def get_data_processor():
    return ChatGroq(model="llama-3.3-70b-versatile", temperature=0, api_key=GROQ_KEY)

# ==========================================
# ヘルパー関数
# ==========================================
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
    return extract_content(model.invoke(messages))

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

def call_data_processor(text_data: str) -> str:
    """データ役に依頼"""
    model = get_data_processor()
    messages = [
        SystemMessage(content="あなたは優秀なデータ処理係です。テキストを分析し、重要なポイントを要約して整理してください。日本語で回答。"),
        HumanMessage(content=text_data)
    ]
    return extract_content(model.invoke(messages))

def call_commander(user_input: str, chat_history: list) -> str:
    """司令塔に依頼（タスク振り分け）"""
    model = get_commander()
    
    system_prompt = """あなたは優秀なプロジェクトマネージャー（司令塔）です。
ユーザーの依頼を分析し、適切な部下を選んでタスクを実行してください。

利用可能な部下:
1. 監査役（GPT-5.2）- 計画のリスク分析、懸念点の指摘 → [AUDITOR]タグ
2. コード役（Claude Sonnet 4.5）- コード実装、プログラミング → [CODER]タグ
3. データ役（Llama 3.3 70B）- データ要約、情報整理 → [DATA]タグ

回答形式:
- 部下を使う場合: [AUDITOR], [CODER], [DATA]のいずれかのタグと依頼内容を返す
- 自分で回答する場合: [SELF]タグと回答を返す

コードを書く依頼の場合は必ず[CODER]を使ってください。"""

    messages = [SystemMessage(content=system_prompt)]
    for msg in chat_history[-6:]:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        else:
            messages.append(SystemMessage(content=msg["content"]))
    messages.append(HumanMessage(content=user_input))
    
    return extract_content(model.invoke(messages))

# ==========================================
# ループ構造：コード生成→レビュー→修正
# ==========================================
def code_with_review_loop(requirement: str, max_iterations: int = 3) -> dict:
    """コード生成→レビュー→修正のループ"""
    iterations = []
    
    # 初回コード生成
    st.write("**🔄 ループ1: コード生成中...**")
    code = call_coder(requirement)
    iterations.append({"type": "code", "content": code, "iteration": 1})
    
    for i in range(max_iterations):
        # レビュー
        st.write(f"**🔄 ループ{i+1}: コードレビュー中...**")
        review = call_code_review(code)
        iterations.append({"type": "review", "content": review["feedback"], "iteration": i+1})
        
        if review["approved"]:
            st.success(f"✅ レビュー通過！（{i+1}回目）")
            return {
                "final_code": code,
                "iterations": iterations,
                "approved": True,
                "total_iterations": i + 1
            }
        
        # 修正が必要
        if i < max_iterations - 1:
            st.warning(f"⚠️ 要修正（{i+1}回目）→ 修正中...")
            code = call_coder_fix(code, review["feedback"])
            iterations.append({"type": "fix", "content": code, "iteration": i+2})
    
    # 最大回数到達
    st.warning(f"⚠️ 最大{max_iterations}回のループ完了。最終版を返します。")
    return {
        "final_code": code,
        "iterations": iterations,
        "approved": False,
        "total_iterations": max_iterations
    }

# ==========================================
# 処理の振り分け

# ==========================================
# クロスチェック機能
# ==========================================
def cross_check(agent_type: str, result: str, original_task: str) -> dict:
    """
    クロスチェック機能: 他のエージェントが結果を100点満点で採点
    
    Args:
        agent_type: 実行したエージェント ("auditor", "coder", "data")
        result: エージェントの出力結果
        original_task: 元のタスク内容
    
    Returns:
        dict: 採点結果と改善提案
    """
    # 実行エージェント以外の2つのエージェントでチェック
    checkers = []
    if agent_type != "auditor":
        checkers.append(("auditor", get_auditor(), "👮‍♂️ 監査役(GPT-5.2)"))
    if agent_type != "coder":
        checkers.append(("coder", get_coder(), "👨‍💻 コード役(Claude Sonnet 4.5)"))
    if agent_type != "data":
        checkers.append(("data", get_data_processor(), "🦙 データ役(Llama 3.3 70B)"))
    
    # 最大2つのチェッカーを選択
    checkers = checkers[:2]
    
    check_results = []
    
    for checker_type, checker_model, checker_name in checkers:
        prompt = f"""以下の出力結果を100点満点で採点してください。

【元のタスク】
{original_task}

【実行エージェントの出力】
{result}

【採点基準】
1. 正確性 (25点): タスクの要求を正確に満たしているか
2. 妥当性 (25点): ロジックや論理展開が妥当か
3. セキュリティ (25点): セキュリティリスクはないか
4. パフォーマンス (25点): 効率的で最適な実装/回答か

【出力形式】
正確性: X/25点
妥当性: Y/25点
セキュリティ: Z/25点
パフォーマンス: W/25点
合計: N/100点

改善提案:
- 具体的な改善点を箇条書きで記載
"""
        
        try:
            messages = [HumanMessage(content=prompt)]
            response = checker_model.invoke(messages)
            check_results.append({
                "checker": checker_name,
                "evaluation": response.content
            })
        except Exception as e:
            check_results.append({
                "checker": checker_name,
                "evaluation": f"❌ 評価エラー: {str(e)}"
            })
    
    return {
        "checks": check_results,
        "total_checkers": len(check_results)
    }


# ==========================================
def process_command(commander_response: str, original_input: str, use_loop: bool, use_crosscheck: bool = True) -> tuple:
    """司令塔の指示を処理（クロスチェック対応）"""
    agent_type = None
    result = None
    loop_data = None
    task = original_input
    
    if "[AUDITOR]" in commander_response:
        task = commander_response.split("[AUDITOR]")[-1].strip() or original_input
        agent_type = "auditor"
        result = call_auditor(task)
    
    elif "[CODER]" in commander_response:
        task = commander_response.split("[CODER]")[-1].strip() or original_input
        if use_loop:
            loop_result = code_with_review_loop(task)
            agent_type = "coder_loop"
            result = loop_result["final_code"]
            loop_data = loop_result
        else:
            agent_type = "coder"
            result = call_coder(task)
    
    elif "[DATA]" in commander_response:
        task = commander_response.split("[DATA]")[-1].strip() or original_input
        agent_type = "data"
        result = call_data_processor(task)
    
    else:
        clean_response = commander_response.replace("[SELF]", "").strip()
        return "self", clean_response, None
    
    # クロスチェック実行（selfモード以外、かつuse_crosscheck=True）
    crosscheck_data = None
    if use_crosscheck and agent_type and agent_type != "coder_loop":  # ループモードは既にレビュー済み
        crosscheck_data = cross_check(agent_type, result, task)
    
    return agent_type, result, {"loop_data": loop_data, "crosscheck": crosscheck_data}

# ==========================================
# UI
# ==========================================
st.title("🤖 Multi-Agent System")
st.markdown("**2026年1月版 - ループ構造 + クロスチェック搭載**")

# サイドバー
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
    
    # ループ構造ON/OFF
    st.header("⚙️ 設定")
    use_loop = st.toggle("🔄 コードレビューループ", value=True, help="ONにするとコード生成後に自動でGPTがレビューし、問題があればClaudeが修正します")
    max_loop = st.slider("最大ループ回数", 1, 5, 3) if use_loop else 1
    
    use_crosscheck = st.toggle("📊 クロスチェック機能", value=True, help="ONにすると他のエージェントが結果を100点満点で採点します（処理時間増加）")
    
    st.divider()
    
    st.header("🔑 APIキー状態")
    st.markdown(f"- Gemini: {'✅' if GEMINI_KEY else '❌'}")
    st.markdown(f"- OpenAI: {'✅' if OPENAI_KEY else '❌'}")
    st.markdown(f"- Anthropic: {'✅' if ANTHROPIC_KEY else '❌'}")
    st.markdown(f"- Groq: {'✅' if GROQ_KEY else '❌'}")
    
    st.divider()
    
    if st.button("🗑️ チャット履歴をクリア"):
        st.session_state.messages = []
        st.rerun()
    
    st.divider()
    
    # 点数窓（サイドバー）
    st.header("📊 クロスチェック結果")
    
    if "messages" in st.session_state and st.session_state.messages and len(st.session_state.messages) > 0:
        last_msg = st.session_state.messages[-1]
        if last_msg.get("role") == "assistant" and last_msg.get("crosscheck"):
            crosscheck = last_msg["crosscheck"]
            for check in crosscheck["checks"]:
                st.markdown(f"**{check['checker']}**")
                st.text_area("評価", check["evaluation"], height=200, disabled=True, key=check["checker"])
                st.divider()
        else:
            st.markdown("**👮‍♂️ 監査役**")
            st.info("待機中...")
            st.markdown("**🦙 データ役**")
            st.info("待機中...")
    else:
        st.markdown("**👮‍♂️ 監査役**")
        st.info("待機中...")
        st.markdown("**🦙 データ役**")
        st.info("待機中...")

# APIキーチェック
missing_keys = []
if not GEMINI_KEY: missing_keys.append("GEMINI_API_KEY")
if not OPENAI_KEY: missing_keys.append("OPENAI_API_KEY")
if not ANTHROPIC_KEY: missing_keys.append("ANTHROPIC_API_KEY")
if not GROQ_KEY: missing_keys.append("GROQ_API_KEY")

if missing_keys:
    st.error(f"❌ 以下のAPIキーが設定されていません: {', '.join(missing_keys)}")
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
    st.session_state.messages.append({"role": "user", "content": prompt, "avatar": "👤"})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)
    
    with st.chat_message("assistant", avatar="👑"):
        with st.spinner("🤔 Gemini司令塔が思考中..."):
            try:
                commander_response = call_commander(prompt, st.session_state.messages)
                agent_type, result, loop_data = process_command(commander_response, prompt, use_loop, use_crosscheck)
                
                agent_info = {
                    "auditor": "👮‍♂️ 監査役(GPT-5.2)",
                    "coder": "👨‍💻 コード役(Claude Sonnet 4.5)",
                    "coder_loop": "👨‍💻 コード役 + 👮‍♂️ 監査役（ループ）",
                    "data": "🦙 データ役(Llama 3.3 70B)",
                    "self": "👑 司令塔(Gemini 3 Pro)"
                }
                
                if agent_type != "self":
                    st.info(f"📋 {agent_info.get(agent_type, '不明')} に依頼しました")
                
                # ループ結果の詳細表示
                if loop_data and loop_data.get("loop_data"):
                    with st.expander(f"🔄 ループ詳細（{loop_data['loop_data']['total_iterations']}回）", expanded=False):
                        for item in loop_data["loop_data"]["iterations"]:
                            if item["type"] == "code":
                                st.markdown(f"**📝 コード生成 (v{item['iteration']})**")
                            elif item["type"] == "review":
                                st.markdown(f"**🔍 レビュー結果**")
                            elif item["type"] == "fix":
                                st.markdown(f"**🔧 修正版 (v{item['iteration']})**")
                            st.code(item["content"][:500] + "..." if len(item["content"]) > 500 else item["content"])
                            st.divider()
                

                
                st.markdown(result)
                
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": result,
                    "avatar": "👑",
                    "agent": agent_type,
                    "crosscheck": loop_data.get("crosscheck") if loop_data else None
                })
                
            except Exception as e:
                st.error(f"❌ エラー: {str(e)}")
                import traceback
                st.code(traceback.format_exc())
