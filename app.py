# app.py
# Multi-Agent System メインUI（タブ機能付き）

import streamlit as st
import uuid
import re

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
from ui.tabs import render_tab_bar, get_active_tab_type, get_tab_data, init_tabs
from ui.todo_panel import render_todo_panel
from ui.conversation_history import render_conversation_history, render_history_detail
from ui.file_history_panel import render_file_history_panel, render_version_detail

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
    return FailureTracker()

@st.cache_resource
def get_failure_analyzer():
    return FailureAnalyzer(get_failure_tracker())

@st.cache_resource
def get_learning_integrator():
    return LearningSkillsIntegrator(get_failure_analyzer())

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

# ==========================================
# CSS
# ==========================================
st.markdown(r'''
<style>
/* レイアウト */
div[data-testid="stAppViewContainer"] { width: 100vw !important; max-width: 100vw !important; overflow-x: hidden !important; }
div.block-container { max-width: 100vw !important; width: 100% !important; padding-left: 1.5rem !important; padding-right: 1.5rem !important; padding-top: 0.5rem !important; margin-top: 0 !important; }
header[data-testid="stHeader"] { display: none !important; }

/* チャット入力欄 */
div[data-testid="stChatInput"] { border: 2px solid #10b981 !important; border-radius: 26px !important; background: #0e1117 !important; }
div[data-testid="stChatInput"]:focus-within { border-color: #059669 !important; box-shadow: 0 0 0 1px #059669 !important; }
div[data-testid="stChatInput"] button { background: #10b981 !important; border-radius: 50% !important; }
div[data-testid="stChatInput"], div[data-testid="stChatInput"] form, div[data-testid="stChatInput"] textarea { width: 100% !important; max-width: 100% !important; box-sizing: border-box !important; }
div[data-testid="stChatInput"] textarea { font-size: 0.9rem !important; }
div[data-testid="stChatInput"] textarea::placeholder { font-size: 0.9rem !important; }

/* タブボタンの改行禁止 */
[data-testid="stButton"] button { white-space: nowrap !important; }

/* ファイルアップロードエリア */
[data-testid="stFileUploader"] { text-align: center !important; }
[data-testid="stFileUploader"] section { display: flex !important; flex-direction: column !important; align-items: center !important; justify-content: center !important; }
[data-testid="stFileUploader"] section > div { text-align: center !important; }
[data-testid="stFileUploader"] small { display: block !important; text-align: center !important; }
[data-testid="stFileUploader"] button { margin: 0 auto !important; display: block !important; }

/* 左右カラムの区切り線 */
.main-columns > div:first-child {
    border-right: 1px solid #374151 !important;
    padding-right: 1rem !important;
}
.main-columns > div:last-child {
    padding-left: 1rem !important;
}

/* クロスチェック折りたたみ */
.crosscheck-expander { background: #1e293b; border: 1px solid #374151; border-radius: 8px; padding: 8px 12px; margin-top: 8px; }
.crosscheck-card { background: #0f172a; border: 1px solid #334155; border-radius: 6px; padding: 10px; margin: 6px 0; }
.crosscheck-card h4 { color: #10b981; margin: 0 0 6px 0; font-size: 0.85rem; }

/* サイドバー */
section[data-testid="stSidebar"] { overflow: visible !important; }
section[data-testid="stSidebar"] > div { 
    margin-top: -3rem !important; 
    padding-top: 0 !important; 
    height: 100vh !important;
    overflow-y: scroll !important;
    scrollbar-width: thin !important;
    scrollbar-color: #10b981 #1e293b !important;
}
section[data-testid="stSidebar"] > div::-webkit-scrollbar { 
    width: 10px !important; 
    display: block !important;
}
section[data-testid="stSidebar"] > div::-webkit-scrollbar-track { 
    background: #1e293b !important; 
}
section[data-testid="stSidebar"] > div::-webkit-scrollbar-thumb { 
    background: #10b981 !important; 
    border-radius: 5px !important; 
}
section[data-testid="stSidebar"] > div::-webkit-scrollbar-thumb:hover { 
    background: #059669 !important; 
}

/* 💬 会話履歴スタイル */
.stButton > button[key*="history_"] {
    background: #1e293b !important;
    border: 1px solid #334155 !important;
    padding: 0.5rem !important;
    text-align: left !important;
    font-size: 0.85rem !important;
    transition: all 0.2s !important;
}
.stButton > button[key*="history_"]:hover {
    background: #334155 !important;
    border-color: #10b981 !important;
    transform: translateX(4px) !important;
}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] { gap: 0.5rem !important; }

/* 設定カード */
.settings-card { background: #1e293b; border: 1px solid #374151; border-radius: 8px; padding: 16px; margin-bottom: 16px; }
.settings-card h3 { color: #10b981; margin: 0 0 12px 0; font-size: 1.1rem; }
</style>
''', unsafe_allow_html=True)

