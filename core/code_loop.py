# core/code_loop.py
# 行数: 41行
# コードレビューループ機能

import streamlit as st
from agents import call_coder, call_code_review, call_coder_fix

def code_with_review_loop(requirement: str, max_iterations: int = 3) -> dict:
    """コード生成→レビュー→修正のループ"""
    iterations = []
    
    # 初回コード生成
    st.write("**🔄 ループ1: コード生成中...**")
    code = call_coder(requirement)
    iterations.append({"type": "code", "content": code, "iteration": 1})
    
    for i in range(max_iterations):
        # レビュー
        st.write(f"**🔄 ループ{i+1}: コードレビュー中...**")
        review = call_code_review(code)
        iterations.append({"type": "review", "content": review["feedback"], "iteration": i+1})
        
        if review["approved"]:
            st.success(f"✅ レビュー通過！（{i+1}回目）")
            return {
                "final_code": code,
                "iterations": iterations,
                "approved": True,
                "total_iterations": i + 1
            }
        
        # 修正が必要
        if i < max_iterations - 1:
            st.warning(f"⚠️ 要修正（{i+1}回目）→ 修正中...")
            code = call_coder_fix(code, review["feedback"])
            iterations.append({"type": "fix", "content": code, "iteration": i+2})
    
    # 最大回数到達
    st.warning(f"⚠️ 最大{max_iterations}回のループ完了。最終版を返します。")
    return {
        "final_code": code,
        "iterations": iterations,
        "approved": False,
        "total_iterations": max_iterations
    }
