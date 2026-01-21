# ui/tabs.py
# タブ管理モジュール（インデックスタブデザイン + ダブルクリック編集）

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
            {"id": "work_1", "type": "work", "name": "作業1"},
            {"id": "settings", "type": "settings", "name": "設定"}
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
    if "editing_tab" not in st.session_state:
        st.session_state.editing_tab = None


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


def rename_tab(tab_id: str, new_name: str):
    """タブ名を変更"""
    for tab in st.session_state.tabs:
        if tab["id"] == tab_id:
            tab["name"] = new_name
            break


def render_tab_bar():
    """インデックスタブ（フォルダ型）をレンダリング"""
    init_tabs()
    
    # インデックスタブ用CSS
    st.markdown("""
    <style>
    /* タブボタンのテキスト折り返し禁止 */
    [data-testid="stButton"] button {
        white-space: nowrap !important;
    }
    
    /* タブ名ダブルクリック用スタイル */
    .tab-name-display {
        cursor: text;
        user-select: none;
    }
    .tab-name-display:hover {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 4px;
        padding: 2px 4px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # タブ表示
    num_tabs = len(st.session_state.tabs)
    cols = st.columns([1] * num_tabs + [1] + [max(1, 6 - num_tabs)])
    
    # 各タブ
    for i, tab in enumerate(st.session_state.tabs):
        with cols[i]:
            type_info = TAB_TYPES.get(tab["type"], TAB_TYPES["work"])
            is_active = st.session_state.active_tab == tab["id"]
            is_editing = st.session_state.editing_tab == tab["id"]
            
            btn_type = "primary" if is_active else "secondary"
            icon = "🗂️" if is_active else "📁"
            
            # 編集モード（作業タブのみ）
            if is_editing and tab["type"] == "work":
                tab_col1, tab_col2 = st.columns([4, 1])
                with tab_col1:
                    new_name = st.text_input(
                        "タブ名", 
                        value=tab["name"], 
                        key=f"rename_{tab['id']}", 
                        label_visibility="collapsed",
                        placeholder="タブ名を入力...",
                        on_change=lambda: _finish_editing(tab["id"])
                    )
                    # Enterキーで確定
                    if new_name != tab["name"]:
                        rename_tab(tab["id"], new_name)
                with tab_col2:
                    if st.button("✓", key=f"confirm_{tab['id']}", use_container_width=True, help="確定"):
                        st.session_state.editing_tab = None
                        st.rerun()
            else:
                # 通常表示
                tab_col1, tab_col2 = st.columns([4, 1])
                with tab_col1:
                    label = f"{icon} {tab['name']}"
                    
                    # ダブルクリック検出用（作業タブのみ）
                    if tab["type"] == "work":
                        # ボタンとして表示
                        button_clicked = st.button(
                            label, 
                            key=f"tab_{tab['id']}", 
                            type=btn_type, 
                            use_container_width=True,
                            help="ダブルクリックで名前変更"
                        )
                        
                        if button_clicked:
                            # シングルクリック：タブ切り替え
                            if st.session_state.active_tab != tab["id"]:
                                st.session_state.active_tab = tab["id"]
                                st.rerun()
                            # ダブルクリック検出用に編集モードチェックボックスを追加
                            elif is_active:
                                # アクティブタブを再クリック = 編集モード
                                st.session_state.editing_tab = tab["id"]
                                st.rerun()
                    else:
                        # 作業タブ以外は通常ボタン
                        if st.button(label, key=f"tab_{tab['id']}", type=btn_type, use_container_width=True):
                            st.session_state.active_tab = tab["id"]
                            st.rerun()
                
                with tab_col2:
                    # ×ボタン（設定タブ以外）
                    if len(st.session_state.tabs) > 1 and tab["type"] != "settings":
                        if st.button("×", key=f"close_{tab['id']}", use_container_width=True, help="タブを閉じる"):
                            remove_tab(tab["id"])
                            st.rerun()
    
    # +ボタン
    with cols[num_tabs]:
        with st.popover("＋"):
            st.markdown("**タブを追加**")
            if st.button("📝 新規作業", key="add_work", use_container_width=True):
                add_tab("work")
                st.rerun()
            
            # 🌐 ブラウザ
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
    
    # 区切り線
    st.markdown('<hr style="margin: 0 0 16px 0; border: none; border-top: 2px solid #10b981;">', unsafe_allow_html=True)
    
    return st.session_state.active_tab


def _finish_editing(tab_id: str):
    """編集モード終了"""
    st.session_state.editing_tab = None


def get_active_tab_type() -> str:
    """アクティブタブのタイプを取得"""
    for tab in st.session_state.tabs:
        if tab["id"] == st.session_state.active_tab:
            return tab["type"]
    return "work"
