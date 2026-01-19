from __future__ import annotations

import json
from typing import Optional

import streamlit as st
import streamlit.components.v1 as components

from core.artifact_store import ArtifactStore


def _try_decode_text(data: bytes, mime_type: str) -> Optional[str]:
    mt = (mime_type or "").lower()

    text_like = (
        mt.startswith("text/")
        or mt in ("application/json", "application/xml", "application/javascript")
        or mt.endswith("+json")
        or mt.endswith("+xml")
    )

    if not text_like:
        return None

    try:
        return data.decode("utf-8")
    except Exception:
        try:
            return data.decode("utf-8", errors="replace")
        except Exception:
            return None


def _clipboard_button(label: str, text: str, key: str) -> None:
    payload = json.dumps(text)
    html = f"""
<div style="display:flex; gap:8px; align-items:center;">
  <button id="{key}" style="
    border-radius:9999px;
    padding:6px 12px;
    border:1px solid rgba(255,255,255,0.16);
    background:rgba(255,255,255,0.04);
    color:inherit;
    cursor:pointer;
    font-size:12px;
    line-height:1;
  ">{label}</button>
  <span id="{key}_status" style="font-size:12px; opacity:0.70;"></span>
</div>
<script>
(() => {{
  const btn = document.getElementById({json.dumps(key)});
  const status = document.getElementById({json.dumps(key + "_status")});
  if (!btn) return;

  const setStatus = (msg) => {{
    if (!status) return;
    status.textContent = msg || "";
    if (msg) {{
      setTimeout(() => {{ status.textContent = ""; }}, 1200);
    }}
  }};

  btn.addEventListener("click", async () => {{
    try {{
      await navigator.clipboard.writeText({payload});
      setStatus("copied");
    }} catch (e) {{
      try {{
        const ta = document.createElement("textarea");
        ta.value = {payload};
        ta.style.position = "fixed";
        ta.style.left = "-9999px";
        document.body.appendChild(ta);
        ta.focus();
        ta.select();
        document.execCommand("copy");
        document.body.removeChild(ta);
        setStatus("copied");
      }} catch (e2) {{
        setStatus("blocked");
      }}
    }}
  }});
}})();
</script>
"""
    components.html(html, height=38)


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
    border-radius: 12px;
    padding: 12px;
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

/* サイドバー内カラム重なり防止 */
[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] {
    flex-wrap: nowrap !important;
    min-width: 0 !important;
}
[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] > div {
    min-width: 0 !important;
    overflow: hidden !important;
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

    st.header("📎 添付（アップロード）")
    st.caption("会話に紐づけて保存します。GitHub退避で永続化してください。")

    show_uploader_key = "upload_panel_show_uploader"
    if show_uploader_key not in st.session_state:
        st.session_state[show_uploader_key] = True

    st.caption("質問してみましょう")
    st.write("")  # スペース

    # 1行目: テキストエリア（全幅）
    note = st.text_area(
        "message",
        value="",
        placeholder="メッセージを入力してください…",
        height=60,
        label_visibility="collapsed",
    )

    st.write("")  # スペース

    # 2行目: ボタン横並び
    btn_cols = st.columns(2)
    with btn_cols[0]:
        toggle = st.button("＋ 添付", key="upload_panel_btn_toggle_uploader", help="添付を表示/非表示", use_container_width=True)
        if toggle:
            st.session_state[show_uploader_key] = not st.session_state[show_uploader_key]

    with btn_cols[1]:
        files_for_disable = st.session_state.get("upload_panel_files_cache", None)
        disabled_send = not bool(files_for_disable)
        save_clicked = st.button(
            "⬆︎ 保存",
            key="upload_panel_btn_save",
            help="保存（この会話に紐づけ）",
            disabled=disabled_send,
            use_container_width=True,
        )

    st.write("")  # スペース

    if st.session_state[show_uploader_key]:
        files = st.file_uploader(
            "files",
            accept_multiple_files=True,
            label_visibility="collapsed",
        )
    else:
        files = []

    st.session_state["upload_panel_files_cache"] = files

    if not files:
        st.caption("＋で添付を選ぶと、⬆︎で保存できます。")

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

            meta_text = (
                f"filename: {a.filename}\n"
                f"size_bytes: {a.size_bytes}\n"
                f"mime: {a.mime_type}\n"
                f"sha256: {a.sha256}\n"
                f"artifact_id: {a.artifact_id}\n"
            )
            _clipboard_button("📋 メタ情報をコピー", meta_text, key=f"copy_meta_{a.artifact_id}")

            data = artifact_store.get_artifact_bytes(a.artifact_id)
            if a.mime_type.startswith("image/"):
                st.image(data, caption=a.filename, use_container_width=True)

            text = _try_decode_text(data, a.mime_type)
            if text is not None:
                clipped = text[:200_000]
                _clipboard_button("📋 内容をコピー（先頭20万文字）", clipped, key=f"copy_text_{a.artifact_id}")
                st.code(clipped[:5_000], language="")

            st.download_button(
                "⬇️ ダウンロード",
                data=data,
                file_name=a.filename,
                mime=a.mime_type,
                use_container_width=True,
                key=f"dl_{a.artifact_id}",
            )
