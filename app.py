# app.py
# 行数: 185行
# Multi-Agent System メインUI（モジュール化版）

import streamlit as st
import uuid

# モジュールインポート
from config import (
    check_api_keys, GEMINI_KEY, OPENAI_KEY, ANTHROPIC_KEY, GROQ_KEY, XAI_KEY,
    AI_MODELS, DEFAULT_TEAM_CONFIG, get_team_config, set_team_config, reset_team_config
)
from agents import call_commander, call_auditor, call_coder, call_searcher, call_data_processor
from agents.coder_team import CoderTeam
from agents.auditor_team import AuditorTeam
from agents.data_team import DataTeam
from agents.searcher_team import SearcherTeam
from agents.concierge import ConciergeTeam as Concierge
from core import code_with_review_loop, cross_check, generate_crosscheck_summary
from failure_tracker import FailureTracker
from failure_analyzer import FailureAnalyzer
from learning_integrator import LearningSkillsIntegrator

from core.artifact_store import ArtifactStore
from ui.upload_panel import render_upload_panel
from ui.parts_panel import render_parts_panel
from ui.chat_uploader import render_chat_uploader, get_uploaded_files_for_prompt, clear_uploaded_files

# Mac操作連携
try:
    from integrations.firebase_mac import render_mac_control_panel, FIREBASE_AVAILABLE
except ImportError:
    FIREBASE_AVAILABLE = False
    def render_mac_control_panel():
        pass

# ==========================================
# Failure Tracking初期化
# ==========================================
@st.cache_resource
def get_failure_tracker():
    tracker = FailureTracker()
    return tracker

@st.cache_resource
def get_failure_analyzer():
    tracker = get_failure_tracker()
    return FailureAnalyzer(tracker)

@st.cache_resource
def get_learning_integrator():
    analyzer = get_failure_analyzer()
    return LearningSkillsIntegrator(analyzer)

@st.cache_resource
def get_artifact_store():
    return ArtifactStore(db_path="data/app.db")


# ==========================================
# ページ設定
# ==========================================
st.set_page_config(
    page_title="Multi-Agent System",
    page_icon="🤖",
    layout="wide"
)

# カスタムCSS（赤枠を緑枠に変更）

st.markdown(r'''
<style>
/* FORCE_WIDE_LAYOUT_V1 */
div[data-testid="stAppViewContainer"] {
  width: 100vw !important;
  max-width: 100vw !important;
  overflow-x: hidden !important;
}
div[data-testid="stAppViewContainer"] > div {
  width: 100% !important;
  max-width: 100vw !important;
}
section.main > div {
  max-width: 100vw !important;
}
div.block-container {
  max-width: 100vw !important;
  width: 100% !important;
  padding-left: 1.5rem !important;
  padding-right: 1.5rem !important;
}
div[data-testid="stBottomBlockContainer"],
div[data-testid="stBottomBlockContainer"] > div {
  width: 100% !important;
  max-width: 100vw !important;
}
div[data-testid="stChatInput"],
div[data-testid="stChatInput"] form,
div[data-testid="stChatInput"] [data-baseweb],
div[data-testid="stChatInput"] textarea {
  width: 100% !important;
  max-width: 100% !important;
  box-sizing: border-box !important;
  min-width: 0 !important;
}
div[data-testid="stChatInput"] {
  margin-left: 0 !important;
  margin-right: 0 !important;
}
</style>
''', unsafe_allow_html=True)


