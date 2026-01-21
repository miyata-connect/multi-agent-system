# ui/todo_panel.py
# プロジェクト分けToDoシステム
# 行数: 250行

import streamlit as st
import uuid
from datetime import datetime, timedelta

def render_todo_panel():
    """プロジェクト分けToDoパネルをレンダリング"""
    st.markdown('<div style="font-size: 1.5rem; font-weight: bold; margin-bottom: 1rem;">✅ プロジェクトToDo</div>', unsafe_allow_html=True)
    
    # セッション状態初期化
    _init_todo_session()
    
    # プロジェクト管理
    _render_project_management()
    
    st.divider()
    
    # プロジェクト別タスク表示
    _render_projects_and_tasks()
    
    st.divider()
    
    # 統計サマリー
    _render_summary()

def _init_todo_session():
    """セッション状態初期化"""
    if "projects" not in st.session_state:
        st.session_state.projects = [
            {
                "id": "default",
                "name": "一般タスク",
                "created_at": datetime.now().isoformat()
            }
        ]
    if "todos" not in st.session_state:
        st.session_state.todos = []

def _render_project_management():
    """プロジェクト管理UI"""
    st.markdown("### 📁 プロジェクト管理")
    
    proj_col1, proj_col2 = st.columns([3, 1])
    with proj_col1:
        new_project = st.text_input(
            "新規プロジェクト",
            key="new_project_input",
            placeholder="プロジェクト名を入力...",
            label_visibility="collapsed"
        )
    with proj_col2:
        if st.button("追加", key="add_project", use_container_width=True):
            if new_project.strip():
                project = {
                    "id": uuid.uuid4().hex,
                    "name": new_project.strip(),
                    "created_at": datetime.now().isoformat()
                }
                st.session_state.projects.append(project)
                st.success(f"✅ プロジェクト「{new_project}」を追加")
                st.rerun()

def _render_projects_and_tasks():
    """プロジェクトとタスク表示"""
    for project in st.session_state.projects:
        _render_project_section(project)

def _render_project_section(project):
    """個別プロジェクトセクション"""
    project_todos = [t for t in st.session_state.todos if t.get("project_id") == project["id"]]
    incomplete = [t for t in project_todos if not t.get("completed")]
    completed = [t for t in project_todos if t.get("completed")]
    
    # プロジェクトヘッダー
    with st.expander(f"📁 {project['name']} ({len(incomplete)}/{len(project_todos)})", expanded=True):
        # タスク追加
        _render_task_input(project)
        
        # 未完了タスク
        if incomplete:
            st.markdown("**未完了タスク**")
            for todo in sorted(incomplete, key=lambda x: x.get("deadline", "9999-12-31")):
                _render_task_item(todo, project)
        else:
            st.caption("未完了タスクはありません")
        
        # 完了タスク
        if completed:
            st.divider()
            with st.expander(f"✅ 完了タスク ({len(completed)}件)", expanded=False):
                for todo in completed:
                    _render_completed_task(todo)
        
        # プロジェクト削除
        if project["id"] != "default" and len(project_todos) == 0:
            if st.button(f"🗑 プロジェクト削除", key=f"del_proj_{project['id']}", use_container_width=True):
                st.session_state.projects = [p for p in st.session_state.projects if p["id"] != project["id"]]
                st.rerun()

def _render_task_input(project):
    """タスク入力UI"""
    st.markdown("**➕ 新しいタスク**")
    
    task_col1, task_col2, task_col3 = st.columns([4, 3, 1])
    
    with task_col1:
        task_text = st.text_input(
            "タスク内容",
            key=f"task_input_{project['id']}",
            placeholder="タスク内容...",
            label_visibility="collapsed"
        )
    
    with task_col2:
        deadline = st.date_input(
            "期限",
            key=f"deadline_{project['id']}",
            value=datetime.now() + timedelta(days=1),
            label_visibility="collapsed"
        )
    
    with task_col3:
        if st.button("追加", key=f"add_task_{project['id']}", use_container_width=True):
            if task_text.strip():
                todo = {
                    "id": uuid.uuid4().hex,
                    "project_id": project["id"],
                    "text": task_text.strip(),
                    "deadline": deadline.isoformat(),
                    "completed": False,
                    "created_at": datetime.now().isoformat()
                }
                st.session_state.todos.append(todo)
                st.rerun()

def _render_task_item(todo, project):
    """タスクアイテム表示"""
    # 期限チェック
    deadline_date = datetime.fromisoformat(todo["deadline"]).date()
    today = datetime.now().date()
    days_left = (deadline_date - today).days
    
    # 期限表示色
    if days_left < 0:
        deadline_color = "#ef4444"
        deadline_icon = "🔴"
    elif days_left == 0:
        deadline_color = "#f59e0b"
        deadline_icon = "🟡"
    elif days_left <= 2:
        deadline_color = "#f59e0b"
        deadline_icon = "⏰"
    else:
        deadline_color = "#10b981"
        deadline_icon = "📅"
    
    task_col1, task_col2, task_col3, task_col4 = st.columns([1, 5, 2, 1])
    
    with task_col1:
        if st.checkbox("", key=f"check_{todo['id']}", value=False, label_visibility="collapsed"):
            todo["completed"] = True
            todo["completed_at"] = datetime.now().isoformat()
            st.rerun()
    
    with task_col2:
        st.markdown(f"{todo['text']}")
    
    with task_col3:
        st.markdown(f"<span style='color:{deadline_color};'>{deadline_icon} {deadline_date.strftime('%m/%d')}</span>", unsafe_allow_html=True)
    
    with task_col4:
        if st.button("🗑", key=f"del_{todo['id']}"):
            st.session_state.todos = [t for t in st.session_state.todos if t["id"] != todo["id"]]
            st.rerun()

def _render_completed_task(todo):
    """完了タスク表示"""
    deadline_date = datetime.fromisoformat(todo["deadline"]).date()
    
    comp_col1, comp_col2, comp_col3 = st.columns([6, 2, 1])
    
    with comp_col1:
        st.markdown(f"~~{todo['text']}~~")
    
    with comp_col2:
        st.caption(f"📅 {deadline_date.strftime('%m/%d')}")
    
    with comp_col3:
        if st.button("🗑", key=f"del_done_{todo['id']}"):
            st.session_state.todos = [t for t in st.session_state.todos if t["id"] != todo["id"]]
            st.rerun()

def _render_summary():
    """統計サマリー"""
    st.markdown("### 📊 統計")
    
    all_todos = st.session_state.todos
    incomplete = [t for t in all_todos if not t.get("completed")]
    completed = [t for t in all_todos if t.get("completed")]
    
    # 期限切れタスク数
    today = datetime.now().date()
    overdue = [t for t in incomplete if datetime.fromisoformat(t["deadline"]).date() < today]
    
    sum_col1, sum_col2, sum_col3 = st.columns(3)
    
    with sum_col1:
        st.metric("未完了", len(incomplete))
    
    with sum_col2:
        st.metric("完了", len(completed))
    
    with sum_col3:
        st.metric("期限切れ", len(overdue), delta_color="inverse")
    
    # 進捗率
    if len(all_todos) > 0:
        progress = len(completed) / len(all_todos)
        st.progress(progress, text=f"全体進捗: {progress*100:.0f}%")
