# ui/tabs.py
# タブ管理モジュール（インデックスタブデザイン）

import streamlit as st
from typing import Dict, Optional

# タブタイプ定義
TAB_TYPES = {
    "work": {"icon": "📝", "name": "作業", "multiple": True},
    "todo": {"icon": "✅", "name": "ToDo", "multiple": False},
    "settings": {"icon": "⚙️", "name": "設定", "multiple": False},
    "browser": {"icon": "🌐", "name": "ブラウザ", "multiple": False},
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
    
    new_tab = {"id": tab_id, "type": tab_type, "name": tab_name}
    st.session_state.tabs.append(new_tab)
    st.session_state.active_tab = tab_id
    
    st.session_state.tab_data[tab_id] = {
        "messages": [],
        "last_crosscheck": None,
        "conversation_id": None,
        "uploaded_files": []
    }
    
    return tab_id


def remove_tab(tab_id: str):
    """タブを削除"""
    if len(st.session_state.tabs) <= 1:
        return
    
    st.session_state.tabs = [t for t in st.session_state.tabs if t["id"] != tab_id]
    
    if tab_id in st.session_state.tab_data:
        del st.session_state.tab_data[tab_id]
    
    if st.session_state.active_tab == tab_id:
        st.session_state.active_tab = st.session_state.tabs[0]["id"]


def render_tab_bar():
    """インデックスタブ（フォルダ型）をレンダリング"""
    init_tabs()
    
    # インデックスタブ用CSS
    st.markdown("""
    <style>
    /* インデックスタブ（フォルダ型） */
    .index-tab-container {
        display: flex;
        align-items: flex-end;
        gap: 2px;
        padding-bottom: 0;
        margin-bottom: 0;
    }
    .index-tab {
        position: relative;
        padding: 6px 16px 8px 16px;
        background: #374151;
        border: 1px solid #4b5563;
        border-bottom: none;
        border-radius: 8px 8px 0 0;
        color: #9ca3af;
        font-size: 0.85rem;
        cursor: pointer;
        transition: all 0.15s;
        display: flex;
        align-items: center;
        gap: 6px;
        margin-bottom: -1px;
        z-index: 1;
    }
    .index-tab:hover {
        background: #4b5563;
        color: #e5e7eb;
    }
    .index-tab.active {
        background: #1f2937;
        border-color: #10b981;
        border-bottom: 1px solid #1f2937;
        color: #10b981;
        font-weight: 600;
        z-index: 10;
        padding-bottom: 10px;
    }
    .index-tab .close-btn {
        margin-left: 4px;
        padding: 0 4px;
        font-size: 0.75rem;
        opacity: 0.6;
        border-radius: 3px;
    }
    .index-tab .close-btn:hover {
        opacity: 1;
        background: rgba(255,255,255,0.1);
    }
    .index-tab-add {
        padding: 6px 12px;
        background: transparent;
        border: 1px dashed #6b7280;
        border-bottom: none;
        border-radius: 8px 8px 0 0;
        color: #6b7280;
        font-size: 0.9rem;
        cursor: pointer;
    }
    .index-tab-add:hover {
        border-color: #10b981;
        color: #10b981;
    }
    /* タブボタンのテキスト折り返し禁止 */
    [data-testid="stButton"] button {
        white-space: nowrap !important;
    }
    .tab-content-area {
        border: 1px solid #374151;
        border-top: 2px solid #10b981;
        border-radius: 0 8px 8px 8px;
        padding: 16px;
        background: #1f2937;
        min-height: 200px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # タブ表示用のカラム数を計算
    num_tabs = len(st.session_state.tabs)
    cols = st.columns([1] * num_tabs + [1] + [max(1, 6 - num_tabs)])
    
    # 各タブ
    for i, tab in enumerate(st.session_state.tabs):
        with cols[i]:
            type_info = TAB_TYPES.get(tab["type"], TAB_TYPES["work"])
            is_active = st.session_state.active_tab == tab["id"]
            
            # タブボタンと×ボタン
            c1, c2 = st.columns([5, 1])
            with c1:
                btn_type = "primary" if is_active else "secondary"
                label = f"🗂️ {tab['name']}" if is_active else f"📁 {tab['name']}"
                if st.button(label, key=f"tab_{tab['id']}", type=btn_type, use_container_width=True):
                    st.session_state.active_tab = tab["id"]
                    st.rerun()
            with c2:
                if len(st.session_state.tabs) > 1:
                    if st.button("×", key=f"close_{tab['id']}", use_container_width=True):
                        remove_tab(tab["id"])
                        st.rerun()
    
    # +ボタン
    with cols[num_tabs]:
        with st.popover("＋"):
            st.markdown("**タブを追加**")
            if st.button("📝 新規作業", key="add_work", use_container_width=True):
                add_tab("work")
                st.rerun()
            
            # 🌐 ブラウザ（常に先頭に表示）
            has_browser = any(t["type"] == "browser" for t in st.session_state.tabs)
            if not has_browser:
                if st.button("🌐 ブラウザ", key="add_browser", use_container_width=True):
                    add_tab("browser")
                    st.rerun()
            
            # ✅ ToDo
            has_todo = any(t["type"] == "todo" for t in st.session_state.tabs)
            if not has_todo:
                if st.button("✅ ToDo", key="add_todo", use_container_width=True):
                    add_tab("todo")
                    st.rerun()
            
            # ⚙️ 設定
            has_settings = any(t["type"] == "settings" for t in st.session_state.tabs)
            if not has_settings:
                if st.button("⚙️ 設定", key="add_settings", use_container_width=True):
                    add_tab("settings")
                    st.rerun()
            
            # 🖥️ Mac操作
            has_mac = any(t["type"] == "mac" for t in st.session_state.tabs)
            if not has_mac:
                if st.button("🖥️ Mac操作", key="add_mac", use_container_width=True):
                    add_tab("mac")
                    st.rerun()
    
    # 区切り線（タブの下）
    st.markdown('<hr style="margin: 0 0 16px 0; border: none; border-top: 2px solid #10b981;">', unsafe_allow_html=True)
    
    return st.session_state.active_tab


def get_active_tab_type() -> str:
    """アクティブタブのタイプを取得"""
    for tab in st.session_state.tabs:
        if tab["id"] == st.session_state.active_tab:
            return tab["type"]
    return "work"
