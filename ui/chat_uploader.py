# ui/chat_uploader.py
# チャット用ファイルアップロードUI（ChatGPT風コンパクト版）

import streamlit as st
from pathlib import Path
from typing import List
import mimetypes
import uuid


ALLOWED_EXTENSIONS = {
    'jpg', 'jpeg', 'png', 'gif', 'webp', 'svg',
    'mp4', 'mov', 'webm',
    'pdf', 'docx', 'xlsx', 'pptx', 'txt', 'md',
    'json', 'csv', 'xml',
    'zip', 'tar', 'gz',
    'py', 'js', 'ts', 'html', 'css', 'sql', 'yaml', 'yml',
}

MAX_FILE_SIZE_MB = 1024  # 1GB


def get_file_icon(filename: str) -> str:
    ext = Path(filename).suffix.lower().lstrip('.')
    icons = {
        'jpg': '🖼️', 'jpeg': '🖼️', 'png': '🖼️', 'gif': '🖼️', 'webp': '🖼️', 'svg': '🖼️',
        'mp4': '🎬', 'mov': '🎬', 'webm': '🎬',
        'pdf': '📕', 'docx': '📘', 'xlsx': '📗', 'pptx': '📙', 'txt': '📄', 'md': '📝',
        'json': '📊', 'csv': '📊', 'xml': '📊',
        'zip': '📦', 'tar': '📦', 'gz': '📦',
        'py': '🐍', 'js': '💛', 'ts': '💙', 'html': '🌐', 'css': '🎨', 'sql': '🗃️',
    }
    return icons.get(ext, '📎')


def format_file_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes}B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f}KB"
    return f"{size_bytes / (1024 * 1024):.1f}MB"


def render_chat_uploader():
    """ChatGPT風コンパクトアップロードUI - 入力欄の左に配置"""
    
    if "chat_uploaded_files" not in st.session_state:
        st.session_state.chat_uploaded_files = []
    
    # ポップオーバーでアップロードUI
    with st.popover("📎 添付", help="ファイルを添付", use_container_width=False):
        # 対応ファイル形式
        st.caption("対応形式: JPEG, PNG, CSV, XLSX, CSS, WEBM, HTML, YAML, PDF, DOCX 等")
        
        uploaded_files = st.file_uploader(
            "ファイルを選択",
            type=list(ALLOWED_EXTENSIONS),
            accept_multiple_files=True,
            key="chat_file_uploader",
            label_visibility="collapsed"
        )
        
        if uploaded_files:
            for file in uploaded_files:
                file_size = len(file.getvalue())
                if file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
                    st.warning(f"⚠️ {file.name}は大きすぎます")
                    continue
                
                existing = [f['name'] for f in st.session_state.chat_uploaded_files]
                if file.name not in existing:
                    # 一意のIDを付与
                    file_id = uuid.uuid4().hex[:8]
                    st.session_state.chat_uploaded_files.append({
                        'id': file_id,
                        'name': file.name,
                        'size': file_size,
                        'type': file.type or mimetypes.guess_type(file.name)[0],
                        'data': file.getvalue(),
                    })
        
        # 添付済み一覧
        if st.session_state.chat_uploaded_files:
            st.markdown("**添付済み:**")
            files_to_remove = []
            for f in st.session_state.chat_uploaded_files:
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.caption(f"{get_file_icon(f['name'])} {f['name']} ({format_file_size(f['size'])})")
                with col2:
                    # 一意のkeyを使用
                    if st.button("✕", key=f"rm_file_{f['id']}"):
                        files_to_remove.append(f['id'])
            
            # 削除処理
            if files_to_remove:
                st.session_state.chat_uploaded_files = [
                    f for f in st.session_state.chat_uploaded_files 
                    if f['id'] not in files_to_remove
                ]
                st.rerun()
    
    # 添付済みファイルがあれば下に表示（削除ボタン付き）
    if st.session_state.chat_uploaded_files:
        st.markdown("---")
        st.caption("📎 **添付ファイル:**")
        files_to_remove = []
        for f in st.session_state.chat_uploaded_files:
            col1, col2 = st.columns([6, 1])
            with col1:
                icon = get_file_icon(f['name'])
                st.markdown(f"{icon} **{f['name']}** ({format_file_size(f['size'])})")
            with col2:
                if st.button("❌", key=f"remove_attached_{f['id']}", help="削除"):
                    files_to_remove.append(f['id'])
        
        # 削除処理
        if files_to_remove:
            st.session_state.chat_uploaded_files = [
                f for f in st.session_state.chat_uploaded_files 
                if f['id'] not in files_to_remove
            ]
            st.rerun()


def get_uploaded_files_for_prompt() -> str:
    """プロンプト用テキスト変換"""
    files = st.session_state.get("chat_uploaded_files", [])
    if not files:
        return ""
    
    parts = ["\n\n【添付ファイル】"]
    for f in files:
        ext = Path(f['name']).suffix.lower()
        if ext in ['.txt', '.md', '.py', '.js', '.ts', '.html', '.css', '.sql', '.json', '.csv', '.xml', '.yaml', '.yml']:
            try:
                content = f['data'].decode('utf-8')
                parts.append(f"\n--- {f['name']} ---\n```\n{content[:5000]}{'...' if len(content) > 5000 else ''}\n```")
            except:
                parts.append(f"\n- {f['name']} ({format_file_size(f['size'])})")
        else:
            parts.append(f"\n- {f['name']} ({format_file_size(f['size'])})")
    return '\n'.join(parts)


def clear_uploaded_files():
    st.session_state.chat_uploaded_files = []
