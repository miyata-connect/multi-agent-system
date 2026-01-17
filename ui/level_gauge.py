# /Users/miyatayasuhiro/Desktop/multi-agent-system/ui/level_gauge.py
# -*- coding: utf-8 -*-
"""
退避レベルゲージ（視認性重視）
- 会話ZIP生成済み
- 添付（Artifacts）保存済み
- GitHub Issue退避済み
上記の達成状況を 0〜100 で表示します。

※B（Issue自動退避）実装時に st.session_state のフラグを確定させます。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

import streamlit as st


@dataclass(frozen=True)
class BackupGaugeState:
    conversation_exported: bool
    artifacts_saved: bool
    github_issue_pushed: bool

    @staticmethod
    def from_session() -> "BackupGaugeState":
        return BackupGaugeState(
            conversation_exported=bool(st.session_state.get("backup_conversation_exported", False)),
            artifacts_saved=bool(st.session_state.get("backup_artifacts_saved", False)),
            github_issue_pushed=bool(st.session_state.get("backup_github_issue_pushed", False)),
        )


def _score(state: BackupGaugeState) -> Tuple[int, Dict[str, bool]]:
    # 重要度：会話40 / 添付40 / Issue20（IssueはBで実装）
    parts: Dict[str, bool] = {
        "会話ZIP": state.conversation_exported,
        "添付": state.artifacts_saved,
        "GitHub Issue": state.github_issue_pushed,
    }

    score = 0
    score += 40 if parts["会話ZIP"] else 0
    score += 40 if parts["添付"] else 0
    score += 20 if parts["GitHub Issue"] else 0
    return score, parts


def render_backup_level_gauge() -> None:
    """
    サイドバー向け表示。
    呼び出し側で st.sidebar 内に置く前提。
    """
    state = BackupGaugeState.from_session()
    score, parts = _score(state)

    ok = "✅"
    ng = "⬜️"

    st.subheader("📈 退避レベル")
    st.progress(score / 100.0)

    st.metric("達成度", f"{score}/100")

    st.caption("チェック項目")
    st.write(f"- {ok if parts[\"会話ZIP\"] else ng} 会話ZIP")
    st.write(f"- {ok if parts[\"添付\"] else ng} 添付")
    st.write(f"- {ok if parts[\"GitHub Issue\"] else ng} GitHub Issue")

    # 状態に応じた短い指示
    if score == 0:
        st.info("まずは会話と添付を保存できる状態にします（A→Bの順で実装）。")
    elif score < 80:
        st.info("会話ZIP/添付のどちらかが未達です。次の実装で埋めます。")
    elif score < 100:
        st.info("最後に GitHub Issue 退避（B）をつなげると100になります。")
    else:
        st.success("退避フローが完了しています。")
