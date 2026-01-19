# ui/parts_panel.py
# 行数: 195行
# 作業パーツ管理UIパネル（ファイルアップロード対応版）

import streamlit as st
from datetime import datetime
from dev_manager import PartsStore
from pathlib import Path


def render_parts_panel():
    """サイドバー用の作業パーツ管理パネル"""
    
    if "parts_store" not in st.session_state:
        st.session_state.parts_store = PartsStore()
    
    store = st.session_state.parts_store
    
    st.header("📦 作業パーツ")
    
    # 新規作成
    with st.expander("＋ 新規パーツ作成", expanded=False):
        new_name = st.text_input("パーツ名", key="new_part_name", placeholder="例: 認証機能")
        new_desc = st.text_area("説明", key="new_part_desc", placeholder="このパーツの説明", height=60)
        
        if st.button("作成", key="create_part_btn", use_container_width=True):
            if new_name.strip():
                part = store.create_part(new_name.strip(), new_desc.strip())
                st.success(f"✅ 「{part['name']}」を作成しました")
                st.rerun()
            else:
                st.warning("パーツ名を入力してください")
    
    st.divider()
    
    # パーツ一覧
    parts = store.get_all_parts()
    
    if not parts:
        st.info("パーツがありません。新規作成してください。")
        return
    
    for part in parts:
        render_part_card(store, part)


def render_part_card(store: PartsStore, part: dict):
    """個別パーツカード表示"""
    
    part_id = part['id']
    progress = part['progress']
    status = part['status']
    
    status_icons = {
        'in_progress': '🔄',
        'completed': '✅',
        'pending': '⏳',
        'review': '📝',
    }
    status_icon = status_icons.get(status, '📦')
    
    if progress >= 100:
        bar_color = "#10b981"
    elif progress >= 50:
        bar_color = "#f59e0b"
    else:
        bar_color = "#3b82f6"
    
    with st.container():
        st.markdown(f"""
        <div style="
            background: #1e293b;
            border: 1px solid #374151;
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 8px;
        ">
            <div style="font-weight: bold; margin-bottom: 4px;">
                {status_icon} {part['name']} <span style="color: #6b7280; font-size: 0.8rem;">{part['version']}</span>
            </div>
            <div style="color: #9ca3af; font-size: 0.85rem; margin-bottom: 8px;">
                進捗率: {progress}% {'✅完了' if progress >= 100 else ''}
            </div>
            <div style="
                background: #374151;
                border-radius: 4px;
                height: 8px;
                overflow: hidden;
                margin-bottom: 8px;
            ">
                <div style="
                    background: {bar_color};
                    height: 100%;
                    width: {progress}%;
                    transition: width 0.3s;
                "></div>
            </div>
            <div style="color: #6b7280; font-size: 0.75rem;">
                最終保存: {format_datetime(part['updated_at'])}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            if st.button("📝", key=f"edit_{part_id}", help="編集"):
                st.session_state.editing_part_id = part_id
                st.rerun()
        
        with col2:
            if st.button("📥", key=f"dl_{part_id}", help="ダウンロード"):
                download_part(store, part)
        
        with col3:
            if st.button("🗑", key=f"del_{part_id}", help="削除"):
                st.session_state.deleting_part_id = part_id
                st.rerun()
    
    if st.session_state.get("editing_part_id") == part_id:
        render_edit_modal(store, part)
    
    if st.session_state.get("deleting_part_id") == part_id:
        render_delete_confirm(store, part)


def render_edit_modal(store: PartsStore, part: dict):
    """パーツ編集モーダル（ファイルアップロード対応）"""
    
    with st.expander(f"✏️ 「{part['name']}」を編集中", expanded=True):
        name = st.text_input("パーツ名", value=part['name'], key=f"edit_name_{part['id']}")
        desc = st.text_area("説明", value=part['description'], key=f"edit_desc_{part['id']}", height=60)
        version = st.text_input("バージョン", value=part['version'], key=f"edit_ver_{part['id']}")
        progress = st.slider("進捗率", 0, 100, part['progress'], key=f"edit_prog_{part['id']}")
        
        # 内容入力（テキストエリア）
        content = st.text_area("内容（コード・メモ）", value=part['content'], key=f"edit_content_{part['id']}", height=150)
        
        # ファイルアップロード（パーツ更新用）
        st.markdown("**📎 ファイルで更新**")
        uploaded_file = st.file_uploader(
            "ファイルをドロップまたは選択",
            type=['txt', 'md', 'py', 'js', 'ts', 'html', 'css', 'json', 'csv', 'sql', 'yaml', 'yml'],
            key=f"part_upload_{part['id']}",
            help="テキスト・コードファイルの内容でパーツを更新"
        )
        
        # アップロードされたファイルの内容をプレビュー
        uploaded_content = None
        if uploaded_file:
            try:
                uploaded_content = uploaded_file.getvalue().decode('utf-8')
                st.code(uploaded_content[:500] + ('...' if len(uploaded_content) > 500 else ''), language=get_language(uploaded_file.name))
                st.caption(f"📄 {uploaded_file.name} ({len(uploaded_content)} 文字)")
            except Exception as e:
                st.error(f"ファイル読み込みエラー: {e}")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 保存", key=f"save_{part['id']}", use_container_width=True):
                # アップロードファイルがあればその内容を使用
                final_content = uploaded_content if uploaded_content else content
                
                store.update_part(
                    part['id'],
                    name=name,
                    description=desc,
                    version=version,
                    progress=progress,
                    content=final_content
                )
                st.session_state.editing_part_id = None
                st.success("✅ 保存しました")
                st.rerun()
        
        with col2:
            if st.button("❌ キャンセル", key=f"cancel_{part['id']}", use_container_width=True):
                st.session_state.editing_part_id = None
                st.rerun()


def render_delete_confirm(store: PartsStore, part: dict):
    """削除確認"""
    
    st.warning(f"「{part['name']}」を削除しますか？")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑 削除", key=f"confirm_del_{part['id']}", use_container_width=True):
            store.delete_part(part['id'])
            st.session_state.deleting_part_id = None
            st.rerun()
    
    with col2:
        if st.button("キャンセル", key=f"cancel_del_{part['id']}", use_container_width=True):
            st.session_state.deleting_part_id = None
            st.rerun()


def download_part(store: PartsStore, part: dict):
    """パーツダウンロード"""
    
    md_content = store.export_part_md(part['id'])
    if md_content:
        st.download_button(
            label=f"📄 {part['name']}.md",
            data=md_content,
            file_name=f"{part['name']}_{part['version']}.md",
            mime="text/markdown",
            key=f"dl_md_{part['id']}"
        )


def format_datetime(dt_str: str) -> str:
    try:
        dt = datetime.fromisoformat(dt_str)
        return dt.strftime("%m-%d %H:%M")
    except:
        return dt_str


def get_language(filename: str) -> str:
    """ファイル拡張子からコード言語を判定"""
    ext = Path(filename).suffix.lower()
    lang_map = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.html': 'html',
        '.css': 'css',
        '.json': 'json',
        '.sql': 'sql',
        '.yaml': 'yaml',
        '.yml': 'yaml',
        '.md': 'markdown',
    }
    return lang_map.get(ext, 'text')