# ==========================================
# クロスチェック結果表示（折りたたみ）
# ==========================================
def render_crosscheck_expander(crosscheck_data):
    """クロスチェック結果を折りたたみで表示"""
    if not crosscheck_data:
        return
    
    with st.expander("📊 クロスチェック結果", expanded=False):
        if "summary" in crosscheck_data:
            st.success(crosscheck_data["summary"])
        
        checks = crosscheck_data.get("checks", [])
        if checks:
            cols = st.columns(min(len(checks), 3))
            for i, check in enumerate(checks):
                with cols[i % 3]:
                    checker = check.get("checker", "不明")
                    evaluation = check.get("evaluation", "")
                    score_match = re.search(r'(\d{1,3})\s*[/点分]', evaluation)
                    score = int(score_match.group(1)) if score_match else None
                    
                    if score is not None:
                        score_color = "#10b981" if score >= 80 else "#f59e0b" if score >= 60 else "#ef4444"
                        score_display = f'<span style="color:{score_color};font-weight:bold;">{score}点</span>'
                    else:
                        score_display = "-"
                    
                    st.markdown(f'''
                    <div class="crosscheck-card">
                        <h4>{checker}</h4>
                        <div>採点: {score_display}</div>
                        <div style="font-size:0.8rem;color:#9ca3af;margin-top:4px;">{evaluation[:100]}...</div>
                    </div>
                    ''', unsafe_allow_html=True)

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
        "data": "データ処理チーム",
        "searcher": "検索チーム"
    }
    
    try:
        if "[AUDITOR]" in commander_response:
            task = commander_response.split("[AUDITOR]")[-1].strip() or original_input
            agent_type = "auditor"
            team = AuditorTeam()
            team_result = team.run(task)
            result = team_result["final_result"]
            loop_data = {"team_info": team_result.get("team"), "scores": team_result.get("scores")}
        
        elif "[CODER]" in commander_response:
            task = commander_response.split("[CODER]")[-1].strip() or original_input
            agent_type = "coder"
            team = CoderTeam()
            team_result = team.run(task)
            result = team_result["final_result"]
            loop_data = {"team_info": team_result.get("team"), "scores": team_result.get("scores")}
        
        elif "[DATA]" in commander_response:
            task = commander_response.split("[DATA]")[-1].strip() or original_input
            agent_type = "data"
            team = DataTeam()
            team_result = team.run(task)
            result = team_result["final_result"]
            loop_data = {"team_info": team_result.get("team"), "scores": team_result.get("scores")}
        
        elif "[SEARCH]" in commander_response:
            task = commander_response.split("[SEARCH]")[-1].strip() or original_input
            agent_type = "searcher"
            team = SearcherTeam()
            team_result = team.run(task)
            result = team_result["final_result"]
            loop_data = {"team_info": team_result.get("team"), "scores": team_result.get("scores")}
        
        else:
            clean_response = commander_response.replace("[SELF]", "").strip()
            return "self", clean_response, None
        
        tracker.record_execution(
            execution_id=execution_id,
            agent_name=agent_role_map.get(agent_type, agent_type),
            role=agent_type,
            task_description=task[:200],
            status='success'
        )
        
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
# セッション状態初期化
# ==========================================
if "use_loop" not in st.session_state:
    st.session_state.use_loop = True
if "use_crosscheck" not in st.session_state:
    st.session_state.use_crosscheck = False
if "max_loop" not in st.session_state:
    st.session_state.max_loop = 3
if "response_style" not in st.session_state:
    st.session_state.response_style = "詳細"
if "auto_save" not in st.session_state:
    st.session_state.auto_save = True
if "skills_user_id" not in st.session_state:
    st.session_state.skills_user_id = ""
if "display_name" not in st.session_state:
    st.session_state.display_name = ""
if "user_email" not in st.session_state:
    st.session_state.user_email = ""
if "gdrive_connected" not in st.session_state:
    st.session_state.gdrive_connected = False
if "slack_connected" not in st.session_state:
    st.session_state.slack_connected = False
if "github_connected" not in st.session_state:
    st.session_state.github_connected = False
if "share_tabs" not in st.session_state:
    st.session_state.share_tabs = False
if "share_team_config" not in st.session_state:
    st.session_state.share_team_config = False
if "history_visibility" not in st.session_state:
    st.session_state.history_visibility = "自分のみ"

# ==========================================
# タブ初期化
# ==========================================
init_tabs()
active_tab = render_tab_bar()
active_tab_type = get_active_tab_type()
tab_data = get_tab_data(active_tab)

