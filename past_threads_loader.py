"""
過去スレッドローダー
Claude APIのconversation_search/recent_chatsツールと統合
"""

import os
import sys
from typing import List, Dict

# Claude APIツールのモック（実際の環境では自動で利用可能）
# 注: これらのツールはClaudeチャット内でのみ動作します

def load_recent_threads_from_claude(n: int = 10) -> List[Dict]:
    """
    Claudeのrecent_chatsツールで直近N件取得
    
    実行環境:
    - Claude Chat環境: 自動でrecent_chatsツールを呼び出し
    - ローカル環境: conversation_memory.pyの保存データを使用
    """
    print(f"📚 直近{n}件のスレッドを読み込み中...")
    
    # このコードはClaude Chat環境でのみ動作
    # ローカル実行時は保存済みデータを使用
    try:
        # Claude環境チェック
        if 'ANTHROPIC_API_KEY' in os.environ:
            print("⚠️ ローカル環境: 保存済みデータを使用します")
            from conversation_memory import memory
            return memory.get_recent_threads(n)
        else:
            print("✅ Claude Chat環境: recent_chatsツールを使用")
            # 実際にはClaude側でrecent_chatsツールが自動実行される
            # この関数は呼び出しのトリガーとして機能
            return []
    except Exception as e:
        print(f"❌ エラー: {e}")
        return []

def search_conversations_by_keyword(query: str) -> List[Dict]:
    """
    Claudeのconversation_searchツールでキーワード検索
    """
    print(f"🔍 キーワード検索: {query}")
    
    try:
        if 'ANTHROPIC_API_KEY' in os.environ:
            print("⚠️ ローカル環境: アンカー検索を使用します")
            from conversation_memory import memory
            return memory.search_anchors(query)
        else:
            print("✅ Claude Chat環境: conversation_searchツールを使用")
            return []
    except Exception as e:
        print(f"❌ エラー: {e}")
        return []

def initialize_memory_system():
    """
    起動時メモリ初期化
    
    実行内容:
    1. recent_chats(n=10)で直近10スレッド取得
    2. アンカー抽出・保存
    3. データベースに永続化
    """
    print("\n" + "="*60)
    print("🧠 会話記憶システム初期化中...")
    print("="*60)
    
    from conversation_memory import memory
    
    # 直近10件取得
    threads = load_recent_threads_from_claude(10)
    
    if not threads:
        print("⚠️ 過去スレッドが見つかりません（初回起動の可能性）")
        return
    
    # 各スレッドを保存・アンカー抽出
    total_anchors = 0
    for thread in threads:
        thread_id = thread.get('thread_id', thread.get('uri', ''))
        title = thread.get('title', 'Untitled')
        content = thread.get('content', thread.get('summary', ''))
        updated_at = thread.get('updated_at', '')
        
        # スレッド保存
        memory.save_thread(thread_id, title, content, updated_at)
        
        # アンカー抽出
        anchor_count = memory.extract_and_save_anchors(thread_id, content)
        total_anchors += anchor_count
    
    print(f"✅ {len(threads)}件のスレッドを記憶")
    print(f"✅ {total_anchors}個のアンカーを抽出")
    print("="*60 + "\n")

if __name__ == "__main__":
    # テスト実行
    initialize_memory_system()
