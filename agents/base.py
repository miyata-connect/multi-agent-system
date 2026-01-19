# agents/base.py
# 行数: 148行
# チーム共通ロジック（AI取得・並列実行・調停）

import asyncio
from typing import Any, Callable, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_groq import ChatGroq

from config import (
    AI_MODELS,
    GEMINI_KEY, OPENAI_KEY, ANTHROPIC_KEY, GROQ_KEY, XAI_KEY,
    get_team_config,
)

# ==========================================
# AI インスタンス取得
# ==========================================
def get_ai_instance(ai_key: str, temperature: float = 0):
    """AI キーからLangChainインスタンスを取得"""
    if ai_key not in AI_MODELS:
        raise ValueError(f"Unknown AI: {ai_key}")
    
    model_info = AI_MODELS[ai_key]
    provider = model_info["provider"]
    model = model_info["model"]
    
    if provider == "anthropic":
        return ChatAnthropic(
            model=model,
            temperature=temperature,
            api_key=ANTHROPIC_KEY
        )
    elif provider == "openai":
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=OPENAI_KEY
        )
    elif provider == "google":
        return ChatGoogleGenerativeAI(
            model=model,
            temperature=temperature
        )
    elif provider == "groq":
        return ChatGroq(
            model=model,
            temperature=temperature,
            api_key=GROQ_KEY
        )
    elif provider == "xai":
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=XAI_KEY,
            base_url="https://api.x.ai/v1"
        )
    elif provider == "perplexity":
        # Perplexity API（OpenAI互換）
        perplexity_key = st.secrets.get("PERPLEXITY_API_KEY", None)
        if not perplexity_key:
            import os
            perplexity_key = os.getenv("PERPLEXITY_API_KEY")
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=perplexity_key,
            base_url="https://api.perplexity.ai"
        )
    else:
        raise ValueError(f"Unknown provider: {provider}")


# ==========================================
# チーム実行基底クラス
# ==========================================
class TeamExecutor:
    """チーム実行の基底クラス"""
    
    def __init__(self, team_name: str):
        self.team_name = team_name
        self.config = get_team_config(team_name)
        
        # AI インスタンス取得
        self.leader_ai = get_ai_instance(self.config["leader"])
        self.creator_ai = get_ai_instance(self.config["creator"])
        self.checker_ai = get_ai_instance(self.config["checker"])
    
    def get_team_info(self) -> dict:
        """チーム情報を取得"""
        return {
            "name": self.config["name"],
            "leader": AI_MODELS[self.config["leader"]]["name"],
            "creator": AI_MODELS[self.config["creator"]]["name"],
            "checker": AI_MODELS[self.config["checker"]]["name"],
        }
    
    def run_parallel(self, tasks: list[tuple[Any, Callable]]) -> list[dict]:
        """
        並列実行（最速優先）
        tasks: [(ai_instance, callable), ...]
        returns: [{"ai": ai_key, "result": result, "time": elapsed}, ...]
        """
        import time
        results = []
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_ai = {}
            for ai_instance, task_func in tasks:
                future = executor.submit(task_func, ai_instance)
                future_to_ai[future] = ai_instance
            
            for future in as_completed(future_to_ai):
                ai = future_to_ai[future]
                start = time.time()
                try:
                    result = future.result(timeout=60)
                    elapsed = time.time() - start
                    results.append({
                        "ai": str(ai),
                        "result": result,
                        "time": elapsed,
                        "success": True,
                    })
                except Exception as e:
                    results.append({
                        "ai": str(ai),
                        "result": None,
                        "error": str(e),
                        "success": False,
                    })
        
        return results
    
    def resolve(self, leader_result: str, checker_scores: list[dict]) -> dict:
        """
        調停ロジック
        - リーダーの判断を最終結果として採用
        - チェッカーのスコアは独立記録（口出し不可）
        """
        return {
            "final_result": leader_result,
            "scores": checker_scores,
            "team": self.get_team_info(),
        }