# ==========================================
# サイドバー
# ==========================================
with st.sidebar:
    # 💬 会話履歴（最上部に配置）
    render_conversation_history()
    
    st.divider()
    
    st.header("👥 エージェントチーム")
    ai_options = list(AI_MODELS.keys())
    ai_names = {k: v["name"] for k, v in AI_MODELS.items()}
    
    with st.expander("🔧 チーム編成", expanded=False):
        if st.button("🔄 デフォルトに戻す", use_container_width=True):
            reset_team_config()
            st.rerun()
        
        for team_key, team_default in DEFAULT_TEAM_CONFIG.items():
            st.markdown(f"**{team_default['name']}**")
            current = get_team_config(team_key)
            
            leader = st.selectbox("👑 長", ai_options, index=ai_options.index(current["leader"]), key=f"{team_key}_leader", format_func=lambda x: ai_names[x])
            creator = st.selectbox("🔨 作成役", ai_options, index=ai_options.index(current["creator"]), key=f"{team_key}_creator", format_func=lambda x: ai_names[x])
            checker = st.selectbox("🔍 チェック役", ai_options, index=ai_options.index(current["checker"]), key=f"{team_key}_checker", format_func=lambda x: ai_names[x])
            
            if leader != current["leader"] or creator != current["creator"] or checker != current["checker"]:
                set_team_config(team_key, leader, creator, checker)
            st.divider()
    
    st.caption("現在のチーム構成")
    
    # チーム構成をシンプルな表形式で表示
    import pandas as pd
    team_data = []
    for team_key in DEFAULT_TEAM_CONFIG.keys():
        cfg = get_team_config(team_key)
        team_name = cfg['name'].replace('チーム', '').strip()
        leader_name = ai_names.get(cfg['leader'], cfg['leader'])
        team_data.append({'チーム': team_name, 'リーダー': leader_name})
    
    team_df = pd.DataFrame(team_data)
    st.table(team_df)
    
    # チーム評価スコア表示
    st.caption("🏆 チーム評価（30日間）")
    try:
        from team_evaluator import get_evaluation_manager
        eval_manager = get_evaluation_manager()
        all_teams = eval_manager.get_all_teams_comparison(days=30)
        
        # 評価データを辞書化
        team_scores = {}
        if all_teams:
            for team in all_teams:
                team_scores[team['team_key']] = {
                    'score': team.get('avg_quality_score'),
                    'success': team.get('success_rate', 0)
                }
        
        # 全チームの評価テーブルを作成
        score_data = []
        for team_key in DEFAULT_TEAM_CONFIG.keys():
            cfg = get_team_config(team_key)
            team_name = cfg['name'].replace('チーム', '').strip()
            
            if team_key in team_scores:
                score = team_scores[team_key]['score']
                success = team_scores[team_key]['success']
                score_text = f"{score:.0f}点" if score else "-"
                success_text = f"{success:.0f}%"
            else:
                score_text = "-"
                success_text = "-"
            
            score_data.append({
                'チーム': team_name,
                '品質': score_text,
                '成功率': success_text
            })
        
        score_df = pd.DataFrame(score_data)
        st.table(score_df)
    except Exception as e:
        # エラー時も初期テーブルを表示
        score_data = []
        for team_key in DEFAULT_TEAM_CONFIG.keys():
            cfg = get_team_config(team_key)
            team_name = cfg['name'].replace('チーム', '').strip()
            score_data.append({'チーム': team_name, '品質': '-', '成功率': '-'})
        score_df = pd.DataFrame(score_data)
        st.table(score_df)
    
    st.divider()
    
    # ⚙️ 設定セクション
    if st.button("⚙️ 設定を開く", key="sidebar_open_settings", use_container_width=True):
        from ui.tabs import add_tab
        add_tab("settings")
        st.rerun()
    
    # 簡易設定トグル
    st.markdown("🔄 **コードレビューループ**")
    use_loop = st.toggle("ループ", value=st.session_state.use_loop, key="sidebar_use_loop", label_visibility="collapsed")
    st.session_state.use_loop = use_loop
    if use_loop:
        max_loop = st.slider("最大ループ回数", 1, 5, st.session_state.max_loop, key="sidebar_max_loop")
        st.session_state.max_loop = max_loop
    
    st.markdown("📊 **クロスチェック機能**")
    use_crosscheck = st.toggle("クロスチェック", value=st.session_state.use_crosscheck, key="sidebar_use_crosscheck", label_visibility="collapsed")
    st.session_state.use_crosscheck = use_crosscheck
    
    st.divider()
    
    st.header("🔑 APIキー状態")
    st.markdown(f"- Gemini: {'✅' if GEMINI_KEY else '❌'}")
    st.markdown(f"- OpenAI: {'✅' if OPENAI_KEY else '❌'}")
    st.markdown(f"- Anthropic: {'✅' if ANTHROPIC_KEY else '❌'}")
    st.markdown(f"- Groq: {'✅' if GROQ_KEY else '❌'}")
    st.markdown(f"- xAI: {'✅' if XAI_KEY else '❌'}")
    
    st.divider()
    
    artifact_store = get_artifact_store()
    if "conversation_id" not in st.session_state:
        st.session_state.conversation_id = str(uuid.uuid4())
    
    try:
        render_upload_panel(artifact_store, st.session_state.conversation_id)
    except:
        st.caption("添付パネル準備中...")
    
    st.divider()
    
    try:
        render_parts_panel()
    except:
        st.caption("パーツパネル準備中...")
    
    st.divider()
    
    # 📂 ファイル履歴パネル
    try:
        render_file_history_panel()
    except:
        st.caption("ファイル履歴準備中...")
    
    st.divider()
    
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
    except:
        st.caption("データ準備中...")
    
    st.divider()
    
    st.header("📚 Skills管理")
    st.markdown("[🔗 Skills Serverで管理](https://skills-server-a34a4.web.app/)")
    
    st.divider()
    
    # ToDo簡易表示（追加・削除機能付き）
    st.header("✅ ToDo")
    try:
        # ローカルセッションでToDo管理
        if "todos" not in st.session_state:
            st.session_state.todos = []
        
        todos = st.session_state.todos
        incomplete = [t for t in todos if not t.get("completed")]
        
        # 追加フォーム
        new_todo = st.text_input("新しいタスク", key="sidebar_new_todo", placeholder="タスクを入力...", label_visibility="collapsed")
        if st.button("➕ 追加", key="sidebar_add_todo", use_container_width=True):
            if new_todo.strip():
                import uuid
                from datetime import datetime
                todo = {
                    "text": new_todo.strip(),
                    "completed": False,
                    "created_at": datetime.now().isoformat(),
                    "id": uuid.uuid4().hex
                }
                st.session_state.todos.append(todo)
                st.rerun()
        
        # タスク一覧（チェックボックス付き）
        if incomplete:
            for todo in incomplete[:5]:
                todo_col1, todo_col2 = st.columns([4, 1])
                with todo_col1:
                    if st.checkbox(f"{todo['text'][:18]}{'...' if len(todo['text']) > 18 else ''}", key=f"sidebar_todo_{todo['id']}", value=False):
                        todo["completed"] = True
                        st.rerun()
                with todo_col2:
                    if st.button("🗑", key=f"sidebar_del_{todo['id']}"):
                        st.session_state.todos = [t for t in st.session_state.todos if t["id"] != todo["id"]]
                        st.rerun()
            if len(incomplete) > 5:
                st.caption(f"他 {len(incomplete) - 5}件...")
        else:
            st.caption("タスクなし")
        st.caption(f"進捗: {len(todos) - len(incomplete)}/{len(todos)} 完了")
    except Exception as e:
        st.caption(f"ToDo: {e}")
    
    st.divider()
    
    try:
        render_mac_control_panel()
    except:
        st.caption("Mac操作パネル準備中...")

