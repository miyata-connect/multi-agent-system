# ui/browser_tab.py
# ブラウザタブ（システムブラウザ起動 + ブックマーク管理）
# 行数: 180行

import streamlit as st
import webbrowser
import requests
from bs4 import BeautifulSoup
from datetime import datetime

def render_browser_tab():
    """ブラウザタブをレンダリング（システムブラウザ起動方式）"""
    st.markdown('<div style="font-size: 1.5rem; font-weight: bold; margin-bottom: 1rem;">🌐 ブラウザ</div>', unsafe_allow_html=True)
    
    st.info("💡 URLを入力してシステムブラウザ（Chrome/Safari等）で開きます")
    
    # セッション状態初期化
    _init_browser_session()
    
    # URL入力欄
    _render_url_input()
    
    st.divider()
    
    # ブックマーク
    _render_bookmarks()
    
    st.divider()
    
    # AI分析機能
    _render_ai_analysis()

def _init_browser_session():
    """セッション初期化"""
    if "browser_url" not in st.session_state:
        st.session_state.browser_url = "https://www.google.com/"
    if "bookmarks" not in st.session_state:
        st.session_state.bookmarks = [
            {"name": "Google", "url": "https://www.google.com/", "added": datetime.now().isoformat()},
            {"name": "Wikipedia", "url": "https://ja.wikipedia.org/", "added": datetime.now().isoformat()},
            {"name": "GitHub", "url": "https://github.com/", "added": datetime.now().isoformat()},
            {"name": "Qiita", "url": "https://qiita.com/", "added": datetime.now().isoformat()},
        ]
    if "browser_analysis" not in st.session_state:
        st.session_state.browser_analysis = None

def _render_url_input():
    """URL入力エリア"""
    url_col1, url_col2 = st.columns([5, 1])
    
    with url_col1:
        url = st.text_input(
            "URL",
            value=st.session_state.browser_url,
            key="browser_url_input",
            label_visibility="collapsed",
            placeholder="https://example.com"
        )
        st.session_state.browser_url = url
    
    with url_col2:
        if st.button("🚀 開く", key="browser_open", use_container_width=True, type="primary"):
            if url:
                try:
                    webbrowser.open(url)
                    st.success(f"✅ ブラウザで開きました: {url}")
                except Exception as e:
                    st.error(f"❌ 開けませんでした: {e}")

def _render_bookmarks():
    """ブックマーク管理"""
    st.subheader("⭐ ブックマーク")
    
    # ブックマーク一覧
    if st.session_state.bookmarks:
        # 4列表示
        cols_per_row = 4
        bookmarks = st.session_state.bookmarks
        
        for i in range(0, len(bookmarks), cols_per_row):
            cols = st.columns(cols_per_row)
            for j, col in enumerate(cols):
                if i + j < len(bookmarks):
                    bm = bookmarks[i + j]
                    with col:
                        # ブックマークカード
                        with st.container():
                            st.markdown(f"**🔗 {bm['name']}**")
                            
                            btn_col1, btn_col2 = st.columns([3, 1])
                            with btn_col1:
                                if st.button("開く", key=f"open_bm_{i+j}", use_container_width=True):
                                    webbrowser.open(bm['url'])
                                    st.success(f"✅ {bm['name']}を開きました")
                            with btn_col2:
                                if st.button("🗑", key=f"del_bm_{i+j}", help="削除"):
                                    st.session_state.bookmarks.remove(bm)
                                    st.rerun()
                            
                            st.caption(f"{bm['url'][:30]}...")
    else:
        st.caption("ブックマークがありません")
    
    # ブックマーク追加
    with st.expander("➕ ブックマーク追加", expanded=False):
        add_col1, add_col2, add_col3 = st.columns([2, 3, 1])
        
        with add_col1:
            new_name = st.text_input(
                "名前",
                key="new_bookmark_name",
                label_visibility="collapsed",
                placeholder="サイト名"
            )
        
        with add_col2:
            new_url = st.text_input(
                "URL",
                key="new_bookmark_url",
                label_visibility="collapsed",
                placeholder="https://example.com"
            )
        
        with add_col3:
            if st.button("追加", key="add_bookmark", use_container_width=True):
                if new_name and new_url:
                    st.session_state.bookmarks.append({
                        "name": new_name,
                        "url": new_url,
                        "added": datetime.now().isoformat()
                    })
                    st.success(f"✅ {new_name}を追加しました")
                    st.rerun()
                else:
                    st.warning("名前とURLを入力してください")

def _render_ai_analysis():
    """AI分析機能"""
    st.subheader("🤖 AI分析")
    
    st.markdown("URLのページ内容を5つのAIが分析します")
    
    analysis_col1, analysis_col2 = st.columns([5, 1])
    
    with analysis_col1:
        analysis_url = st.text_input(
            "分析URL",
            value=st.session_state.browser_url,
            key="analysis_url_input",
            label_visibility="collapsed",
            placeholder="https://example.com"
        )
    
    with analysis_col2:
        if st.button("🤖 分析", key="start_analysis", use_container_width=True):
            if analysis_url:
                _analyze_page(analysis_url)
    
    # 分析結果表示
    if st.session_state.browser_analysis:
        st.divider()
        st.markdown("**📊 分析結果**")
        
        from config import AI_MODELS
        
        # 5列表示
        cols = st.columns(5)
        for i, result in enumerate(st.session_state.browser_analysis):
            with cols[i]:
                ai_name = AI_MODELS.get(result['ai'], {}).get('name', result['ai'])
                
                if result['success']:
                    st.markdown(f"**{ai_name}**")
                    st.markdown(result['result'][:300] + "...")
                else:
                    st.error(f"**{ai_name}**")
                    st.caption("分析失敗")

def _analyze_page(url: str):
    """ページをAI分析"""
    with st.spinner("🤖 5つのAIが分析中..."):
        try:
            # ページ取得
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            }
            response = requests.get(url, headers=headers, timeout=15)
            response.encoding = response.apparent_encoding or 'utf-8'
            
            # テキスト抽出
            soup = BeautifulSoup(response.text, "html.parser")
            title = soup.title.string if soup.title else "タイトルなし"
            
            for tag in soup(["script", "style", "noscript"]):
                tag.decompose()
            text = soup.get_text(separator="\n", strip=True)
            
            # AI分析
            from agents.base import get_ai_instance
            from langchain_core.messages import HumanMessage, SystemMessage
            from concurrent.futures import ThreadPoolExecutor, as_completed
            
            prompt = f"""以下のWebページを分析してください。

URL: {url}
タイトル: {title}

内容:
{text[:5000]}

以下の形式で簡潔に回答:
1. 要約（50文字以内）
2. キーワード（3つ）
3. 評価（100点満点）"""
            
            ai_keys = ["gemini", "gpt", "claude", "grok", "llama"]
            results = []
            
            def analyze_with_ai(ai_key):
                try:
                    ai = get_ai_instance(ai_key, temperature=0)
                    messages = [
                        SystemMessage(content="あなたはWebページ分析の専門家です。簡潔に分析してください。"),
                        HumanMessage(content=prompt)
                    ]
                    response = ai.invoke(messages)
                    return {"ai": ai_key, "result": response.content, "success": True}
                except Exception as e:
                    return {"ai": ai_key, "result": str(e), "success": False}
            
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = {executor.submit(analyze_with_ai, key): key for key in ai_keys}
                for future in as_completed(futures):
                    results.append(future.result())
            
            st.session_state.browser_analysis = results
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ 分析失敗: {e}")
