# ui/tabs.py
# タブ管理モジュール

import streamlit as st
from typing import Dict, List, Optional

# タブタイプ定義
TAB_TYPES = {
    "work": {"icon": "📝", "name": "作業", "multiple": True},
    "settings": {"icon": "⚙️", "name": "設定", "multiple": False},
    "mac": {"icon": "🖥️", "name": "Mac操作", "multiple": False}
}


def init_tabs():
    """タブ状態の初期化"""
    if "tabs" not in st.session_state:
        st.session_state.tabs = [
            {"id": "work_1", "type": "work", "name": "作業1"}
        ]
    if "active_tab" not in st.session_state:
        st.session_state.active_tab = "work_1"
    if "tab_counter" not in st.session_state:
        st.session_state.tab_counter = 1
    # 各タブのデータ
    if "tab_data" not in st.session_state:
        st.session_state.tab_data = {
            "work_1": {
                "messages": [],
                "last_crosscheck": None,
                "conversation_id": None,
                "uploaded_files": []
            }
        }


def get_tab_data(tab_id: str) -> Dict:
    """タブのデータを取得"""
    if tab_id not in st.session_state.tab_data:
        st.session_state.tab_data[tab_id] = {
            "messages": [],
            "last_crosscheck": None,
            "conversation_id": None,
            "uploaded_files": []
        }
    return st.session_state.tab_data[tab_id]


def add_tab(tab_type: str) -> Optional[str]:
    """タブを追加"""
    type_info = TAB_TYPES.get(tab_type)
    if not type_info:
        return None
    
    # 1つのみ許可のタブタイプで既存チェック
    if not type_info["multiple"]:
        for tab in st.session_state.tabs:
            if tab["type"] == tab_type:
                st.session_state.active_tab = tab["id"]
                return tab["id"]
    
    # 新規タブ作成
    if tab_type == "work":
        st.session_state.tab_counter += 1
        tab_id = f"work_{st.session_state.tab_counter}"
        tab_name = f"作業{st.session_state.tab_counter}"
    else:
        tab_id = tab_type
        tab_name = type_info["name"]
    
    new_tab = {
        "id": tab_id,
        "type": tab_type,
        "name": tab_name
    }
    
    # +ボタンの前に挿入
    st.session_state.tabs.append(new_tab)
    st.session_state.active_tab = tab_id
    
    # タブデータ初期化
    st.session_state.tab_data[tab_id] = {
        "messages": [],
        "last_crosscheck": None,
        "conversation_id": None,
        "uploaded_files": []
    }
    
    return tab_id


def remove_tab(tab_id: str):
    """タブを削除"""
    # タブが1つだけの場合は削除しない
    work_tabs = [t for t in st.session_state.tabs if t["type"] == "work"]
    if len(st.session_state.tabs) <= 1:
        return
    
    # タブ削除
    st.session_state.tabs = [t for t in st.session_state.tabs if t["id"] != tab_id]
    
    # タブデータ削除
    if tab_id in st.session_state.tab_data:
        del st.session_state.tab_data[tab_id]
    
    # アクティブタブが削除された場合、最初のタブをアクティブに
    if st.session_state.active_tab == tab_id:
        st.session_state.active_tab = st.session_state.tabs[0]["id"]


def render_tab_bar():
    """タブバーをレンダリング"""
    init_tabs()
    
    # タブバー用CSS
    st.markdown("""
    <style>
    .tab-bar {
        display: flex;
        gap: 4px;
        padding: 8px 0;
        border-bottom: 1px solid #374151;
        margin-bottom: 16px;
        flex-wrap: wrap;
    }
    .tab-item {
        display: flex;
        align-items: center;
        gap: 6px;
        padding: 8px 12px;
        background: #1f2937;
        border: 1px solid #374151;
        border-radius: 8px 8px 0 0;
        cursor: pointer;
        color: #9ca3af;
        font-size: 0.9rem;
        transition: all 0.2s;
    }
    .tab-item:hover {
        background: #374151;
        color: #f3f4f6;
    }
    .tab-item.active {
        background: #10b981;
        border-color: #10b981;
        color: white;
    }
    .tab-close {
        margin-left: 4px;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 0.8rem;
    }
    .tab-close:hover {
        background: rgba(255,255,255,0.2);
    }
    .tab-add {
        padding: 8px 16px;
        background: #374151;
        border: 1px dashed #6b7280;
        border-radius: 8px 8px 0 0;
        cursor: pointer;
        color: #9ca3af;
        font-size: 1rem;
    }
    .tab-add:hover {
        background: #4b5563;
        color: #f3f4f6;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # タブを横並びで表示
    cols = st.columns([1] * (len(st.session_state.tabs) + 1) + [4])
    
    # 各タブ
    for i, tab in enumerate(st.session_state.tabs):
        with cols[i]:
            type_info = TAB_TYPES.get(tab["type"], TAB_TYPES["work"])
            is_active = st.session_state.active_tab == tab["id"]
            
            # タブボタン
            col_btn, col_close = st.columns([4, 1])
            with col_btn:
                btn_type = "primary" if is_active else "secondary"
                if st.button(f"{type_info['icon']} {tab['name']}", key=f"tab_{tab['id']}", type=btn_type, use_container_width=True):
                    st.session_state.active_tab = tab["id"]
                    st.rerun()
            
            with col_close:
                if len(st.session_state.tabs) > 1:
                    if st.button("×", key=f"close_{tab['id']}", use_container_width=True):
                        remove_tab(tab["id"])
                        st.rerun()
    
    # +ボタン（ポップオーバー）
    with cols[len(st.session_state.tabs)]:
        with st.popover("＋", use_container_width=True):
            st.markdown("**タブを追加**")
            if st.button("📝 新規作業", key="add_work", use_container_width=True):
                add_tab("work")
                st.rerun()
            
            # 設定タブが未追加なら表示
            has_settings = any(t["type"] == "settings" for t in st.session_state.tabs)
            if not has_settings:
                if st.button("⚙️ 設定", key="add_settings", use_container_width=True):
                    add_tab("settings")
                    st.rerun()
            
            # Mac操作タブが未追加なら表示
            has_mac = any(t["type"] == "mac" for t in st.session_state.tabs)
            if not has_mac:
                if st.button("🖥️ Mac操作", key="add_mac", use_container_width=True):
                    add_tab("mac")
                    st.rerun()
    
    return st.session_state.active_tab


def get_active_tab_type() -> str:
    """アクティブタブのタイプを取得"""
    for tab in st.session_state.tabs:
        if tab["id"] == st.session_state.active_tab:
            return tab["type"]
    return "work"