# ==========================================
# タブ別コンテンツ
# ==========================================
if active_tab_type == "settings":
    # 設定タブ
    st.markdown('<div style="font-size: 1.5rem; font-weight: bold; margin-bottom: 1rem;">⚙️ 設定</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 1. AIカスタム設定
        st.subheader("🤖 AIカスタム設定")
        
        st.markdown("🔄 **コードレビューループ**")
        use_loop = st.toggle("ループ有効", value=st.session_state.use_loop, key="settings_use_loop", label_visibility="collapsed")
        st.session_state.use_loop = use_loop
        
        if use_loop:
            max_loop = st.slider("最大ループ回数", 1, 5, st.session_state.max_loop, key="settings_max_loop")
            st.session_state.max_loop = max_loop
        
        st.markdown("📊 **クロスチェック機能**")
        use_crosscheck = st.toggle("クロスチェック有効", value=st.session_state.use_crosscheck, key="settings_use_crosscheck", label_visibility="collapsed")
        st.session_state.use_crosscheck = use_crosscheck
        
        response_style = st.selectbox("💬 デフォルト応答スタイル", ["簡潔", "詳細"], index=0 if st.session_state.response_style == "簡潔" else 1, key="settings_response_style")
        st.session_state.response_style = response_style
        
        st.markdown("💾 **自動保存**")
        auto_save = st.toggle("自動保存有効", value=st.session_state.auto_save, key="settings_auto_save", label_visibility="collapsed")
        st.session_state.auto_save = auto_save
        
        st.divider()
        
        # 2. アカウント設定
        st.subheader("👤 アカウント設定")
        
        skills_user_id = st.text_input("Skills User ID", value=st.session_state.skills_user_id, key="settings_skills_user_id", help="Skills Serverで取得したユーザーID")
        st.session_state.skills_user_id = skills_user_id
        
        display_name = st.text_input("表示名", value=st.session_state.display_name, key="settings_display_name")
        st.session_state.display_name = display_name
        
        user_email = st.text_input("メールアドレス", value=st.session_state.user_email, key="settings_user_email")
        st.session_state.user_email = user_email
        
        if st.button("🔐 パスワード変更", use_container_width=True):
            st.info("パスワード変更機能は準備中です")
        
        st.divider()
        
        # 3. チーム編成
        st.subheader("👥 チーム編成")
        if st.button("🔄 デフォルトに戻す", key="settings_reset", use_container_width=True):
            reset_team_config()
            st.rerun()
        
        for team_key, team_default in DEFAULT_TEAM_CONFIG.items():
            with st.expander(f"**{team_default['name']}**", expanded=False):
                current = get_team_config(team_key)
                leader = st.selectbox("👑 長", ai_options, index=ai_options.index(current["leader"]), key=f"settings_{team_key}_leader", format_func=lambda x: ai_names[x])
                creator = st.selectbox("🔨 作成役", ai_options, index=ai_options.index(current["creator"]), key=f"settings_{team_key}_creator", format_func=lambda x: ai_names[x])
                checker = st.selectbox("🔍 チェック役", ai_options, index=ai_options.index(current["checker"]), key=f"settings_{team_key}_checker", format_func=lambda x: ai_names[x])
                if leader != current["leader"] or creator != current["creator"] or checker != current["checker"]:
                    set_team_config(team_key, leader, creator, checker)
    
    with col2:
        # 4. サービス連携
        st.subheader("🔗 サービス連携")
        
        st.markdown("**Google Drive**")
        gdrive_col1, gdrive_col2 = st.columns([3, 1])
        with gdrive_col1:
            st.markdown(f"状態: {'🟢 接続済み' if st.session_state.gdrive_connected else '🔴 未接続'}")
        with gdrive_col2:
            if st.button("接続" if not st.session_state.gdrive_connected else "解除", key="gdrive_btn"):
                st.session_state.gdrive_connected = not st.session_state.gdrive_connected
                st.rerun()
        
        st.markdown("**Slack**")
        slack_col1, slack_col2 = st.columns([3, 1])
        with slack_col1:
            st.markdown(f"状態: {'🟢 接続済み' if st.session_state.slack_connected else '🔴 未接続'}")
        with slack_col2:
            if st.button("接続" if not st.session_state.slack_connected else "解除", key="slack_btn"):
                st.session_state.slack_connected = not st.session_state.slack_connected
                st.rerun()
        
        st.markdown("**GitHub**")
        github_col1, github_col2 = st.columns([3, 1])
        with github_col1:
            st.markdown(f"状態: {'🟢 接続済み' if st.session_state.github_connected else '🔴 未接続'}")
        with github_col2:
            if st.button("接続" if not st.session_state.github_connected else "解除", key="github_btn"):
                st.session_state.github_connected = not st.session_state.github_connected
                st.rerun()
        
        st.markdown("**Skills Server**")
        st.markdown("[🔗 Skills Serverで管理](https://skills-server-a34a4.web.app/)")
        
        st.divider()
        
        # 5. 共有設定
        st.subheader("🌐 共有設定")
        
        st.markdown("📁 **作業タブの共有を許可**")
        share_tabs = st.toggle("作業タブ共有", value=st.session_state.share_tabs, key="settings_share_tabs", label_visibility="collapsed")
        st.session_state.share_tabs = share_tabs
        
        st.markdown("👥 **チーム編成の共有**")
        share_team_config = st.toggle("チーム共有", value=st.session_state.share_team_config, key="settings_share_team", label_visibility="collapsed")
        st.session_state.share_team_config = share_team_config
        
        history_visibility = st.selectbox("履歴の公開範囲", ["自分のみ", "チームメンバー", "全員"], index=["自分のみ", "チームメンバー", "全員"].index(st.session_state.history_visibility), key="settings_history_visibility")
        st.session_state.history_visibility = history_visibility
        
        st.divider()
        
        # 6. システム情報
        st.subheader("🔑 システム情報")
        
        st.markdown("**APIキー状態**")
        st.markdown(f"- Gemini: {'✅' if GEMINI_KEY else '❌'}")
        st.markdown(f"- OpenAI: {'✅' if OPENAI_KEY else '❌'}")
        st.markdown(f"- Anthropic: {'✅' if ANTHROPIC_KEY else '❌'}")
        st.markdown(f"- Groq: {'✅' if GROQ_KEY else '❌'}")
        st.markdown(f"- xAI: {'✅' if XAI_KEY else '❌'}")
        
        st.divider()
        
        st.markdown("**システム透明性**")
        try:
            tracker = get_failure_tracker()
            stats_24h = tracker.get_failure_rate(24)
            stats_7d = tracker.get_failure_rate(168)
            m1, m2 = st.columns(2)
            with m1:
                st.metric("24時間失敗率", f"{stats_24h['failure_rate']}%")
            with m2:
                st.metric("7日間失敗率", f"{stats_7d['failure_rate']}%")
            st.caption(f"総実行回数（24時間）: {stats_24h['total_executions']}回")
        except:
            st.caption("データ準備中...")
        
        st.divider()
        
        # 7. チーム評価システム
        st.subheader("🏆 チーム評価")
        
        try:
            from team_evaluator import get_evaluation_manager
            eval_manager = get_evaluation_manager()
            
            # 履歴ベースの統計表示
            st.markdown("**📊 チーム別パフォーマンス（30日間）**")
            all_teams = eval_manager.get_all_teams_comparison(days=30)
            
            if all_teams:
                for team in all_teams[:5]:
                    score = team.get('avg_quality_score')
                    score_color = "#10b981" if score and score >= 80 else "#f59e0b" if score and score >= 60 else "#ef4444"
                    st.markdown(f'''
                    <div style="background:#1e293b;border:1px solid #374151;border-radius:6px;padding:8px;margin:4px 0;">
                        <div style="font-weight:bold;color:#e5e7eb;">{team['team_key']}</div>
                        <div style="font-size:0.85rem;color:#9ca3af;">
                            品質: <span style="color:{score_color};font-weight:bold;">{score if score else '-'}点</span> | 
                            成功率: {team.get('success_rate', 0)}% | 
                            実行: {team.get('total_executions', 0)}回
                        </div>
                    </div>
                    ''', unsafe_allow_html=True)
            else:
                st.caption("評価データなし（実行すると蓄積されます）")
            
            st.markdown("---")
            
            # ベンチマークテスト
            st.markdown("**🎯 ベンチマークテスト**")
            benchmark_team = st.selectbox("テスト対象チーム", ["coder", "auditor", "data", "searcher"], key="benchmark_team_select")
            
            if st.button("🚀 ベンチマーク実行", key="run_benchmark", use_container_width=True):
                with st.spinner(f"🎯 {benchmark_team}チームのベンチマーク実行中..."):
                    try:
                        # チームランナーを取得
                        team_config = get_team_config(benchmark_team)
                        
                        def team_runner(task):
                            if benchmark_team == "coder":
                                team = CoderTeam()
                            elif benchmark_team == "auditor":
                                team = AuditorTeam()
                            elif benchmark_team == "data":
                                team = DataTeam()
                            else:
                                team = SearcherTeam()
                            result = team.run(task)
                            return result.get("final_result", "")
                        
                        result = eval_manager.run_benchmark(benchmark_team, team_config, team_runner)
                        
                        st.success(f"✅ ベンチマーク完了: 平均{result['avg_score']}点 / {result['avg_time']}秒")
                        
                        for task_result in result.get('task_results', []):
                            status = "✅" if task_result['success'] else "❌"
                            st.caption(f"{status} {task_result['name']}: {task_result['score']}点")
                    except Exception as e:
                        st.error(f"❌ ベンチマーク失敗: {e}")
            
            st.markdown("---")
            
            # A/Bテスト
            st.markdown("**⚖️ A/Bテスト**")
            ab_task = st.text_input("A/Bテスト用タスク", placeholder="Pythonでフィボナッチ数列を計算...", key="ab_test_task")
            
            ab_col1, ab_col2 = st.columns(2)
            with ab_col1:
                st.caption("チームA: 現在の設定")
            with ab_col2:
                ab_team_b = st.selectbox("チームB", ["coder", "auditor", "data", "searcher"], key="ab_team_b_select")
            
            if st.button("▶️ A/Bテスト実行", key="run_ab_test", use_container_width=True):
                if ab_task.strip():
                    with st.spinner("⚖️ A/Bテスト実行中..."):
                        try:
                            team_a_config = get_team_config("coder")
                            team_b_config = get_team_config(ab_team_b)
                            
                            def team_a_runner(task):
                                team = CoderTeam()
                                result = team.run(task)
                                return result.get("final_result", "")
                            
                            def team_b_runner(task):
                                if ab_team_b == "coder":
                                    team = CoderTeam()
                                elif ab_team_b == "auditor":
                                    team = AuditorTeam()
                                elif ab_team_b == "data":
                                    team = DataTeam()
                                else:
                                    team = SearcherTeam()
                                result = team.run(task)
                                return result.get("final_result", "")
                            
                            result = eval_manager.run_ab_test(
                                ab_task, team_a_config, team_b_config,
                                team_a_runner, team_b_runner
                            )
                            
                            winner_text = "🏆 チームA勝利" if result['winner'] == 'team_a' else "🏆 チームB勝利" if result['winner'] == 'team_b' else "🤝 引き分け"
                            st.success(winner_text)
                            
                            r_col1, r_col2 = st.columns(2)
                            with r_col1:
                                st.markdown(f"**チームA**: {result['team_a']['time']:.2f}秒")
                            with r_col2:
                                st.markdown(f"**チームB**: {result['team_b']['time']:.2f}秒")
                        except Exception as e:
                            st.error(f"❌ A/Bテスト失敗: {e}")
                else:
                    st.warning("タスクを入力してください")
        except Exception as e:
            st.caption(f"評価システム: {e}")

elif active_tab_type == "todo":
    # ToDoタブ
    try:
        render_todo_panel()
    except Exception as e:
        st.error(f"ToDoパネルエラー: {e}")

elif active_tab_type == "mac":
    # Mac操作タブ
    st.markdown('<div style="font-size: 1.5rem; font-weight: bold; margin-bottom: 1rem;">🖥️ Mac操作</div>', unsafe_allow_html=True)
    try:
        render_mac_control_panel()
    except Exception as e:
        st.error(f"Mac操作パネルエラー: {e}")

elif active_tab_type == "browser":
    # ブラウザタブ（サーバーサイド取得 + レンダリング表示）
    import requests
    from bs4 import BeautifulSoup
    
    st.markdown('<div style="font-size: 1.5rem; font-weight: bold; margin-bottom: 1rem;">🌐 ブラウザ</div>', unsafe_allow_html=True)
    
    # セッション状態初期化
    if "browser_url" not in st.session_state:
        st.session_state.browser_url = "https://www.google.com/"
    if "browser_content" not in st.session_state:
        st.session_state.browser_content = None
    if "browser_analysis" not in st.session_state:
        st.session_state.browser_analysis = None
    if "browser_html" not in st.session_state:
        st.session_state.browser_html = None
    
    # URL入力バー
    url_col1, url_col2, url_col3 = st.columns([5, 1, 1])
    with url_col1:
        url = st.text_input("URL", value=st.session_state.browser_url, key="browser_url_input", label_visibility="collapsed", placeholder="https://example.com")
    with url_col2:
        go_clicked = st.button("🔄 移動", key="browser_go", use_container_width=True)
    with url_col3:
        analyze_clicked = st.button("🤖 AI分析", key="browser_analyze", use_container_width=True)
    
    # ページ取得関数
    def fetch_page(target_url):
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "ja,en-US;q=0.7,en;q=0.3",
            }
            response = requests.get(target_url, headers=headers, timeout=15)
            response.encoding = response.apparent_encoding or 'utf-8'
            return response.text, None
        except Exception as e:
            return None, str(e)
    
    # URL変更時またはページ未取得時
    if go_clicked and url:
        st.session_state.browser_url = url
        st.session_state.browser_content = None
        st.session_state.browser_analysis = None
        st.session_state.browser_html = None
    
    # ページ取得（初回または移動時）
    if st.session_state.browser_html is None:
        with st.spinner(f"🌐 {st.session_state.browser_url} を読み込み中..."):
            html, error = fetch_page(st.session_state.browser_url)
            if html:
                soup = BeautifulSoup(html, "html.parser")
                title = soup.title.string if soup.title else "タイトルなし"
                
                # base タグを追加してリソースの相対パスを解決
                from urllib.parse import urljoin, urlparse
                base_url = f"{urlparse(st.session_state.browser_url).scheme}://{urlparse(st.session_state.browser_url).netloc}"
                
                # 既存のbaseタグを削除
                for base in soup.find_all('base'):
                    base.decompose()
                
                # 新しいbaseタグを追加
                if soup.head:
                    new_base = soup.new_tag('base', href=base_url)
                    soup.head.insert(0, new_base)
                
                # 相対URLを絶対URLに変換
                for tag in soup.find_all(['img', 'link', 'script']):
                    for attr in ['src', 'href']:
                        if tag.get(attr) and not tag[attr].startswith(('http://', 'https://', 'data:', '//', '#')):
                            tag[attr] = urljoin(st.session_state.browser_url, tag[attr])
                
                # テキスト抽出（AI分析用）
                text_soup = BeautifulSoup(html, "html.parser")
                for tag in text_soup(["script", "style", "noscript"]):
                    tag.decompose()
                text = text_soup.get_text(separator="\n", strip=True)
                
                st.session_state.browser_html = str(soup)
                st.session_state.browser_content = {
                    "title": title,
                    "text": text[:15000],
                    "url": st.session_state.browser_url
                }
            else:
                st.error(f"❌ ページ取得失敗: {error}")
                st.session_state.browser_html = f"<html><body><h1>エラー</h1><p>{error}</p></body></html>"
                st.session_state.browser_content = None
    
    # ページ情報表示
    if st.session_state.browser_content:
        st.markdown(f"**📄 {st.session_state.browser_content['title']}**")
    
    # HTMLレンダリング表示
    if st.session_state.browser_html:
        st.components.v1.html(
            st.session_state.browser_html,
            height=550,
            scrolling=True
        )
    
    # AI分析
    if analyze_clicked and st.session_state.browser_content:
        with st.spinner("🤖 5つのAIが分析中..."):
            try:
                from agents.base import get_ai_instance
                from langchain_core.messages import HumanMessage, SystemMessage
                from concurrent.futures import ThreadPoolExecutor, as_completed
                
                content = st.session_state.browser_content
                prompt = f"""以下のWebページを分析してください。

URL: {content['url']}
タイトル: {content['title']}

内容:
{content['text'][:5000]}

以下の形式で回答:
1. 要約（100文字以内）
2. キーワード（5つ）
3. 特徴的なポイント
4. 採点（100点満点、情報の有用性）"""
                
                ai_keys = ["gemini", "gpt", "claude", "grok", "llama"]
                results = []
                
                def analyze_with_ai(ai_key):
                    try:
                        ai = get_ai_instance(ai_key, temperature=0)
                        messages = [
                            SystemMessage(content="あなたはWebページ分析の専門家です。簡潔に分析してください。"),
                            HumanMessage(content=prompt)
                        ]
                        response = ai.invoke(messages)
                        return {"ai": ai_key, "result": response.content, "success": True}
                    except Exception as e:
                        return {"ai": ai_key, "result": str(e), "success": False}
                
                with ThreadPoolExecutor(max_workers=5) as executor:
                    futures = {executor.submit(analyze_with_ai, key): key for key in ai_keys}
                    for future in as_completed(futures):
                        results.append(future.result())
                
                st.session_state.browser_analysis = results
            except Exception as e:
                st.error(f"❌ 分析失敗: {e}")
        st.rerun()
    
    # AI分析結果表示
    if st.session_state.browser_analysis:
        st.divider()
        st.subheader("🤖 AI分析結果")
        
        from config import AI_MODELS
        cols = st.columns(len(st.session_state.browser_analysis))
        for i, result in enumerate(st.session_state.browser_analysis):
            with cols[i]:
                ai_name = AI_MODELS.get(result['ai'], {}).get('name', result['ai'])
                if result['success']:
                    st.markdown(f"**{ai_name}**")
                    st.markdown(result['result'][:500])
                else:
                    st.error(f"{ai_name}: 失敗")
    
    # ブックマーク
    st.divider()
    st.subheader("⭐ ブックマーク")
    
    if "bookmarks" not in st.session_state:
        st.session_state.bookmarks = [
            {"name": "Google", "url": "https://www.google.com/"},
            {"name": "Wikipedia", "url": "https://ja.wikipedia.org/"},
            {"name": "GitHub", "url": "https://github.com/"},
            {"name": "Qiita", "url": "https://qiita.com/"},
        ]
    
    bm_cols = st.columns(4)
    for i, bm in enumerate(st.session_state.bookmarks):
        with bm_cols[i % 4]:
            if st.button(f"🔗 {bm['name']}", key=f"bm_{i}", use_container_width=True):
                st.session_state.browser_url = bm['url']
                st.session_state.browser_content = None
                st.session_state.browser_analysis = None
                st.session_state.browser_html = None
                st.rerun()
    
    # ブックマーク追加
    with st.expander("➕ ブックマーク管理"):
        bm_col1, bm_col2, bm_col3 = st.columns([2, 3, 1])
        with bm_col1:
            bm_name = st.text_input("名前", key="bm_name_input", label_visibility="collapsed", placeholder="名前")
        with bm_col2:
            bm_url = st.text_input("URL", key="bm_url_input", label_visibility="collapsed", placeholder="URL")
        with bm_col3:
            if st.button("追加", key="bm_add"):
                if bm_name and bm_url:
                    st.session_state.bookmarks.append({"name": bm_name, "url": bm_url})
                    st.rerun()