st.markdown("""
<style>
    /* ---- Fit safety: prevent horizontal overflow ---- */
    html, body {
        overflow-x: hidden !important;
    }
    div[data-testid="stChatInput"] {
        width: 100% !important;
        max-width: 100% !important;
        box-sizing: border-box !important;
    }
    div[data-testid="stChatInput"] * {
        box-sizing: border-box !important;
        min-width: 0 !important;
    }

    /* チャット入力欄全体 - 完全に上書き */
    div[data-testid="stChatInput"],
    div[data-testid="stChatInput"] > *,
    div[data-testid="stChatInput"] > * > *,
    div[data-testid="stChatInput"] > * > * > *,
    div[data-testid="stChatInput"] > * > * > * > *,
    div[data-testid="stChatInput"] div,
    div[data-testid="stChatInput"] form,
    div[data-testid="stChatInput"] textarea,
    div[data-testid="stChatInput"] [data-baseweb],
    div[data-testid="stChatInput"] [class*="st-"] {
        background: #0e1117 !important;
        background-color: #0e1117 !important;
    }
    
    div[data-testid="stChatInput"] {
        border: 2px solid #10b981 !important;
        border-radius: 26px !important;
        box-shadow: none !important;
        overflow: hidden !important;
        outline: none !important;
    }
    
    /* デフォルトの赤枠を完全に無効化 */
    div[data-testid="stChatInput"]::before,
    div[data-testid="stChatInput"]::after,
    div[data-testid="stChatInput"] *::before,
    div[data-testid="stChatInput"] *::after {
        display: none !important;
        border: none !important;
    }
    
    div[data-testid="stChatInput"] > div,
    div[data-testid="stChatInput"] form,
    div[data-testid="stChatInput"] [data-baseweb] {
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
    }
    
    /* 送信ボタンの背景 */
    div[data-testid="stChatInput"] button {
        background: #10b981 !important;
        background-color: #10b981 !important;
        border-radius: 50% !important;
    }
    
    /* フォーカス時 */
    div[data-testid="stChatInput"]:focus-within {
        border-color: #059669 !important;
        box-shadow: 0 0 0 1px #059669 !important;
    }
    
    /* テキストエリアのフォーカス時 */
    div[data-testid="stChatInput"] textarea:focus {
        outline: none !important;
        box-shadow: none !important;
    }
    
    /* クロスチェックカード */
    .crosscheck-card {
        background: #1e1e1e;
        border: 1px solid #374151;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 12px;
    }
    .crosscheck-card h4 {
        color: #10b981;
        margin: 0 0 8px 0;
        font-size: 0.9rem;
    }
    .crosscheck-score {
        font-size: 1.2rem;
        font-weight: bold;
    }
    .score-high { color: #10b981; }
    .score-mid { color: #f59e0b; }
    .score-low { color: #ef4444; }

    /* Fit safety: prevent horizontal overflow (parent containers too) */
    div[data-testid="stBottom"],
    div[data-testid="stBottomBlockContainer"],
    div[data-testid="stBottomBlockContainer"] > div,
    div[data-testid="stChatInput"] {
        width: 100% !important;
        max-width: 100% !important;
        box-sizing: border-box !important;
        min-width: 0 !important;
    }
    div[data-testid="stChatInput"] form,
    div[data-testid="stChatInput"] [data-baseweb],
    div[data-testid="stChatInput"] textarea,
    div[data-testid="stChatInput"] button {
        max-width: 100% !important;
        box-sizing: border-box !important;
        min-width: 0 !important;
    }

/* Fit safety: chat input hard clamp */
html, body {
    max-width: 100% !important;
    overflow-x: hidden !important;
}

div[data-testid="stAppViewContainer"],
div[data-testid="stMain"],
div[data-testid="stMainBlockContainer"] {
    max-width: 100% !important;
    overflow-x: hidden !important;
}

div[data-testid="stChatInput"] {
    width: 100% !important;
    max-width: 100% !important;
    box-sizing: border-box !important;
    min-width: 0 !important;
    margin-left: 0 !important;
    margin-right: 0 !important;
}

div[data-testid="stChatInput"] form {
    width: 100% !important;
    max-width: 100% !important;
    box-sizing: border-box !important;
    min-width: 0 !important;
}

div[data-testid="stChatInput"] textarea {
    width: 100% !important;
    max-width: 100% !important;
    box-sizing: border-box !important;
    min-width: 0 !important;
}

div[data-testid="stChatInput"] button {
    flex: 0 0 auto !important;
}


/* FIT_CHAT_INPUT_FORCE */
html, body {
  overflow-x: hidden !important;
}
div[data-testid="stAppViewContainer"],
div[data-testid="stMain"],
div[data-testid="stMainBlockContainer"],
div[data-testid="stVerticalBlock"],
div[data-testid="stVerticalBlockBorderWrapper"],
div[data-testid="stChatInput"] {
  max-width: 100vw !important;
  width: 100% !important;
  min-width: 0 !important;
  box-sizing: border-box !important;
  overflow-x: hidden !important;
}
/* BaseWeb: textarea wrapper */
div[data-testid="stChatInput"] [data-baseweb],
div[data-testid="stChatInput"] textarea {
  max-width: 100% !important;
  width: 100% !important;
  min-width: 0 !important;
  box-sizing: border-box !important;
}



/* FIT_FORCE_V1 */
html, body {
  width: 100% !important;
  max-width: 100vw !important;
  overflow-x: hidden !important;
  box-sizing: border-box !important;
}
*, *::before, *::after {
  box-sizing: border-box !important;
  min-width: 0 !important;
}
/* Streamlit containers */
div[data-testid="stAppViewContainer"],
div[data-testid="stAppViewContainer"] > div,
section[data-testid="stSidebar"] + div {
  max-width: 100vw !important;
  overflow-x: hidden !important;
}
/* Chat input area */
div[data-testid="stChatInput"],
div[data-testid="stChatInput"] > div {
  width: 100% !important;
  max-width: 100% !important;
  overflow-x: hidden !important;
}

</style>
""", unsafe_allow_html=True)

