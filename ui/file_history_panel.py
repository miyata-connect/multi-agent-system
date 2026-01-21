# ui/file_history_panel.py
# ファイル履歴表示・復元UIコンポーネント
# 行数: 160行

import streamlit as st
from datetime import datetime
from file_version_manager import file_version_manager
import difflib

def format_file_size(size_bytes: int) -> str:
    """ファイルサイズを読みやすい形式に変換"""
    if size_bytes < 1024:
        return f"{size_bytes}B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f}KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f}MB"

def format_datetime(dt_str: str) -> str:
    """日時を読みやすい形式に変換"""
    try:
        dt = datetime.fromisoformat(dt_str)
        return dt.strftime("%Y年%m月%d日 %H:%M:%S")
    except:
        return dt_str

def render_file_history_panel():
    """ファイル履歴パネルを表示"""
    
    st.markdown("### 📂 ファイル履歴")
    
    # 統計情報
    stats = file_version_manager.get_stats()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("ファイル数", stats['unique_files'])
    with col2:
        st.metric("バージョン数", stats['total_versions'])
    with col3:
        st.metric("総サイズ", f"{stats['total_size_mb']}MB")
    
    st.caption("保存期間: 3日間")
    
    st.divider()
    
    # 管理中のファイル一覧
    files = file_version_manager.get_all_files()
    
    if not files:
        st.info("📭 まだファイル履歴がありません")
        return
    
    # ファイル選択
    selected_file = st.selectbox(
        "ファイルを選択",
        files,
        key="file_history_select",
        format_func=lambda x: x.split('/')[-1] if '/' in x else x
    )
    
    if not selected_file:
        return
    
    st.markdown(f"**選択中:** `{selected_file}`")
    st.divider()
    
    # ファイルの履歴取得
    history = file_version_manager.get_file_history(selected_file, limit=20)
    
    if not history:
        st.warning("このファイルの履歴が見つかりません")
        return
    
    st.markdown("#### 📜 バージョン履歴")
    
    # バージョンリスト表示
    for version_info in history:
        version = version_info['version']
        updated_at = version_info['updated_at']
        file_size = version_info['file_size']
        
        # バージョンカード
        with st.container():
            col_info, col_action = st.columns([3, 1])
            
            with col_info:
                st.markdown(f"**バージョン {version}**")
                st.caption(f"🕒 {format_datetime(updated_at)} | 📦 {format_file_size(file_size)}")
            
            with col_action:
                # 詳細表示ボタン
                if st.button("👁️ 表示", key=f"view_{selected_file}_{version}", use_container_width=True):
                    st.session_state['view_version'] = {
                        'file_path': selected_file,
                        'version': version
                    }
                    st.rerun()
                
                # 復元ボタン
                if st.button("🔄 復元", key=f"restore_{selected_file}_{version}", use_container_width=True):
                    restore_file_version(selected_file, version)
            
            st.markdown("---")
    
    # クリーンアップボタン
    if st.button("🗑️ 古いバージョンを削除", use_container_width=True):
        deleted = file_version_manager.cleanup_old_versions()
        st.success(f"✅ {deleted}件の古いバージョンを削除しました")
        st.rerun()

def render_version_detail():
    """選択されたバージョンの詳細を表示"""
    if 'view_version' not in st.session_state:
        return
    
    view_data = st.session_state['view_version']
    file_path = view_data['file_path']
    version = view_data['version']
    
    # バージョンデータ取得
    version_data = file_version_manager.get_version(file_path, version)
    
    if not version_data:
        st.error("バージョンデータが見つかりません")
        if st.button("✖️ 閉じる"):
            del st.session_state['view_version']
            st.rerun()
        return
    
    st.markdown(f"## 📄 {file_path.split('/')[-1]}")
    st.markdown(f"**バージョン:** {version}")
    st.markdown(f"**更新日時:** {format_datetime(version_data['updated_at'])}")
    st.markdown(f"**サイズ:** {format_file_size(version_data['file_size'])}")
    st.divider()
    
    # 内容表示
    st.markdown("### 📝 内容")
    st.code(version_data['content'], language="python" if file_path.endswith('.py') else None)
    
    st.divider()
    
    # ボタン
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 このバージョンを復元", key="restore_from_detail", use_container_width=True):
            restore_file_version(file_path, version)
    
    with col2:
        if st.button("✖️ 閉じる", key="close_version_detail", use_container_width=True):
            del st.session_state['view_version']
            st.rerun()

def restore_file_version(file_path: str, version: int):
    """ファイルバージョンを復元"""
    try:
        # バージョン内容を取得
        content = file_version_manager.restore_version(file_path, version)
        
        if content is None:
            st.error("復元に失敗しました")
            return
        
        # セッションステートに復元内容を保存（後で実際のファイルに書き込むかユーザーが決定）
        st.session_state['restored_file'] = {
            'file_path': file_path,
            'version': version,
            'content': content
        }
        
        st.success(f"✅ バージョン{version}を復元しました！")
        st.info("💡 復元内容は一時保存されています。ファイルに書き込む場合は下のボタンをクリックしてください。")
        
        # 復元内容プレビュー
        with st.expander("📄 復元内容を確認"):
            st.code(content[:1000] + ("..." if len(content) > 1000 else ""), language="python" if file_path.endswith('.py') else None)
        
        # ファイルに書き込むボタン
        if st.button("💾 ファイルに書き込む", key="write_restored_file", use_container_width=True):
            write_restored_file_to_disk(file_path, content)
        
    except Exception as e:
        st.error(f"復元エラー: {e}")
        import traceback
        st.code(traceback.format_exc())

def write_restored_file_to_disk(file_path: str, content: str):
    """復元内容を実際のファイルに書き込む"""
    try:
        # ファイルパスの存在確認・作成
        from pathlib import Path
        file_obj = Path(file_path)
        file_obj.parent.mkdir(parents=True, exist_ok=True)
        
        # ファイル書き込み
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        st.success(f"✅ ファイルに書き込みました: {file_path}")
        
        # セッションステートクリア
        if 'restored_file' in st.session_state:
            del st.session_state['restored_file']
        
        st.rerun()
        
    except Exception as e:
        st.error(f"ファイル書き込みエラー: {e}")
