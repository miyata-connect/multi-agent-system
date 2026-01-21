# ui/todo_panel.py
# ToDo機能（Firebase永続化）

import streamlit as st
from datetime import datetime
import uuid

# Firebase初期化
try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    
    if not firebase_admin._apps:
        # Streamlit Secretsから認証情報取得
        try:
            cred_dict = dict(st.secrets["firebase"])
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
        except Exception as e:
            pass
    
    db = firestore.client() if firebase_admin._apps else None
    FIREBASE_AVAILABLE = True
except ImportError:
    db = None
    FIREBASE_AVAILABLE = False


def get_user_id():
    """ユーザーID取得（セッションまたは仮ID）"""
    if "todo_user_id" not in st.session_state:
        # 仮のユーザーID（本番ではFirebase Auth連携）
        st.session_state.todo_user_id = f"local_{uuid.uuid4().hex[:8]}"
    return st.session_state.todo_user_id


def load_todos():
    """ToDoリストをFirebaseから読み込み"""
    if not FIREBASE_AVAILABLE or not db:
        # ローカルセッション使用
        if "todos" not in st.session_state:
            st.session_state.todos = []
        return st.session_state.todos
    
    try:
        user_id = get_user_id()
        docs = db.collection("todos").document(user_id).collection("items").order_by("created_at").stream()
        todos = []
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            todos.append(data)
        st.session_state.todos = todos
        return todos
    except Exception as e:
        st.session_state.todos = st.session_state.get("todos", [])
        return st.session_state.todos


def save_todo(text: str):
    """新規ToDo保存"""
    todo = {
        "text": text,
        "completed": False,
        "created_at": datetime.now().isoformat(),
        "id": uuid.uuid4().hex
    }
    
    if FIREBASE_AVAILABLE and db:
        try:
            user_id = get_user_id()
            db.collection("todos").document(user_id).collection("items").document(todo["id"]).set(todo)
        except Exception as e:
            pass
    
    if "todos" not in st.session_state:
        st.session_state.todos = []
    st.session_state.todos.append(todo)


def update_todo(todo_id: str, completed: bool):
    """ToDo完了状態更新"""
    if FIREBASE_AVAILABLE and db:
        try:
            user_id = get_user_id()
            db.collection("todos").document(user_id).collection("items").document(todo_id).update({"completed": completed})
        except Exception as e:
            pass
    
    for todo in st.session_state.get("todos", []):
        if todo["id"] == todo_id:
            todo["completed"] = completed
            break


def delete_todo(todo_id: str):
    """ToDo削除"""
    if FIREBASE_AVAILABLE and db:
        try:
            user_id = get_user_id()
            db.collection("todos").document(user_id).collection("items").document(todo_id).delete()
        except Exception as e:
            pass
    
    st.session_state.todos = [t for t in st.session_state.get("todos", []) if t["id"] != todo_id]


def render_todo_panel():
    """ToDoパネルをレンダリング"""
    st.markdown('<div style="font-size: 1.5rem; font-weight: bold; margin-bottom: 1rem;">✅ ToDo</div>', unsafe_allow_html=True)
    
    # Firebase状態表示
    if not FIREBASE_AVAILABLE:
        st.warning("⚠️ Firebase未接続（ローカル保存モード）")
    
    # 新規ToDo入力
    col1, col2 = st.columns([5, 1])
    with col1:
        new_todo = st.text_input("新しいタスク", placeholder="タスクを入力...", key="new_todo_input", label_visibility="collapsed")
    with col2:
        if st.button("追加", key="add_todo_btn", use_container_width=True):
            if new_todo.strip():
                save_todo(new_todo.strip())
                st.rerun()
    
    st.divider()
    
    # ToDoリスト読み込み
    todos = load_todos()
    
    # 未完了タスク
    incomplete = [t for t in todos if not t.get("completed")]
    completed = [t for t in todos if t.get("completed")]
    
    if incomplete:
        st.markdown("**📋 未完了**")
        for todo in incomplete:
            col1, col2, col3 = st.columns([1, 8, 1])
            with col1:
                if st.checkbox("", key=f"check_{todo['id']}", value=False):
                    update_todo(todo["id"], True)
                    st.rerun()
            with col2:
                st.markdown(todo["text"])
            with col3:
                if st.button("🗑️", key=f"del_{todo['id']}"):
                    delete_todo(todo["id"])
                    st.rerun()
    else:
        st.info("タスクがありません")
    
    # 完了タスク
    if completed:
        with st.expander(f"✅ 完了済み ({len(completed)}件)", expanded=False):
            for todo in completed:
                col1, col2, col3 = st.columns([1, 8, 1])
                with col1:
                    if st.checkbox("", key=f"check_{todo['id']}", value=True):
                        pass
                    else:
                        update_todo(todo["id"], False)
                        st.rerun()
                with col2:
                    st.markdown(f"~~{todo['text']}~~")
                with col3:
                    if st.button("🗑️", key=f"del_{todo['id']}"):
                        delete_todo(todo["id"])
                        st.rerun()
    
    # 統計
    st.divider()
    total = len(todos)
    done = len(completed)
    st.caption(f"進捗: {done}/{total} 完了" + (f" ({int(done/total*100)}%)" if total > 0 else ""))
