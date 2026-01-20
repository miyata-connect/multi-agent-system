# integrations/firebase_mac.py
# Mac操作用Firebase連携モジュール

import streamlit as st
import json
from datetime import datetime
from typing import Optional, Dict, Any

# Firebase Admin SDK
try:
    import firebase_admin
    from firebase_admin import credentials, db
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False


def get_firebase_creds() -> Optional[Dict]:
    """Streamlit SecretsからFirebase認証情報を取得"""
    try:
        if hasattr(st, 'secrets') and 'firebase' in st.secrets:
            return dict(st.secrets['firebase'])
        return None
    except Exception:
        return None


def init_firebase() -> bool:
    """Firebase初期化"""
    if not FIREBASE_AVAILABLE:
        return False
    
    try:
        # 既に初期化済みならスキップ
        firebase_admin.get_app()
        return True
    except ValueError:
        # 初期化されていない場合
        creds = get_firebase_creds()
        if not creds:
            return False
        
        try:
            cred = credentials.Certificate(creds)
            firebase_admin.initialize_app(cred, {
                'databaseURL': 'https://skills-server-a34a4-default-rtdb.firebaseio.com'
            })
            return True
        except Exception as e:
            st.error(f"Firebase初期化エラー: {e}")
            return False


def get_user_id() -> Optional[str]:
    """ユーザーIDを取得（Secrets or セッション）"""
    try:
        if hasattr(st, 'secrets') and 'SKILLS_USER_ID' in st.secrets:
            return st.secrets['SKILLS_USER_ID']
        return st.session_state.get('skills_user_id')
    except Exception:
        return None


def get_mac_status(user_id: str) -> Optional[Dict]:
    """Mac状態を取得"""
    if not init_firebase():
        return None
    
    try:
        ref = db.reference(f'users/{user_id}/macStatus')
        return ref.get()
    except Exception as e:
        st.error(f"Mac状態取得エラー: {e}")
        return None


def send_task(user_id: str, task: str, task_type: str = 'multi-agent') -> bool:
    """タスクをMacに送信"""
    if not init_firebase():
        return False
    
    try:
        ref = db.reference(f'users/{user_id}/commands')
        ref.push({
            'task': task,
            'type': task_type,
            'status': 'pending',
            'createdAt': {'.sv': 'timestamp'}
        })
        return True
    except Exception as e:
        st.error(f"タスク送信エラー: {e}")
        return False


def get_task_history(user_id: str, limit: int = 10) -> list:
    """タスク履歴を取得"""
    if not init_firebase():
        return []
    
    try:
        ref = db.reference(f'users/{user_id}/commands')
        snapshot = ref.order_by_child('createdAt').limit_to_last(limit).get()
        
        if not snapshot:
            return []
        
        tasks = []
        for key, value in snapshot.items():
            tasks.append({'id': key, **value})
        
        # 新しい順にソート
        tasks.sort(key=lambda x: x.get('createdAt', 0), reverse=True)
        return tasks
    except Exception as e:
        st.error(f"履歴取得エラー: {e}")
        return []


def format_relative_time(timestamp: int) -> str:
    """相対時間フォーマット"""
    if not timestamp:
        return "-"
    
    now = datetime.now().timestamp() * 1000
    diff = now - timestamp
    
    seconds = int(diff / 1000)
    minutes = int(seconds / 60)
    hours = int(minutes / 60)
    days = int(hours / 24)
    
    if seconds < 60:
        return f"{seconds}秒前"
    elif minutes < 60:
        return f"{minutes}分前"
    elif hours < 24:
        return f"{hours}時間前"
    else:
        return f"{days}日前"


def render_mac_control_panel():
    """Mac操作パネルをレンダリング"""
    st.header("🖥️ Mac操作")
    
    # Firebase利用可能チェック
    if not FIREBASE_AVAILABLE:
        st.warning("firebase-adminがインストールされていません")
        return
    
    # ユーザーID入力/取得
    user_id = get_user_id()
    
    if not user_id:
        st.text_input(
            "Skills User ID",
            key="skills_user_id_input",
            help="Skills ServerのユーザーIDを入力",
            on_change=lambda: st.session_state.update({'skills_user_id': st.session_state.skills_user_id_input})
        )
        st.info("Skills User IDを入力してください")
        return
    
    # Firebase初期化チェック
    if not init_firebase():
        st.warning("Firebase認証情報が設定されていません")
        st.caption("Streamlit Secretsに'firebase'を追加してください")
        return
    
    # Mac状態表示
    status = get_mac_status(user_id)
    
    if status:
        is_online = status.get('online', False) and \
                    (datetime.now().timestamp() * 1000 - status.get('lastSeen', 0) < 120000)
        
        col1, col2 = st.columns([1, 3])
        with col1:
            if is_online:
                st.markdown("🟢 **オンライン**")
            else:
                st.markdown("🔴 **オフライン**")
        with col2:
            st.caption(f"最終確認: {format_relative_time(status.get('lastSeen'))}")
        
        # システム情報
        sys_info = status.get('systemInfo', {})
        if sys_info:
            col1, col2, col3 = st.columns(3)
            with col1:
                cpu = sys_info.get('cpu')
                st.metric("CPU", f"{cpu:.1f}%" if cpu else "-")
            with col2:
                mem = sys_info.get('memory')
                st.metric("メモリ", f"{mem:.1f}%" if mem else "-")
            with col3:
                ai_status = sys_info.get('aiStatus', '-')
                st.metric("AI状態", ai_status)
    else:
        st.info("Mac未接続")
    
    st.divider()
    
    # タスク送信
    st.subheader("📤 タスク送信")
    task_input = st.text_area(
        "タスク",
        placeholder="Macで実行したいタスクを入力...\n例: Wordファイルを作成して、今日の日報を書いて",
        height=80,
        key="mac_task_input"
    )
    
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("📤 送信", use_container_width=True, disabled=not task_input):
            if send_task(user_id, task_input):
                st.success("✅ タスクを送信しました")
                st.session_state.mac_task_input = ""
                st.rerun()
    with col2:
        if st.button("🔄 更新", use_container_width=True):
            st.rerun()
    
    st.divider()
    
    # 実行履歴
    st.subheader("📋 実行履歴")
    history = get_task_history(user_id, limit=5)
    
    if history:
        for task in history:
            status_icon = {
                'pending': '⏳',
                'processing': '🔄',
                'completed': '✅',
                'error': '❌'
            }.get(task.get('status'), '❓')
            
            with st.container():
                st.markdown(f"{status_icon} **{task.get('task', '-')[:50]}{'...' if len(task.get('task', '')) > 50 else ''}**")
                st.caption(f"{format_relative_time(task.get('createdAt'))} | {task.get('status', '-')}")
                
                # 結果表示
                if task.get('result'):
                    with st.expander("結果を見る"):
                        st.write(task['result'].get('message', task['result'].get('output', '-')))
                
                # エラー表示
                if task.get('error'):
                    st.error(f"エラー: {task['error'].get('message', '-')}")
    else:
        st.caption("履歴がありません")