# ==========================================
# 処理の振り分け
# ==========================================
def process_command(commander_response: str, original_input: str, use_loop: bool, use_crosscheck: bool = True) -> tuple:
    """司令塔の指示を処理（3AI協働チーム対応版）"""
    agent_type = None
    result = None
    loop_data = None
    task = original_input
    execution_id = str(uuid.uuid4())
    tracker = get_failure_tracker()
    
    agent_role_map = {
        "auditor": "監査チーム",
        "coder": "コーディングチーム",
        "coder_loop": "コーディングチーム(ループ)",
        "data": "データ処理チーム",
        "searcher": "検索チーム"
    }
    
    try:
        if "[AUDITOR]" in commander_response:
            task = commander_response.split("[AUDITOR]")[-1].strip() or original_input
            agent_type = "auditor"
            # 3AI協働: AuditorTeam
            team = AuditorTeam()
            team_result = team.run(task)
            result = team_result["final_result"]
            loop_data = {"team_info": team_result.get("team"), "scores": team_result.get("scores")}
        
        elif "[CODER]" in commander_response:
            task = commander_response.split("[CODER]")[-1].strip() or original_input
            agent_type = "coder"
            # 3AI協働: CoderTeam
            team = CoderTeam()
            team_result = team.run(task)
            result = team_result["final_result"]
            loop_data = {"team_info": team_result.get("team"), "scores": team_result.get("scores")}
        
        elif "[DATA]" in commander_response:
            task = commander_response.split("[DATA]")[-1].strip() or original_input
            agent_type = "data"
            # 3AI協働: DataTeam
            team = DataTeam()
            team_result = team.run(task)
            result = team_result["final_result"]
            loop_data = {"team_info": team_result.get("team"), "scores": team_result.get("scores")}
        
        elif "[SEARCH]" in commander_response:
            task = commander_response.split("[SEARCH]")[-1].strip() or original_input
            agent_type = "searcher"
            # 3AI協働: SearcherTeam
            team = SearcherTeam()
            team_result = team.run(task)
            result = team_result["final_result"]
            loop_data = {"team_info": team_result.get("team"), "scores": team_result.get("scores")}
        
        else:
            clean_response = commander_response.replace("[SELF]", "").strip()
            return "self", clean_response, None
        
        # 成功を記録
        tracker.record_execution(
            execution_id=execution_id,
            agent_name=agent_role_map.get(agent_type, agent_type),
            role=agent_type,
            task_description=task[:200],
            status='success'
        )
        
        # クロスチェック実行（チームのscoresを使用）
        crosscheck_data = None
        if use_crosscheck and agent_type and loop_data:
            crosscheck_data = {
                "checks": loop_data.get("scores", []),
                "team": loop_data.get("team_info", {})
            }
            if crosscheck_data["checks"]:
                summary = generate_crosscheck_summary(crosscheck_data["checks"])
                crosscheck_data["summary"] = summary
        
        return agent_type, result, {"loop_data": loop_data, "crosscheck": crosscheck_data}
        
    except Exception as e:
        # 失敗を記録
        if agent_type:
            tracker.record_execution(
                execution_id=execution_id,
                agent_name=agent_role_map.get(agent_type, agent_type),
                role=agent_type,
                task_description=task[:200] if task else original_input[:200],
                status='failed',
                error_message=str(e),
                error_type=type(e).__name__
            )
        raise

