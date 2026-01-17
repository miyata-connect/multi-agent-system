from __future__ import annotations

import streamlit as st

from core.artifact_store import ArtifactStore


def render_upload_panel(artifact_store: ArtifactStore, conversation_id: str) -> None:
    st.markdown(
        """
<style>
/* ------------------------------------------------------------
   ChatGPT-like Composer (Streamlit-safe, minimal invasive)
   NOTE: Streamlit DOM can change; adjust selectors if needed.
------------------------------------------------------------ */

.upload-composer-wrap {
    border: 1px solid rgba(255, 255, 255, 0.16);
    border-radius: 9999px;
    padding: 10px 12px;
    background: rgba(255, 255, 255, 0.04);
}

.upload-composer-wrap:focus-within {
    border-color: rgba(46, 204, 113, 0.85);
    box-shadow: 0 0 0 3px rgba(46, 204, 113, 0.18);
}

.upload-composer-hint {
    font-size: 12px;
    opacity: 0.70;
    margin: 0 0 8px 0;
}

.upload-composer-row {
    display: flex;
    gap: 10px;
    align-items: flex-end;
}

.upload-composer-tools {
    display: flex;
    gap: 8px;
    align-items: center;
    padding-bottom: 2px;
}

.upload-composer-send {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    padding-bottom: 2px;
}

/* Hide default Streamlit labels for collapsed inputs (safety) */
div[data-testid="stWidgetLabel"] {
    display: none;
}

/* Text area styling (best-effort) */
div[data-testid="stTextArea"] textarea {
    border: none !important;
    outline: none !important;
    background: transparent !important;
    box-shadow: none !important;
    padding: 0 !important;
    margin: 0 !important;
    resize: none !important;
    font-size: 16px !important;
    line-height: 1.45 !important;
}

/* Remove default textarea wrapper padding/border (best-effort) */
div[data-testid="stTextArea"] > div {
    border: none !important;
    box-shadow: none !important;
    background: transparent !important;
    padding: 0 !important;
}

/* Make buttons round (best-effort) */
button[kind="secondary"],
button[kind="primary"] {
    border-radius: 9999px !important;
}

/* Tool button smaller */
.upload-tool-btn button {
    padding: 0.30rem 0.65rem !important;
    min-height: 2.2rem !important;
}

/* Send button more "icon-like" */
.upload-send-btn button {
    padding: 0.30rem 0.85rem !important;
    min-height: 2.2rem !important;
}

/* Uploader area: subtle */
div[data-testid="stFileUploader"] section {
    border-radius: 16px !important;
}
</style>
        """,
        unsafe_allow_html=True,
    )

    st.divider()
    st.header("📎 添付（アップロード）")
    st.caption("会話に紐づけて保存します。GitHub退避で永続化してください。")

    # -----------------------------
    # ChatGPT-like composer state
    # -----------------------------
    show_uploader_key = "upload_panel_show_uploader"
    if show_uploader_key not in st.session_state:
        st.session_state[show_uploader_key] = True

    # -----------------------------
    # Composer UI (ChatGPT-like)
    # -----------------------------
    st.markdown('<div class="upload-composer-wrap">', unsafe_allow_html=True)
    st.markdown('<div class="upload-composer-hint">質問してみましょう</div>', unsafe_allow_html=True)

    cols = st.columns([0.16, 0.68, 0.16], gap="small")

    with cols[0]:
        st.markdown('<div class="upload-composer-tools upload-tool-btn">', unsafe_allow_html=True)
        toggle = st.button("＋", key="upload_panel_btn_toggle_uploader", help="添付を表示/非表示")
        st.markdown("</div>", unsafe_allow_html=True)

        if toggle:
            st.session_state[show_uploader_key] = not st.session_state[show_uploader_key]

    with cols[1]:
        note = st.text_area(
            "message",
            value="",
            placeholder="メッセージを入力してください…",
            height=86,
            label_visibility="collapsed",
        )

    with cols[2]:
        st.markdown('<div class="upload-composer-send upload-send-btn">', unsafe_allow_html=True)

        files_for_disable = st.session_state.get("upload_panel_files_cache", None)
        disabled_send = not bool(files_for_disable)

        save_clicked = st.button(
            "⬆︎",
            key="upload_panel_btn_save",
            help="保存（この会話に紐づけ）",
            disabled=disabled_send,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # -----------------------------
    # Attachment picker (toggleable)
    # -----------------------------
    files = None
    if st.session_state[show_uploader_key]:
        files = st.file_uploader(
            "files",
            accept_multiple_files=True,
            label_visibility="collapsed",
        )
    else:
        files = []

    # Keep latest selection for disabling/enabling send button
    st.session_state["upload_panel_files_cache"] = files

    # Guidance below composer (small)
    if not files:
        st.caption("＋で添付を選ぶと、⬆︎で保存できます。")

    # -----------------------------
    # Save logic (unchanged behavior)
    # -----------------------------
    if save_clicked:
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

    # -----------------------------
    # List artifacts (unchanged)
    # -----------------------------
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