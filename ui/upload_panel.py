from __future__ import annotations

import streamlit as st

from core.artifact_store import ArtifactStore


def render_upload_panel(artifact_store: ArtifactStore, conversation_id: str) -> None:
    st.divider()
    st.header("📎 添付（アップロード）")
    st.caption("会話に紐づけて保存します。GitHub退避で永続化してください。")

    note = st.text_input("添付メモ（任意）", value="", placeholder="例: 仕様スクショ、過去コード、要件メモ")
    files = st.file_uploader("ファイルを選択", accept_multiple_files=True)

    if st.button("⬆️ 保存（この会話に紐づけ）", use_container_width=True, disabled=not files):
        ok = 0
        ng = 0
        for f in files or []:
            try:
                artifact_store.add_artifact(
                    conversation_id=conversation_id,
                    filename=f.name,
                    mime_type=f.type or "application/octet-stream",
                    data=f.getvalue(),
                    note=note,
                )
                ok += 1
            except Exception as e:
                ng += 1
                st.error(f"保存失敗: {f.name} / {e}")

        if ok:
            st.success(f"保存しました: {ok}件")
        if ng:
            st.warning(f"失敗: {ng}件")

    items = artifact_store.list_artifacts(conversation_id, limit=200)
    if not items:
        st.caption("まだ添付はありません。")
        return

    st.subheader("📄 添付一覧")
    for a in items:
        with st.expander(f"{a.filename}  ({a.size_bytes} bytes)", expanded=False):
            st.caption(f"artifact_id: {a.artifact_id}")
            if a.note:
                st.write(f"メモ: {a.note}")
            st.caption(f"mime: {a.mime_type}")
            st.caption(f"sha256: {a.sha256}")

            data = artifact_store.get_artifact_bytes(a.artifact_id)
            if a.mime_type.startswith("image/"):
                st.image(data, caption=a.filename, use_container_width=True)

            st.download_button(
                "⬇️ ダウンロード",
                data=data,
                file_name=a.filename,
                mime=a.mime_type,
                use_container_width=True,
                key=f"dl_{a.artifact_id}",
            )
