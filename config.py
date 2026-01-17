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
