# ui/settings_tab.py
# 設定タブの実装
# 行数: 250行

import streamlit as st
from config import (
    GEMINI_KEY, OPENAI_KEY, ANTHROPIC_KEY, GROQ_KEY, XAI_KEY,
    AI_MODELS, DEFAULT_TEAM_CONFIG, get_team_config, set_team_config, reset_team_config
)
from agents.coder_team import CoderTeam
from agents.auditor_team import AuditorTeam
from agents.data_team import DataTeam
from agents.searcher_team import SearcherTeam

def render_settings_tab():
    """設定タブをレンダリング"""
    st.markdown('<div style="font-size: 1.5rem; font-weight: bold; margin-bottom: 1rem;">⚙️ 設定</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        _render_ai_settings()
        st.divider()
        _render_account_settings()
        st.divider()
        _render_team_composition()
    
    with col2:
        _render_service_connections()
        st.divider()
        _render_sharing_settings()
        st.divider()
        _render_system_info()
        st.divider()
        _render_team_evaluation()

def _render_ai_settings():
    """AIカスタム設定"""
    st.subheader("🤖 AIカスタム設定")
    
    st.markdown("🔄 **コードレビューループ**")
    use_loop = st.toggle("ループ有効", value=st.session_state.use_loop, key="settings_use_loop", label_visibility="collapsed")
    st.session_state.use_loop = use_loop
    
    if use_loop:
        max_loop = st.slider("最大ループ回数", 1, 5, st.session_state.max_loop, key="settings_max_loop")
        st.session_state.max_loop = max_loop
    
    st.markdown("📊 **クロスチェック機能**")
    use_crosscheck = st.toggle("クロスチェック有効", value=st.session_state.use_crosscheck, key="settings_use_crosscheck", label_visibility="collapsed")
    st.session_state.use_crosscheck = use_crosscheck
    
    response_style = st.selectbox("💬 デフォルト応答スタイル", ["簡潔", "詳細"], index=0 if st.session_state.response_style == "簡潔" else 1, key="settings_response_style")
    st.session_state.response_style = response_style
    
    st.markdown("💾 **自動保存**")
    auto_save = st.toggle("自動保存有効", value=st.session_state.auto_save, key="settings_auto_save", label_visibility="collapsed")
    st.session_state.auto_save = auto_save

def _render_account_settings():
    """アカウント設定"""
    st.subheader("👤 アカウント設定")
    
    skills_user_id = st.text_input("Skills User ID", value=st.session_state.skills_user_id, key="settings_skills_user_id", help="Skills Serverで取得したユーザーID")
    st.session_state.skills_user_id = skills_user_id
    
    display_name = st.text_input("表示名", value=st.session_state.display_name, key="settings_display_name")
    st.session_state.display_name = display_name
    
    user_email = st.text_input("メールアドレス", value=st.session_state.user_email, key="settings_user_email")
    st.session_state.user_email = user_email
    
    if st.button("🔐 パスワード変更", use_container_width=True):
        st.info("パスワード変更機能は準備中です")

def _render_team_composition():
    """チーム編成"""
    st.subheader("👥 チーム編成")
    if st.button("🔄 デフォルトに戻す", key="settings_reset", use_container_width=True):
        reset_team_config()
        st.rerun()
    
    ai_options = list(AI_MODELS.keys())
    ai_names = {k: v["name"] for k, v in AI_MODELS.items()}
    
    for team_key, team_default in DEFAULT_TEAM_CONFIG.items():
        with st.expander(f"**{team_default['name']}**", expanded=False):
            current = get_team_config(team_key)
            leader = st.selectbox("👑 長", ai_options, index=ai_options.index(current["leader"]), key=f"settings_{team_key}_leader", format_func=lambda x: ai_names[x])
            creator = st.selectbox("🔨 作成役", ai_options, index=ai_options.index(current["creator"]), key=f"settings_{team_key}_creator", format_func=lambda x: ai_names[x])
            checker = st.selectbox("🔍 チェック役", ai_options, index=ai_options.index(current["checker"]), key=f"settings_{team_key}_checker", format_func=lambda x: ai_names[x])
            if leader != current["leader"] or creator != current["creator"] or checker != current["checker"]:
                set_team_config(team_key, leader, creator, checker)

def _render_service_connections():
    """サービス連携"""
    st.subheader("🔗 サービス連携")
    
    st.markdown("**Google Drive**")
    gdrive_col1, gdrive_col2 = st.columns([3, 1])
    with gdrive_col1:
        st.markdown(f"状態: {'🟢 接続済み' if st.session_state.gdrive_connected else '🔴 未接続'}")
    with gdrive_col2:
        if st.button("接続" if not st.session_state.gdrive_connected else "解除", key="gdrive_btn"):
            st.session_state.gdrive_connected = not st.session_state.gdrive_connected
            st.rerun()
    
    st.markdown("**Slack**")
    slack_col1, slack_col2 = st.columns([3, 1])
    with slack_col1:
        st.markdown(f"状態: {'🟢 接続済み' if st.session_state.slack_connected else '🔴 未接続'}")
    with slack_col2:
        if st.button("接続" if not st.session_state.slack_connected else "解除", key="slack_btn"):
            st.session_state.slack_connected = not st.session_state.slack_connected
            st.rerun()
    
    st.markdown("**GitHub**")
    github_col1, github_col2 = st.columns([3, 1])
    with github_col1:
        st.markdown(f"状態: {'🟢 接続済み' if st.session_state.github_connected else '🔴 未接続'}")
    with github_col2:
        if st.button("接続" if not st.session_state.github_connected else "解除", key="github_btn"):
            st.session_state.github_connected = not st.session_state.github_connected
            st.rerun()
    
    st.markdown("**Skills Server**")
    st.markdown("[🔗 Skills Serverで管理](https://skills-server-a34a4.web.app/)")

def _render_sharing_settings():
    """共有設定"""
    st.subheader("🌐 共有設定")
    
    st.markdown("📁 **作業タブの共有を許可**")
    share_tabs = st.toggle("作業タブ共有", value=st.session_state.share_tabs, key="settings_share_tabs", label_visibility="collapsed")
    st.session_state.share_tabs = share_tabs
    
    st.markdown("👥 **チーム編成の共有**")
    share_team_config = st.toggle("チーム共有", value=st.session_state.share_team_config, key="settings_share_team", label_visibility="collapsed")
    st.session_state.share_team_config = share_team_config
    
    history_visibility = st.selectbox("履歴の公開範囲", ["自分のみ", "チームメンバー", "全員"], index=["自分のみ", "チームメンバー", "全員"].index(st.session_state.history_visibility), key="settings_history_visibility")
    st.session_state.history_visibility = history_visibility

def _render_system_info():
    """システム情報"""
    st.subheader("🔑 システム情報")
    
    st.markdown("**APIキー状態**")
    st.markdown(f"- Gemini: {'✅' if GEMINI_KEY else '❌'}")
    st.markdown(f"- OpenAI: {'✅' if OPENAI_KEY else '❌'}")
    st.markdown(f"- Anthropic: {'✅' if ANTHROPIC_KEY else '❌'}")
    st.markdown(f"- Groq: {'✅' if GROQ_KEY else '❌'}")
    st.markdown(f"- xAI: {'✅' if XAI_KEY else '❌'}")
    
    st.divider()
    
    st.markdown("**システム透明性**")
    try:
        from failure_tracker import FailureTracker
        tracker = FailureTracker()
        stats_24h = tracker.get_failure_rate(24)
        stats_7d = tracker.get_failure_rate(168)
        m1, m2 = st.columns(2)
        with m1:
            st.metric("24時間失敗率", f"{stats_24h['failure_rate']}%")
        with m2:
            st.metric("7日間失敗率", f"{stats_7d['failure_rate']}%")
        st.caption(f"総実行回数（24時間）: {stats_24h['total_executions']}回")
    except:
        st.caption("データ準備中...")

def _render_team_evaluation():
    """チーム評価システム"""
    st.subheader("🏆 チーム評価")
    
    try:
        from team_evaluator import get_evaluation_manager
        eval_manager = get_evaluation_manager()
        
        # 履歴ベースの統計表示
        st.markdown("**📊 チーム別パフォーマンス（30日間）**")
        all_teams = eval_manager.get_all_teams_comparison(days=30)
        
        if all_teams:
            for team in all_teams[:5]:
                score = team.get('avg_quality_score')
                score_color = "#10b981" if score and score >= 80 else "#f59e0b" if score and score >= 60 else "#ef4444"
                st.markdown(f'''
                <div style="background:#1e293b;border:1px solid #374151;border-radius:6px;padding:8px;margin:4px 0;">
                    <div style="font-weight:bold;color:#e5e7eb;">{team['team_key']}</div>
                    <div style="font-size:0.85rem;color:#9ca3af;">
                        品質: <span style="color:{score_color};font-weight:bold;">{score if score else '-'}点</span> | 
                        成功率: {team.get('success_rate', 0)}% | 
                        実行: {team.get('total_executions', 0)}回
                    </div>
                </div>
                ''', unsafe_allow_html=True)
        else:
            st.caption("評価データなし（実行すると蓄積されます）")
        
        st.markdown("---")
        
        # ベンチマークテスト
        _render_benchmark_test(eval_manager)
        
        st.markdown("---")
        
        # A/Bテスト  
        _render_ab_test(eval_manager)
        
    except Exception as e:
        st.caption(f"評価システム: {e}")

def _render_benchmark_test(eval_manager):
    """ベンチマークテスト"""
    st.markdown("**🎯 ベンチマークテスト**")
    benchmark_team = st.selectbox("テスト対象チーム", ["coder", "auditor", "data", "searcher"], key="benchmark_team_select")
    
    if st.button("🚀 ベンチマーク実行", key="run_benchmark", use_container_width=True):
        with st.spinner(f"🎯 {benchmark_team}チームのベンチマーク実行中..."):
            try:
                team_config = get_team_config(benchmark_team)
                
                def team_runner(task):
                    if benchmark_team == "coder":
                        team = CoderTeam()
                    elif benchmark_team == "auditor":
                        team = AuditorTeam()
                    elif benchmark_team == "data":
                        team = DataTeam()
                    else:
                        team = SearcherTeam()
                    result = team.run(task)
                    return result.get("final_result", "")
                
                result = eval_manager.run_benchmark(benchmark_team, team_config, team_runner)
                
                st.success(f"✅ ベンチマーク完了: 平均{result['avg_score']}点 / {result['avg_time']}秒")
                
                for task_result in result.get('task_results', []):
                    status = "✅" if task_result['success'] else "❌"
                    st.caption(f"{status} {task_result['name']}: {task_result['score']}点")
            except Exception as e:
                st.error(f"❌ ベンチマーク失敗: {e}")

def _render_ab_test(eval_manager):
    """A/Bテスト"""
    st.markdown("**⚖️ A/Bテスト**")
    ab_task = st.text_input("A/Bテスト用タスク", placeholder="Pythonでフィボナッチ数列を計算...", key="ab_test_task")
    
    ab_col1, ab_col2 = st.columns(2)
    with ab_col1:
        st.caption("チームA: 現在の設定")
    with ab_col2:
        ab_team_b = st.selectbox("チームB", ["coder", "auditor", "data", "searcher"], key="ab_team_b_select")
    
    if st.button("▶️ A/Bテスト実行", key="run_ab_test", use_container_width=True):
        if ab_task.strip():
            with st.spinner("⚖️ A/Bテスト実行中..."):
                try:
                    team_a_config = get_team_config("coder")
                    team_b_config = get_team_config(ab_team_b)
                    
                    def team_a_runner(task):
                        team = CoderTeam()
                        result = team.run(task)
                        return result.get("final_result", "")
                    
                    def team_b_runner(task):
                        if ab_team_b == "coder":
                            team = CoderTeam()
                        elif ab_team_b == "auditor":
                            team = AuditorTeam()
                        elif ab_team_b == "data":
                            team = DataTeam()
                        else:
                            team = SearcherTeam()
                        result = team.run(task)
                        return result.get("final_result", "")
                    
                    result = eval_manager.run_ab_test(
                        ab_task, team_a_config, team_b_config,
                        team_a_runner, team_b_runner
                    )
                    
                    winner_text = "🏆 チームA勝利" if result['winner'] == 'team_a' else "🏆 チームB勝利" if result['winner'] == 'team_b' else "🤝 引き分け"
                    st.success(winner_text)
                    
                    r_col1, r_col2 = st.columns(2)
                    with r_col1:
                        st.markdown(f"**チームA**: {result['team_a']['time']:.2f}秒")
                    with r_col2:
                        st.markdown(f"**チームB**: {result['team_b']['time']:.2f}秒")
                except Exception as e:
                    st.error(f"❌ A/Bテスト失敗: {e}")
        else:
            st.warning("タスクを入力してください")
