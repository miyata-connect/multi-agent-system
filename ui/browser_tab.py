# ui/browser_tab.py
# ブラウザタブの実装
# 行数: 180行

import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

def render_browser_tab():
    """ブラウザタブをレンダリング"""
    st.markdown('<div style="font-size: 1.5rem; font-weight: bold; margin-bottom: 1rem;">🌐 ブラウザ</div>', unsafe_allow_html=True)
    
    # セッション状態初期化
    _init_browser_session()
    
    # URL入力バー
    _render_url_bar()
    
    # ページ取得
    if st.session_state.browser_html is None:
        _fetch_and_render_page()
    
    # ページ情報表示
    if st.session_state.browser_content:
        st.markdown(f"**📄 {st.session_state.browser_content['title']}**")
    
    # HTMLレンダリング
    if st.session_state.browser_html:
        st.components.v1.html(st.session_state.browser_html, height=550, scrolling=True)
    
    # AI分析結果
    _render_analysis_results()
    
    # ブックマーク
    _render_bookmarks()

def _init_browser_session():
    """ブラウザセッション初期化"""
    if "browser_url" not in st.session_state:
        st.session_state.browser_url = "https://www.google.com/"
    if "browser_content" not in st.session_state:
        st.session_state.browser_content = None
    if "browser_analysis" not in st.session_state:
        st.session_state.browser_analysis = None
    if "browser_html" not in st.session_state:
        st.session_state.browser_html = None

def _render_url_bar():
    """URL入力バー"""
    url_col1, url_col2, url_col3 = st.columns([5, 1, 1])
    
    with url_col1:
        url = st.text_input("URL", value=st.session_state.browser_url, key="browser_url_input", 
                          label_visibility="collapsed", placeholder="https://example.com")
    with url_col2:
        go_clicked = st.button("🔄 移動", key="browser_go", use_container_width=True)
    with url_col3:
        analyze_clicked = st.button("🤖 AI分析", key="browser_analyze", use_container_width=True)
    
    if go_clicked and url:
        st.session_state.browser_url = url
        st.session_state.browser_content = None
        st.session_state.browser_analysis = None
        st.session_state.browser_html = None

def _fetch_page(target_url):
    """ページ取得"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "ja,en-US;q=0.7,en;q=0.3",
        }
        response = requests.get(target_url, headers=headers, timeout=15)
        response.encoding = response.apparent_encoding or 'utf-8'
        return response.text, None
    except Exception as e:
        return None, str(e)

def _fetch_and_render_page():
    """ページ取得とレンダリング"""
    with st.spinner(f"🌐 {st.session_state.browser_url} を読み込み中..."):
        html, error = _fetch_page(st.session_state.browser_url)
        
        if html:
            soup = BeautifulSoup(html, "html.parser")
            title = soup.title.string if soup.title else "タイトルなし"
            
            # ベースURL設定
            base_url = f"{urlparse(st.session_state.browser_url).scheme}://{urlparse(st.session_state.browser_url).netloc}"
            
            # baseタグ追加
            for base in soup.find_all('base'):
                base.decompose()
            if soup.head:
                new_base = soup.new_tag('base', href=base_url)
                soup.head.insert(0, new_base)
            
            # 相対URL変換
            for tag in soup.find_all(['img', 'link', 'script']):
                for attr in ['src', 'href']:
                    if tag.get(attr) and not tag[attr].startswith(('http://', 'https://', 'data:', '//', '#')):
                        tag[attr] = urljoin(st.session_state.browser_url, tag[attr])
            
            # テキスト抽出
            text_soup = BeautifulSoup(html, "html.parser")
            for tag in text_soup(["script", "style", "noscript"]):
                tag.decompose()
            text = text_soup.get_text(separator="\n", strip=True)
            
            st.session_state.browser_html = str(soup)
            st.session_state.browser_content = {
                "title": title,
                "text": text[:15000],
                "url": st.session_state.browser_url
            }
        else:
            st.error(f"❌ ページ取得失敗: {error}")
            st.session_state.browser_html = f"<html><body><h1>エラー</h1><p>{error}</p></body></html>"
            st.session_state.browser_content = None

def _render_analysis_results():
    """AI分析結果表示"""
    if st.session_state.browser_analysis:
        st.divider()
        st.subheader("🤖 AI分析結果")
        
        from config import AI_MODELS
        cols = st.columns(len(st.session_state.browser_analysis))
        for i, result in enumerate(st.session_state.browser_analysis):
            with cols[i]:
                ai_name = AI_MODELS.get(result['ai'], {}).get('name', result['ai'])
                if result['success']:
                    st.markdown(f"**{ai_name}**")
                    st.markdown(result['result'][:500])
                else:
                    st.error(f"{ai_name}: 失敗")

def _render_bookmarks():
    """ブックマーク表示"""
    st.divider()
    st.subheader("⭐ ブックマーク")
    
    if "bookmarks" not in st.session_state:
        st.session_state.bookmarks = [
            {"name": "Google", "url": "https://www.google.com/"},
            {"name": "Wikipedia", "url": "https://ja.wikipedia.org/"},
            {"name": "GitHub", "url": "https://github.com/"},
            {"name": "Qiita", "url": "https://qiita.com/"},
        ]
    
    bm_cols = st.columns(4)
    for i, bm in enumerate(st.session_state.bookmarks):
        with bm_cols[i % 4]:
            if st.button(f"🔗 {bm['name']}", key=f"bm_{i}", use_container_width=True):
                st.session_state.browser_url = bm['url']
                st.session_state.browser_content = None
                st.session_state.browser_analysis = None
                st.session_state.browser_html = None
                st.rerun()
    
    # ブックマーク追加
    with st.expander("➕ ブックマーク管理"):
        bm_col1, bm_col2, bm_col3 = st.columns([2, 3, 1])
        with bm_col1:
            bm_name = st.text_input("名前", key="bm_name_input", label_visibility="collapsed", placeholder="名前")
        with bm_col2:
            bm_url = st.text_input("URL", key="bm_url_input", label_visibility="collapsed", placeholder="URL")
        with bm_col3:
            if st.button("追加", key="bm_add"):
                if bm_name and bm_url:
                    st.session_state.bookmarks.append({"name": bm_name, "url": bm_url})
                    st.rerun()