# ==========================================
# UI
# ==========================================
# カスタムCSS（タイトルをコンパクトに）
st.markdown("""
<style>
    /* ---- Fit safety: prevent horizontal overflow ---- */
    html, body {
        overflow-x: hidden !important;
    }
    div[data-testid="stChatInput"] {
        width: 100% !important;
        max-width: 100% !important;
        box-sizing: border-box !important;
    }
    div[data-testid="stChatInput"] * {
        box-sizing: border-box !important;
        min-width: 0 !important;
    }

    /* タイトルエリアを小さく */
    h1 {
        font-size: 1.5rem !important;
        margin-top: 0 !important;
        margin-bottom: 0.5rem !important;
        padding-top: 0.5rem !important;
    }
    
    /* サブタイトルを小さく */
    .stMarkdown p {
        font-size: 0.8rem !important;
        margin-top: 0 !important;
        margin-bottom: 0.5rem !important;
        color: #9ca3af !important;
    }
</style>
""", unsafe_allow_html=True)

# 上部余白を削除するCSS
st.markdown("""
<style>
    /* ---- Fit safety: prevent horizontal overflow ---- */
    html, body {
        overflow-x: hidden !important;
    }
    div[data-testid="stChatInput"] {
        width: 100% !important;
        max-width: 100% !important;
        box-sizing: border-box !important;
    }
    div[data-testid="stChatInput"] * {
        box-sizing: border-box !important;
        min-width: 0 !important;
    }

    .block-container {
        padding-top: 0rem !important;
        margin-top: 0rem !important;
        padding-left: 1.5rem !important;
    }
    header[data-testid="stHeader"] {
        display: none !important;
    }
    /* サイドバー上部余白完全削除 */
    [data-testid="stSidebar"],
    [data-testid="stSidebar"] > div,
    [data-testid="stSidebar"] > div > div,
    [data-testid="stSidebar"] > div > div > div,
    [data-testid="stSidebarContent"],
    [data-testid="stSidebarUserContent"],
    section[data-testid="stSidebar"],
    section[data-testid="stSidebar"] > div {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    /* サイドバー内のブロック間隔 */
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
        gap: 0.5rem !important;
        padding-top: 0 !important;
    }
    /* サイドバー全体を上に移動 */
    section[data-testid="stSidebar"] > div {
        margin-top: -3rem !important;
        padding-top: 0 !important;
    }
    section[data-testid="stSidebar"] > div > div {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    section[data-testid="stSidebar"] > div > div > div {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
</style>
""", unsafe_allow_html=True)

# メインレイアウト: 左=クロスチェック結果, 右=チャット
col_crosscheck, col_chat = st.columns([1, 2])

