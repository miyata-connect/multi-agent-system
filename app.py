# app.py
# Multi-Agent System メインUI（細分化版）
# 行数: 250行（1376行→250行に削減）

import streamlit as st
import uuid
import re

# モジュールインポート
from config import (
    check_api_keys, GEMINI_KEY, OPENAI_KEY, ANTHROPIC_KEY, GROQ_KEY, XAI_KEY,
    AI_MODELS, DEFAULT_TEAM_CONFIG, get_team_config, set_team_config, reset_team_config
)
from agents import call_commander
from agents.coder_team import CoderTeam
from agents.auditor_team import AuditorTeam
from agents.data_team import DataTeam
from agents.searcher_team import SearcherTeam
from core import generate_crosscheck_summary
from failure_tracker import FailureTracker
from failure_analyzer import FailureAnalyzer
from learning_integrator import LearningSkillsIntegrator
from core.artifact_store import ArtifactStore

# UI モジュール
from ui.tabs import render_tab_bar, get_active_tab_type, get_tab_data, init_tabs
from ui.settings_tab import render_settings_tab
from ui.todo_panel import render_todo_panel
from ui.browser_tab import render_browser_tab
from ui.work_tab import render_work_tab
from ui.sidebar import render_sidebar

# Mac操作連携
try:
    from integrations.firebase_mac import render_mac_control_panel, FIREBASE_AVAILABLE
except ImportError:
    FIREBASE_AVAILABLE = False
    def render_mac_control_panel():
        pass

# ==========================================
# リソース初期化
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

/* クロスチェック */
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

/* 作業タブレイアウト */
.work-tab-left {
    flex: 1;
    border-right: 2px solid #10b981;
    padding-right: 1.5rem;
    display: flex;
    flex-direction: column;
    align-items: flex-start;
}
</style>
''', unsafe_allow_html=True)

# ==========================================
# 処理の振り分け
# ==========================================
def process_command(commander_response: str, original_input: str, use_loop: bool, use_crosscheck: bool = True) -> tuple:
    """司令塔の指示を処理"""
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
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = str(uuid.uuid4())

# ==========================================
# タブ初期化
# ==========================================
init_tabs()
active_tab = render_tab_bar()
active_tab_type = get_active_tab_type()

# ==========================================
# サイドバー
# ==========================================
artifact_store = get_artifact_store()
render_sidebar(artifact_store)

# ==========================================
# タブ別コンテンツ
# ==========================================
if active_tab_type == "settings":
    render_settings_tab()

elif active_tab_type == "todo":
    try:
        render_todo_panel()
    except Exception as e:
        st.error(f"ToDoパネルエラー: {e}")

elif active_tab_type == "mac":
    st.markdown('<div style="font-size: 1.5rem; font-weight: bold; margin-bottom: 1rem;">🖥️ Mac操作</div>', unsafe_allow_html=True)
    try:
        render_mac_control_panel()
    except Exception as e:
        st.error(f"Mac操作パネルエラー: {e}")

elif active_tab_type == "browser":
    render_browser_tab()

else:
    # 作業タブ
    render_work_tab(active_tab, process_command, get_failure_tracker)