else:
    # 作業タブ（work）- 左カラム:クロスチェック結果、右カラム:チャット
    
    # 作業タブ専用CSS
    st.markdown('''
    <style>
    .work-tab-layout {
        display: flex;
        gap: 0;
        min-height: calc(100vh - 180px);
    }
    .work-tab-left {
        flex: 1;
        border-right: 2px solid #10b981;
        padding-right: 1.5rem;
        display: flex;
        flex-direction: column;
        align-items: flex-start;
    }
    .work-tab-right {
        flex: 2;
        padding-left: 1.5rem;
    }
    </style>
    ''', unsafe_allow_html=True)
    
    # 💬 履歴詳細表示（サイドバーからクリック時）
    if 'selected_history' in st.session_state:
        render_history_detail()
        st.divider()
    
    # 📂 ファイルバージョン詳細表示
    if 'view_version' in st.session_state:
        render_version_detail()
        st.divider()
    
    # APIキーチェック
    missing_keys = check_api_keys()
    if missing_keys:
        st.error(f"❌ APIキーが不足: {', '.join(missing_keys)}")
        st.stop()
    
    # タブ固有のメッセージ履歴
    messages_key = f"messages_{active_tab}"
    if messages_key not in st.session_state:
        st.session_state[messages_key] = []
    
    # クロスチェック結果用のセッション
    crosscheck_key = f"last_crosscheck_{active_tab}"
    if crosscheck_key not in st.session_state:
        st.session_state[crosscheck_key] = None
    
    # セッション状態から設定値を取得
    use_loop = st.session_state.use_loop
    use_crosscheck = st.session_state.use_crosscheck
    
    # メインレイアウト: 左=クロスチェック結果, 右=チャット
    # st.columnsを使い、左カラムに区切り線を追加
    col_crosscheck, col_chat = st.columns([1, 2], gap="medium")
    
    # 左カラム: クロスチェック結果パネル
    with col_crosscheck:
        # 左カラムに区切り線付きコンテナ
        st.markdown('<div class="work-tab-left">', unsafe_allow_html=True)
        
        # タイトルを最上部に配置
        st.markdown('<div style="font-size: 1.2rem; font-weight: bold; margin-bottom: 0.5rem;">📊 クロスチェック結果</div>', unsafe_allow_html=True)
        
        # セッションに保存されたクロスチェック結果を表示
        if st.session_state[crosscheck_key]:
            crosscheck = st.session_state[crosscheck_key]
            
            # 総合判定
            if "summary" in crosscheck:
                st.success(crosscheck["summary"])
            
            # 各AIの評価カード
            for check in crosscheck.get("checks", []):
                checker = check.get("checker", "不明")
                evaluation = check.get("evaluation", "")
                
                # スコア抽出（数字を探す）
                score_match = re.search(r'(\d{1,3})\s*[/点分]', evaluation)
                score = int(score_match.group(1)) if score_match else None
                
                # スコアによる色分け
                if score is not None:
                    if score >= 80:
                        score_color = "#10b981"  # 緑
                    elif score >= 60:
                        score_color = "#f59e0b"  # 黄
                    else:
                        score_color = "#ef4444"  # 赤
                    score_display = f'<span style="color:{score_color};font-size:1.2rem;font-weight:bold;">{score}点</span>'
                else:
                    score_display = "-"
                
                st.markdown(f'''
                <div class="crosscheck-card">
                    <h4>{checker}</h4>
                    <div>採点: {score_display}</div>
                    <div style="font-size:0.85rem;color:#9ca3af;margin-top:8px;white-space:pre-wrap;">{evaluation[:200]}{'...' if len(evaluation) > 200 else ''}</div>
                </div>
                ''', unsafe_allow_html=True)
        else:
            # 待機中メッセージもタイトル直下に表示
            st.info("待機中... メッセージを送信するとクロスチェック結果が表示されます")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # 右カラム: チャットエリア
    with col_chat:
        # ヘッダー（右端に配置）
        st.markdown('''<div style="display: flex; justify-content: flex-end; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
            <span style="font-size: 1.3rem;">🤖</span>
            <div>
                <span style="font-size: 1.1rem; font-weight: bold;">Multi-Agent System</span>
                <span style="font-size: 0.7rem; color: #6b7280; margin-left: 8px;">2026年1月版</span>
            </div>
        </div>''', unsafe_allow_html=True)
        
        # チャット履歴表示
        for message in st.session_state[messages_key]:
            with st.chat_message(message["role"], avatar=message.get("avatar")):
                st.markdown(message["content"])
        
        # ファイルアップロード（チャット入力の上）
        render_chat_uploader()
        
        # ユーザー入力（最下部）
        if prompt := st.chat_input("メッセージを入力してください..."):
            file_context = get_uploaded_files_for_prompt()
            full_prompt = prompt + file_context if file_context else prompt
            
            st.session_state[messages_key].append({"role": "user", "content": prompt, "avatar": "👤"})
            with st.chat_message("user", avatar="👤"):
                st.markdown(prompt)
                if file_context:
                    st.caption(f"📎 ファイル添付あり")
            
            with st.chat_message("assistant", avatar="👑"):
                with st.spinner("🤔 Gemini司令塔が思考中..."):
                    try:
                        commander_response = call_commander(full_prompt, st.session_state[messages_key])
                        agent_type, result, loop_data = process_command(commander_response, prompt, use_loop, use_crosscheck)
                        
                        agent_info = {
                            "auditor": "👮‍♂️ 監査チーム",
                            "coder": "👨‍💻 コーディングチーム",
                            "data": "🦙 データ処理チーム",
                            "searcher": "🔍 検索チーム",
                            "self": "👑 司令塔"
                        }
                        
                        if agent_type != "self":
                            st.info(f"📋 {agent_info.get(agent_type, '不明')} に依頼")
                        
                        st.markdown(result)
                        
                        crosscheck_data = loop_data.get("crosscheck") if loop_data else None
                        if crosscheck_data:
                            # 左カラムに表示するためセッションに保存
                            st.session_state[crosscheck_key] = crosscheck_data
                        
                        st.session_state[messages_key].append({
                            "role": "assistant",
                            "content": result,
                            "avatar": "👑",
                            "agent": agent_type,
                            "crosscheck": crosscheck_data
                        })
                        
                        clear_uploaded_files()
                        st.rerun()  # 左カラムを更新するため
                        
                    except Exception as e:
                        st.error(f"❌ エラー: {str(e)}")
                        import traceback
                        st.code(traceback.format_exc())