# 左カラム: クロスチェック結果パネル
with col_crosscheck:
    st.markdown('<div style="font-size: 1.2rem; font-weight: bold; margin-top: -0.3rem; margin-bottom: 1rem;">📊 クロスチェック結果</div>', unsafe_allow_html=True)
    
    # セッションに保存されたクロスチェック結果を表示
    if "last_crosscheck" in st.session_state and st.session_state.last_crosscheck:
        crosscheck = st.session_state.last_crosscheck
        
        # 総合判定
        if "summary" in crosscheck:
            st.success(crosscheck["summary"])
        
        # 各AIの評価カード（横2列表示）
        checks = crosscheck.get("checks", [])
        for i in range(0, len(checks), 2):
            cols = st.columns(2)
            for j, col in enumerate(cols):
                if i + j < len(checks):
                    check = checks[i + j]
                    checker = check.get("checker", "不明")
                    evaluation = check.get("evaluation", "")
                    
                    # スコア抽出
                    import re
                    score_match = re.search(r'(\d{1,3})\s*[/点分]', evaluation)
                    score = int(score_match.group(1)) if score_match else None
                    
                    if score is not None:
                        if score >= 80:
                            score_color = "#10b981"
                        elif score >= 60:
                            score_color = "#f59e0b"
                        else:
                            score_color = "#ef4444"
                        score_display = f'<span style="color:{score_color};font-size:1.1rem;font-weight:bold;">{score}点</span>'
                    else:
                        score_display = "-"
                    
                    with col:
                        st.markdown(f"""
                        <div class="crosscheck-card">
                            <h4>{checker}</h4>
                            <div>採点: {score_display}</div>
                            <div style="font-size:0.8rem;color:#9ca3af;margin-top:6px;white-space:pre-wrap;max-height:120px;overflow-y:auto;">{evaluation[:150]}{'...' if len(evaluation) > 150 else ''}</div>
                        </div>
                        """, unsafe_allow_html=True)
    else:
        st.info("待機中... メッセージを送信するとクロスチェック結果が表示されます")

