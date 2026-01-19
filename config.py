# config.py
# 行数: 62行
# APIキー設定とモデル初期化

import os
import streamlit as st
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_groq import ChatGroq

load_dotenv()

# ==========================================
# APIキー設定
# ==========================================
GEMINI_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY")
GROQ_KEY = os.getenv("GROQ_API_KEY")
XAI_KEY = os.getenv("XAI_API_KEY")

if GEMINI_KEY:
    os.environ["GOOGLE_API_KEY"] = GEMINI_KEY

# ==========================================
# モデル初期化
# ==========================================
@st.cache_resource
def get_commander():
    return ChatGoogleGenerativeAI(model="gemini-3-pro-preview", temperature=0.5)

@st.cache_resource
def get_auditor():
    return ChatOpenAI(model="gpt-5.2", temperature=0, api_key=OPENAI_KEY)

@st.cache_resource
def get_coder():
    return ChatAnthropic(model="claude-sonnet-4-5-20250929", temperature=0, api_key=ANTHROPIC_KEY)

@st.cache_resource
def get_data_processor():
    return ChatGroq(model="llama-3.3-70b-versatile", temperature=0, api_key=GROQ_KEY)

@st.cache_resource
def get_searcher():
    return ChatOpenAI(
        model="grok-4-1-thinking",
        temperature=0,
        api_key=XAI_KEY,
        base_url="https://api.x.ai/v1"
    )

# ==========================================
# APIキーチェック
# ==========================================
def check_api_keys():
    missing_keys = []
    if not GEMINI_KEY: missing_keys.append("GEMINI_API_KEY")
    if not OPENAI_KEY: missing_keys.append("OPENAI_API_KEY")
    if not ANTHROPIC_KEY: missing_keys.append("ANTHROPIC_API_KEY")
    if not GROQ_KEY: missing_keys.append("GROQ_API_KEY")
    if not XAI_KEY: missing_keys.append("XAI_API_KEY")
    return missing_keys

# ==========================================
# AIモデル定義（スイッチ用）
# ==========================================
AI_MODELS = {
    "claude": {
        "name": "Claude Sonnet 4.5",
        "provider": "anthropic",
        "model": "claude-sonnet-4-5-20250929",
        "strengths": ["コーディング", "安定性", "デザイン"],
    },
    "gpt": {
        "name": "GPT-5.2",
        "provider": "openai",
        "model": "gpt-5.2",
        "strengths": ["オールマイティ", "監査", "設計"],
    },
    "gemini": {
        "name": "Gemini 3 Pro",
        "provider": "google",
        "model": "gemini-3-pro-preview",
        "strengths": ["問題解決", "聞き取り"],
    },
    "grok": {
        "name": "Grok 4.1 Thinking",
        "provider": "xai",
        "model": "grok-4-1-thinking",
        "strengths": ["検索", "X内検索", "聞き役"],
    },
    "llama": {
        "name": "Llama 3.3 70B",
        "provider": "groq",
        "model": "llama-3.3-70b-versatile",
        "strengths": ["データ保存", "データ検索"],
    },
    "perplexity": {
        "name": "Perplexity",
        "provider": "perplexity",
        "model": "sonar-pro",
        "strengths": ["最新検索", "ディープサーチ"],
    },
}

# ==========================================
# チーム構成（デフォルト）
# ==========================================
DEFAULT_TEAM_CONFIG = {
    "concierge": {
        "name": "コンシェルジュ",
        "leader": "grok",
        "creator": "gemini",
        "checker": "perplexity",
    },
    "auditor": {
        "name": "監査・レビュー",
        "leader": "gpt",
        "creator": "claude",
        "checker": "gemini",
    },
    "coder": {
        "name": "コーディング",
        "leader": "claude",
        "creator": "claude",
        "checker": "gpt",
    },
    "data": {
        "name": "データ確認・保存",
        "leader": "llama",
        "creator": "llama",
        "checker": "grok",
    },
    "searcher": {
        "name": "検索",
        "leader": "grok",
        "creator": "perplexity",
        "checker": "llama",
    },
}

# ==========================================
# チーム構成取得（セッション対応）
# ==========================================
def get_team_config(team_name: str) -> dict:
    """セッションのカスタム設定があればそれを、なければデフォルトを返す"""
    if "team_config" in st.session_state:
        return st.session_state.team_config.get(team_name, DEFAULT_TEAM_CONFIG[team_name])
    return DEFAULT_TEAM_CONFIG[team_name]

def set_team_config(team_name: str, leader: str, creator: str, checker: str):
    """セッションにカスタムチーム設定を保存"""
    if "team_config" not in st.session_state:
        st.session_state.team_config = {}
    st.session_state.team_config[team_name] = {
        "name": DEFAULT_TEAM_CONFIG[team_name]["name"],
        "leader": leader,
        "creator": creator,
        "checker": checker,
    }

def reset_team_config():
    """チーム設定をデフォルトに戻す"""
    if "team_config" in st.session_state:
        del st.session_state.team_config
