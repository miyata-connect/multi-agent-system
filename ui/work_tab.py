# ui/work_tab.py
# 作業タブ(チャット)の実装
# 行数: 150行

import streamlit as st
import uuid
from config import check_api_keys
from agents import call_commander
from ui.chat_uploader import render_chat_uploader, get_uploaded_files_for_prompt, clear_uploaded_files
from ui.conversation_history import render_history_detail
from ui.file_history_panel import render_version_detail
from core import generate_crosscheck_summary

def render_work_tab(active_tab, process_command_func, get_failure_tracker_func):
    """作業タブをレンダリング"""
    
    # 履歴詳細表示
    if 'selected_history' in st.session_state:
        render_history_detail()
        st.divider()
    
    # ファイルバージョン詳細表示
    if 'view_version' in st.session_state:
        render_version_detail()
        st.divider()
    
    # APIキーチェック
    missing_keys = check_api_keys()
    if missing_keys:
        st.error(f"❌ APIキーが不足: {', '.join(missing_keys)}")
        st.stop()
    
    # メッセージ履歴初期化
    messages_key = f"messages_{active_tab}"
    if messages_key not in st.session_state:
        st.session_state[messages_key] = []
    
    # クロスチェック結果初期化
    crosscheck_key = f"last_crosscheck_{active_tab}"
    if crosscheck_key not in st.session_state:
        st.session_state[crosscheck_key] = None
    
    # レイアウト
    col_crosscheck, col_chat = st.columns([1, 2], gap="medium")
    
    # 左カラム: クロスチェック結果
    with col_crosscheck:
        _render_crosscheck_panel(crosscheck_key)
    
    # 右カラム: チャット
    with col_chat:
        _render_chat_area(messages_key, crosscheck_key, process_command_func, get_failure_tracker_func)

def _render_crosscheck_panel(crosscheck_key):
    """クロスチェック結果パネル"""
    import re
    
    st.markdown('<div class="work-tab-left">', unsafe_allow_html=True)
    st.markdown('<div style="font-size: 1.2rem; font-weight: bold; margin-bottom: 0.5rem;">📊 クロスチェック結果</div>', unsafe_allow_html=True)
    
    if st.session_state[crosscheck_key]:
        crosscheck = st.session_state[crosscheck_key]
        
        if "summary" in crosscheck:
            st.success(crosscheck["summary"])
        
        for check in crosscheck.get("checks", []):
            checker = check.get("checker", "不明")
            evaluation = check.get("evaluation", "")
            
            score_match = re.search(r'(\d{1,3})\s*[/点分]', evaluation)
            score = int(score_match.group(1)) if score_match else None
            
            if score is not None:
                if score >= 80:
                    score_color = "#10b981"
                elif score >= 60:
                    score_color = "#f59e0b"
                else:
                    score_color = "#ef4444"
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
        st.info("待機中... メッセージを送信するとクロスチェック結果が表示されます")
    
    st.markdown('</div>', unsafe_allow_html=True)

def _render_chat_area(messages_key, crosscheck_key, process_command_func, get_failure_tracker_func):
    """チャットエリア"""
    
    # ヘッダー
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
    
    # ファイルアップロード
    render_chat_uploader()
    
    # ユーザー入力
    if prompt := st.chat_input("メッセージを入力してください..."):
        _handle_user_input(prompt, messages_key, crosscheck_key, process_command_func)

def _handle_user_input(prompt, messages_key, crosscheck_key, process_command_func):
    """ユーザー入力処理"""
    
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
                
                use_loop = st.session_state.use_loop
                use_crosscheck = st.session_state.use_crosscheck
                
                agent_type, result, loop_data = process_command_func(
                    commander_response, prompt, use_loop, use_crosscheck
                )
                
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
                    st.session_state[crosscheck_key] = crosscheck_data
                
                st.session_state[messages_key].append({
                    "role": "assistant",
                    "content": result,
                    "avatar": "👑",
                    "agent": agent_type,
                    "crosscheck": crosscheck_data
                })
                
                clear_uploaded_files()
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ エラー: {str(e)}")
                import traceback
                st.code(traceback.format_exc())