# 右カラム: チャットエリア
with col_chat:
    st.markdown("""
    <div style="display: flex; justify-content: flex-start; align-items: center; gap: 0.5rem; margin-bottom: 1rem; flex-wrap: wrap;">
        <span style="font-size: 1.5rem;">🤖</span>
        <div>
            <div style="font-size: 1.2rem; font-weight: bold; line-height: 1.2;">Multi-Agent System</div>
            <div style="font-size: 0.7rem; color: #6b7280;">2026年1月版 - モジュール化 + 5AI協働システム</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# 添付（アップロード）用
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = str(uuid.uuid4())
artifact_store = get_artifact_store()

# サイドバー
with st.sidebar:
    st.header("👥 エージェントチーム")
    
    # AI選択肢
    ai_options = list(AI_MODELS.keys())
    ai_names = {k: v["name"] for k, v in AI_MODELS.items()}
    
    # チーム編成UI
    with st.expander("🔧 チーム編成（クリックで開く）", expanded=False):
        # デフォルトに戻すボタン
        if st.button("🔄 デフォルトに戻す", use_container_width=True):
            reset_team_config()
            st.rerun()
        
        for team_key, team_default in DEFAULT_TEAM_CONFIG.items():
            st.markdown(f"**{team_default['name']}**")
            current = get_team_config(team_key)
            
            leader = st.selectbox(
                "👑 長",
                ai_options,
                index=ai_options.index(current["leader"]),
                key=f"{team_key}_leader",
                format_func=lambda x: ai_names[x]
            )
            creator = st.selectbox(
                "🔨 作成役",
                ai_options,
                index=ai_options.index(current["creator"]),
                key=f"{team_key}_creator",
                format_func=lambda x: ai_names[x]
            )
            checker = st.selectbox(
                "🔍 チェック役",
                ai_options,
                index=ai_options.index(current["checker"]),
                key=f"{team_key}_checker",
                format_func=lambda x: ai_names[x]
            )
            
            # 変更があれば保存
            if leader != current["leader"] or creator != current["creator"] or checker != current["checker"]:
                set_team_config(team_key, leader, creator, checker)
            
            st.divider()
    
    # 現在のチーム構成表示
    st.caption("現在のチーム構成")
    for team_key in DEFAULT_TEAM_CONFIG.keys():
        cfg = get_team_config(team_key)
        st.markdown(f"**{cfg['name']}**: {ai_names.get(cfg['leader'], cfg['leader'])}（長）")
    
    st.divider()
    
    st.header("⚙️ 設定")
    use_loop = st.toggle("🔄 コードレビューループ", value=True, help="ONにするとコード生成後に自動でGPTがレビューし、問題があればClaudeが修正します")
    max_loop = st.slider("最大ループ回数", 1, 5, 3) if use_loop else 1
    use_crosscheck = st.toggle("📊 クロスチェック機能", value=False, help="ONにすると全AIが結果を採点（重要なタスク時のみ推奨）")
    
    st.divider()
    
    st.header("🔑 APIキー状態")
    st.markdown(f"- Gemini: {'✅' if GEMINI_KEY else '❌'}")
    st.markdown(f"- OpenAI: {'✅' if OPENAI_KEY else '❌'}")
    st.markdown(f"- Anthropic: {'✅' if ANTHROPIC_KEY else '❌'}")
    st.markdown(f"- Groq: {'✅' if GROQ_KEY else '❌'}")
    st.markdown(f"- xAI (Grok): {'✅' if XAI_KEY else '❌'}")
    
    st.divider()
    # 添付（アップロード）
    try:
        render_upload_panel(artifact_store, st.session_state.conversation_id)
    except Exception as e:
        st.caption("添付パネル準備中...")

    st.divider()
    
    # 作業パーツ管理パネル
    try:
        render_parts_panel()
    except Exception as e:
        st.caption(f"パーツパネル準備中... {e}")
    
    # 失敗透明性レポート
    st.header("📊 システム透明性")
    try:
        tracker = get_failure_tracker()
        stats_24h = tracker.get_failure_rate(24)
        stats_7d = tracker.get_failure_rate(168)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("24時間失敗率", f"{stats_24h['failure_rate']}%")
        with col2:
            st.metric("7日間失敗率", f"{stats_7d['failure_rate']}%")
        
        st.caption(f"総実行回数（24時間）: {stats_24h['total_executions']}回")
        
        if stats_24h['total_executions'] > 0:
            analyzer = get_failure_analyzer()
            top_failures = analyzer.get_top_failure_reasons(3)
            if top_failures:
                st.write("**主な失敗:**")
                for f in top_failures:
                    st.text(f"• {f['error_type']}: {f['occurrence_count']}回")
    except Exception as e:
        st.caption("データ準備中...")
    
    st.divider()
    
    # Skills Server連携
    st.header("📚 Skills管理")
    st.markdown("[🔗 Skills Serverで管理](https://skills-server-a34a4.web.app/)")
    st.caption("スキルのアップロード・検索はSkills Serverで行ってください")
    
    st.divider()
    
    # Mac操作パネル
    try:
        render_mac_control_panel()
    except Exception as e:
        st.caption(f"Mac操作パネル準備中... {e}")
    


# APIキーチェック
missing_keys = check_api_keys()
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

# チャット用ファイルアップロードUI（入力欄の上に配置）
render_chat_uploader()

# ユーザー入力
if prompt := st.chat_input("メッセージを入力してください..."):
    # アップロードファイルの内容をプロンプトに追加
    file_context = get_uploaded_files_for_prompt()
    full_prompt = prompt + file_context if file_context else prompt
    
    st.session_state.messages.append({"role": "user", "content": prompt, "avatar": "👤"})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)
        # 添付ファイル表示
        if file_context:
            files = st.session_state.get('chat_uploaded_files', [])
            st.caption(f"📎 {len(files)}個のファイルを添付")
    
    with st.chat_message("assistant", avatar="👑"):
        with st.spinner("🤔 Gemini司令塔が思考中..."):
            try:
                # AIにはファイル内容込みのfull_promptを送信
                commander_response = call_commander(full_prompt, st.session_state.messages)
                agent_type, result, loop_data = process_command(commander_response, prompt, use_loop, use_crosscheck)
                
                agent_info = {
                    "auditor": "👮‍♂️ 監査チーム（3AI協働）",
                    "coder": "👨‍💻 コーディングチーム（3AI協働）",
                    "coder_loop": "👨‍💻 コーディングチーム（3AI協働）",
                    "data": "🦙 データ処理チーム（3AI協働）",
                    "searcher": "🔍 検索チーム（3AI協働）",
                    "self": "👑 司令塔(Gemini 3 Pro)"
                }
                
                if agent_type != "self":
                    st.info(f"📋 {agent_info.get(agent_type, '不明')} に依頼しました")
                    
                    # チーム詳細表示
                    if loop_data and loop_data.get("team_info"):
                        team_info = loop_data["team_info"]
                        with st.expander("👥 チーム構成", expanded=False):
                            st.markdown(f"""
                            - **👑 長**: {team_info.get('leader', '-')}
                            - **🔨 作成役**: {team_info.get('creator', '-')}
                            - **🔍 チェック役**: {team_info.get('checker', '-')}
                            """)
                            
                            # チェック役の評価
                            if loop_data.get("scores"):
                                st.markdown("**チェック役の評価:**")
                                for score in loop_data["scores"]:
                                    st.markdown(f"- {score.get('checker', '-')}: {score.get('evaluation', '-')[:200]}...")
                
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
                
                # クロスチェック結果をセッション状態に保存
                need_rerun = False
                if loop_data and loop_data.get("crosscheck"):
                    st.session_state.last_crosscheck = loop_data["crosscheck"]
                    need_rerun = True
                
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": result,
                    "avatar": "👑",
                    "agent": agent_type,
                    "crosscheck": loop_data.get("crosscheck") if loop_data else None
                })
                
                # 送信完了後、アップロードファイルをクリア
                clear_uploaded_files()
                
                if need_rerun:
                    st.rerun()
                
            except Exception as e:
                st.error(f"❌ エラー: {str(e)}")
                import traceback
                st.code(traceback.format_exc())


# --- injected: WIDTH_FIX_V2 (final override; keep at end) ---
import streamlit as st
st.markdown(r"""
<style>
/* WIDTH_FIX_V2 */
html, body { width: 100% !important; max-width: 100% !important; overflow-x: hidden !important; }
*, *::before, *::after { box-sizing: border-box !important; min-width: 0 !important; }

/* Streamlit main containers: never exceed viewport width */
div[data-testid="stAppViewContainer"],
div[data-testid="stAppViewContainer"] > div,
div[data-testid="stMain"],
div[data-testid="stMainBlockContainer"],
div[data-testid="stVerticalBlock"],
div[data-testid="stVerticalBlockBorderWrapper"],
section[data-testid="stSidebar"] + div {
  width: 100% !important;
  max-width: 100% !important;
  overflow-x: hidden !important;
}

/* Streamlit block container: add right padding too (prevents right-edge clip) */
.block-container {
  width: 100% !important;
  max-width: 100% !important;
  padding-left: 1.5rem !important;
  padding-right: 1.5rem !important;
}

/* Bottom + chat input: clamp to parent width */
div[data-testid="stBottom"],
div[data-testid="stBottomBlockContainer"],
div[data-testid="stBottomBlockContainer"] > div,
div[data-testid="stChatInput"],
div[data-testid="stChatInput"] > div,
div[data-testid="stChatInput"] form,
div[data-testid="stChatInput"] [data-baseweb],
div[data-testid="stChatInput"] textarea,
div[data-testid="stChatInput"] button {
  width: 100% !important;
  max-width: 100% !important;
  min-width: 0 !important;
}

/* Ensure button doesn't force overflow */
div[data-testid="stChatInput"] button { flex: 0 0 auto !important; }
</style>
""", unsafe_allow_html=True)
# --- injected: WIDTH_FIX_V2 (final override; keep at end) ---

