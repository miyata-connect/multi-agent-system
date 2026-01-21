# ui/conversation_history.py
# 会話履歴表示コンポーネント

import streamlit as st
from datetime import datetime
from conversation_memory import memory

def render_conversation_history():
    """サイドバーに会話履歴を表示"""
    
    st.markdown("### 💬 会話履歴")
    
    # 履歴取得
    try:
        history = memory.get_session_history(limit=50)  # 最大50件
        
        if not history:
            st.caption("まだ会話履歴がありません")
            return
        
        # 直近10件を表示
        recent_history = history[-10:]
        
        # スクロール可能なコンテナ
        history_container = st.container()
        
        with history_container:
            for i, msg in enumerate(reversed(recent_history)):  # 新しい順
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')
                ai_type = msg.get('ai_type', '')
                timestamp = msg.get('timestamp', '')
                
                # 履歴アイテム
                with st.container():
                    # アイコンと短縮メッセージ
                    if role == 'user':
                        icon = "👤"
                        display_name = "あなた"
                        preview = content[:40] + "..." if len(content) > 40 else content
                    else:
                        if ai_type == 'Gemini':
                            icon = "👑"
                            display_name = "司令塔"
                        elif ai_type == 'auditor':
                            icon = "👮‍♂️"
                            display_name = "監査役"
                        elif ai_type == 'coder':
                            icon = "👨‍💻"
                            display_name = "コード役"
                        elif ai_type == 'data_processor':
                            icon = "🦙"
                            display_name = "データ役"
                        else:
                            icon = "🤖"
                            display_name = "AI"
                        preview = content[:40] + "..." if len(content) > 40 else content
                    
                    # クリック可能なボタン
                    if st.button(
                        f"{icon} {display_name}: {preview}",
                        key=f"history_{i}_{timestamp}",
                        use_container_width=True,
                        help=f"クリックで詳細表示\n{content[:100]}"
                    ):
                        # 詳細をメインエリアに表示
                        st.session_state['selected_history'] = {
                            'role': role,
                            'content': content,
                            'ai_type': ai_type,
                            'timestamp': timestamp,
                            'display_name': display_name,
                            'icon': icon
                        }
                        st.rerun()
                    
                    st.caption(f"🕒 {format_timestamp(timestamp)}")
                    st.markdown("---")
        
        # クリア機能
        if st.button("🗑️ 履歴をクリア", use_container_width=True, key="clear_history"):
            memory.clear_session()
            st.success("履歴をクリアしました")
            st.rerun()
            
    except Exception as e:
        st.error(f"履歴取得エラー: {e}")

def format_timestamp(ts_str):
    """タイムスタンプを読みやすい形式に変換"""
    try:
        if not ts_str:
            return "不明"
        # ISO形式のタイムスタンプを変換
        dt = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
        now = datetime.now(dt.tzinfo)
        
        # 時間差計算
        diff = now - dt
        
        if diff.days > 0:
            return f"{diff.days}日前"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours}時間前"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes}分前"
        else:
            return "たった今"
    except:
        return "不明"

def render_history_detail():
    """選択された履歴の詳細を表示"""
    if 'selected_history' not in st.session_state:
        return
    
    hist = st.session_state['selected_history']
    
    st.markdown(f"## {hist['icon']} {hist['display_name']}")
    st.markdown(f"*{format_timestamp(hist['timestamp'])}*")
    st.markdown("---")
    st.markdown(hist['content'])
    st.markdown("---")
    
    # ボタンを横並びに表示
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 この会話を続ける", key="restore_history", use_container_width=True):
            restore_conversation_from_history(hist['timestamp'])
    
    with col2:
        if st.button("✖️ 閉じる", key="close_detail", use_container_width=True):
            del st.session_state['selected_history']
            st.rerun()

def restore_conversation_from_history(target_timestamp: str):
    """指定タイムスタンプまでの会話を復元"""
    try:
        # タイムスタンプまでの履歴を取得
        history_data = memory.get_history_until(target_timestamp)
        
        if not history_data:
            st.warning("復元する履歴が見つかりません")
            return
        
        # 現在のアクティブタブのメッセージキーを取得
        from ui.tabs import get_active_tab_type
        active_tab = get_active_tab_type()
        messages_key = f"messages_{active_tab}"
        
        # 履歴をStreamlitメッセージ形式に変換
        restored_messages = []
        for msg in history_data:
            role = msg['role']
            content = msg['content']
            ai_type = msg.get('ai_type', '')
            
            # アバター設定
            if role == 'user':
                avatar = "👤"
            else:
                if ai_type == 'Gemini':
                    avatar = "👑"
                elif ai_type == 'auditor':
                    avatar = "👮‍♂️"
                elif ai_type == 'coder':
                    avatar = "👨‍💻"
                elif ai_type == 'data_processor':
                    avatar = "🦙"
                else:
                    avatar = "🤖"
            
            restored_messages.append({
                "role": role,
                "content": content,
                "avatar": avatar,
                "agent": ai_type
            })
        
        # セッションステートに復元
        st.session_state[messages_key] = restored_messages
        
        # 詳細表示を閉じる
        if 'selected_history' in st.session_state:
            del st.session_state['selected_history']
        
        st.success(f"✅ {len(restored_messages)}件のメッセージを復元しました！")
        st.rerun()
        
    except Exception as e:
        st.error(f"復元エラー: {e}")
        import traceback
        st.code(traceback.format_exc())
