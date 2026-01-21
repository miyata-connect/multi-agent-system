# ui/sidebar.py
# サイドバーの実装（設定ボタンを緑色に）
# 行数: 200行

import streamlit as st
import pandas as pd
from config import GEMINI_KEY, OPENAI_KEY, ANTHROPIC_KEY, GROQ_KEY, XAI_KEY, AI_MODELS, DEFAULT_TEAM_CONFIG, get_team_config, set_team_config, reset_team_config
from ui.conversation_history import render_conversation_history
from ui.upload_panel import render_upload_panel
from ui.parts_panel import render_parts_panel
from ui.file_history_panel import render_file_history_panel

def render_sidebar(artifact_store):
    """サイドバー全体をレンダリング"""
    with st.sidebar:
        # 設定ボタン（最上部・緑色）
        if st.button("⚙️ 設定を開く", key="sidebar_top_settings", use_container_width=True):
            from ui.tabs import add_tab
            add_tab("settings")
            st.rerun()
        st.divider()
        
        # 会話履歴
        render_conversation_history()
        st.divider()
        
        # エージェントチーム
        _render_agent_team()
        st.divider()
        
        # 設定セクション
        _render_quick_settings()
        st.divider()
        
        # APIキー状態
        _render_api_keys()
        st.divider()
        
        # 添付パネル
        try:
            render_upload_panel(artifact_store, st.session_state.conversation_id)
        except:
            st.caption("添付パネル準備中...")
        st.divider()
        
        # パーツパネル
        try:
            render_parts_panel()
        except:
            st.caption("パーツパネル準備中...")
        st.divider()
        
        # ファイル履歴パネル
        try:
            render_file_history_panel()
        except:
            st.caption("ファイル履歴準備中...")
        st.divider()
        
        # システム透明性
        _render_system_transparency()
        st.divider()
        
        # Skills管理
        st.header("📚 Skills管理")
        st.markdown("[🔗 Skills Serverで管理](https://skills-server-a34a4.web.app/)")
        st.divider()
        
        # ToDo
        _render_todo()
        st.divider()
        
        # Mac操作
        try:
            from integrations.firebase_mac import render_mac_control_panel
            render_mac_control_panel()
        except:
            st.caption("Mac操作パネル準備中...")

def _render_agent_team():
    """エージェントチーム表示"""
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
    
    # チーム構成テーブル
    team_data = []
    for team_key in DEFAULT_TEAM_CONFIG.keys():
        cfg = get_team_config(team_key)
        team_name = cfg['name'].replace('チーム', '').strip()
        leader_name = ai_names.get(cfg['leader'], cfg['leader'])
        team_data.append({'チーム': team_name, 'リーダー': leader_name})
    
    team_df = pd.DataFrame(team_data)
    st.table(team_df)
    
    # チーム評価スコア
    _render_team_scores(ai_names)

def _render_team_scores(ai_names):
    """チーム評価スコア表示"""
    st.caption("🏆 チーム評価（30日間）")
    try:
        from team_evaluator import get_evaluation_manager
        eval_manager = get_evaluation_manager()
        all_teams = eval_manager.get_all_teams_comparison(days=30)
        
        team_scores = {}
        if all_teams:
            for team in all_teams:
                team_scores[team['team_key']] = {
                    'score': team.get('avg_quality_score'),
                    'success': team.get('success_rate', 0)
                }
        
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
        score_data = []
        for team_key in DEFAULT_TEAM_CONFIG.keys():
            cfg = get_team_config(team_key)
            team_name = cfg['name'].replace('チーム', '').strip()
            score_data.append({'チーム': team_name, '品質': '-', '成功率': '-'})
        score_df = pd.DataFrame(score_data)
        st.table(score_df)

def _render_quick_settings():
    """簡易設定"""
    st.markdown("🔄 **コードレビューループ**")
    use_loop = st.toggle("ループ", value=st.session_state.use_loop, key="sidebar_use_loop", label_visibility="collapsed")
    st.session_state.use_loop = use_loop
    if use_loop:
        max_loop = st.slider("最大ループ回数", 1, 5, st.session_state.max_loop, key="sidebar_max_loop")
        st.session_state.max_loop = max_loop
    
    st.markdown("📊 **クロスチェック機能**")
    use_crosscheck = st.toggle("クロスチェック", value=st.session_state.use_crosscheck, key="sidebar_use_crosscheck", label_visibility="collapsed")
    st.session_state.use_crosscheck = use_crosscheck

def _render_api_keys():
    """APIキー状態"""
    st.header("🔑 APIキー状態")
    st.markdown(f"- Gemini: {'✅' if GEMINI_KEY else '❌'}")
    st.markdown(f"- OpenAI: {'✅' if OPENAI_KEY else '❌'}")
    st.markdown(f"- Anthropic: {'✅' if ANTHROPIC_KEY else '❌'}")
    st.markdown(f"- Groq: {'✅' if GROQ_KEY else '❌'}")
    st.markdown(f"- xAI: {'✅' if XAI_KEY else '❌'}")

def _render_system_transparency():
    """システム透明性"""
    st.header("📊 システム透明性")
    try:
        from failure_tracker import FailureTracker
        tracker = FailureTracker()
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

def _render_todo():
    """ToDo簡易表示"""
    st.header("✅ ToDo")
    try:
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
        
        # タスク一覧
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
