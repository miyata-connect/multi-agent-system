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
div.block-container { max-width: 100vw !important; width: 100% !important; padding-left: 1.5rem !important; padding-right: 1.5rem !important; padding-top: 0 !important; margin-top: 0 !important; }
header[data-testid="stHeader"] { display: none !important; }

/* チャット入力欄 */
div[data-testid="stChatInput"] { border: 2px solid #10b981 !important; border-radius: 26px !important; background: #0e1117 !important; }
div[data-testid="stChatInput"]:focus-within { border-color: #059669 !important; box-shadow: 0 0 0 1px #059669 !important; }
div[data-testid="stChatInput"] button { background: #10b981 !important; border-radius: 50% !important; }
div[data-testid="stChatInput"], div[data-testid="stChatInput"] form, div[data-testid="stChatInput"] textarea { width: 100% !important; max-width: 100% !important; box-sizing: border-box !important; }

/* クロスチェックカード */
.crosscheck-card { background: #1e1e1e; border: 1px solid #374151; border-radius: 8px; padding: 12px; margin-bottom: 12px; }
.crosscheck-card h4 { color: #10b981; margin: 0 0 8px 0; font-size: 0.9rem; }

/* サイドバー */
section[data-testid="stSidebar"] > div { margin-top: -3rem !important; padding-top: 0 !important; }
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] { gap: 0.5rem !important; }
</style>
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
# タブ初期化
# ==========================================
init_tabs()
active_tab = render_tab_bar()
active_tab_type = get_active_tab_type()
tab_data = get_tab_data(active_tab)

# ==========================================
# サイドバー（仕様確定まで残す）
# ==========================================
with st.sidebar:
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
    for team_key in DEFAULT_TEAM_CONFIG.keys():
        cfg = get_team_config(team_key)
        st.markdown(f"**{cfg['name']}**: {ai_names.get(cfg['leader'], cfg['leader'])}（長）")
    
    st.divider()
    
    st.header("⚙️ 設定")
    use_loop = st.toggle("🔄 コードレビューループ", value=True)
    max_loop = st.slider("最大ループ回数", 1, 5, 3) if use_loop else 1
    use_crosscheck = st.toggle("📊 クロスチェック機能", value=False)
    
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
        
        st.subheader("🔑 APIキー状態")
        st.markdown(f"- Gemini: {'✅' if GEMINI_KEY else '❌'}")
        st.markdown(f"- OpenAI: {'✅' if OPENAI_KEY else '❌'}")
        st.markdown(f"- Anthropic: {'✅' if ANTHROPIC_KEY else '❌'}")
        st.markdown(f"- Groq: {'✅' if GROQ_KEY else '❌'}")
        st.markdown(f"- xAI: {'✅' if XAI_KEY else '❌'}")
    
    with col2:
        st.subheader("📊 システム透明性")
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
        
        st.subheader("📚 Skills管理")
        st.markdown("[🔗 Skills Serverで管理](https://skills-server-a34a4.web.app/)")

elif active_tab_type == "mac":
    # Mac操作タブ
    st.markdown('<div style="font-size: 1.5rem; font-weight: bold; margin-bottom: 1rem;">🖥️ Mac操作</div>', unsafe_allow_html=True)
    try:
        render_mac_control_panel()
    except Exception as e:
        st.error(f"Mac操作パネルエラー: {e}")

else:
    # 作業タブ（work）
    col_crosscheck, col_chat = st.columns([1, 2])
    
    # 左カラム: クロスチェック結果
    with col_crosscheck:
        st.markdown('<div style="font-size: 1.2rem; font-weight: bold; margin-bottom: 1rem;">📊 クロスチェック結果</div>', unsafe_allow_html=True)
        
        # タブ固有のクロスチェック結果を使用
        crosscheck_key = f"crosscheck_{active_tab}"
        if crosscheck_key in st.session_state and st.session_state[crosscheck_key]:
            crosscheck = st.session_state[crosscheck_key]
            if "summary" in crosscheck:
                st.success(crosscheck["summary"])
            
            checks = crosscheck.get("checks", [])
            for i in range(0, len(checks), 2):
                cols = st.columns(2)
                for j, col in enumerate(cols):
                    if i + j < len(checks):
                        check = checks[i + j]
                        checker = check.get("checker", "不明")
                        evaluation = check.get("evaluation", "")
                        score_match = re.search(r'(\d{1,3})\s*[/点分]', evaluation)
                        score = int(score_match.group(1)) if score_match else None
                        
                        if score is not None:
                            score_color = "#10b981" if score >= 80 else "#f59e0b" if score >= 60 else "#ef4444"
                            score_display = f'<span style="color:{score_color};font-size:1.1rem;font-weight:bold;">{score}点</span>'
                        else:
                            score_display = "-"
                        
                        with col:
                            st.markdown(f'''<div class="crosscheck-card"><h4>{checker}</h4><div>採点: {score_display}</div><div style="font-size:0.8rem;color:#9ca3af;margin-top:6px;">{evaluation[:150]}...</div></div>''', unsafe_allow_html=True)
        else:
            st.info("待機中... メッセージを送信するとクロスチェック結果が表示されます")
    
    # 右カラム: チャット
    with col_chat:
        st.markdown('''<div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem;"><span style="font-size: 1.5rem;">🤖</span><div><div style="font-size: 1.2rem; font-weight: bold;">Multi-Agent System</div><div style="font-size: 0.7rem; color: #6b7280;">2026年1月版 - タブ機能付き</div></div></div>''', unsafe_allow_html=True)
        
        # APIキーチェック
        missing_keys = check_api_keys()
        if missing_keys:
            st.error(f"❌ APIキーが不足: {', '.join(missing_keys)}")
            st.stop()
        
        # タブ固有のメッセージ履歴を使用
        messages_key = f"messages_{active_tab}"
        if messages_key not in st.session_state:
            st.session_state[messages_key] = []
        
        # チャット履歴表示
        for message in st.session_state[messages_key]:
            with st.chat_message(message["role"], avatar=message.get("avatar")):
                st.markdown(message["content"])
        
        # ファイルアップロード
        render_chat_uploader()
        
        # ユーザー入力
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
                        
                        # クロスチェック結果をタブ固有のキーに保存
                        need_rerun = False
                        if loop_data and loop_data.get("crosscheck"):
                            st.session_state[f"crosscheck_{active_tab}"] = loop_data["crosscheck"]
                            need_rerun = True
                        
                        st.session_state[messages_key].append({
                            "role": "assistant",
                            "content": result,
                            "avatar": "👑",
                            "agent": agent_type
                        })
                        
                        clear_uploaded_files()
                        
                        if need_rerun:
                            st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ エラー: {str(e)}")
                        import traceback
                        st.code(traceback.format_exc())
