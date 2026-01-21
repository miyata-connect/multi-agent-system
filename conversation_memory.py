"""
会話記憶管理システム
- 直近10件のスレッド記憶
- アンカー検索機能
- SQLite永続化
"""

import os
import sqlite3
import json
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

# データベースパス
DB_PATH = Path(__file__).parent / 'data' / 'conversation_memory.db'

class ConversationMemory:
    def __init__(self):
        self.db_path = DB_PATH
        self._init_database()
    
    def _init_database(self):
        """データベース初期化"""
        DB_PATH.parent.mkdir(exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # スレッド記憶テーブル
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS threads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                thread_id TEXT UNIQUE,
                title TEXT,
                content TEXT,
                updated_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # アンカーテーブル
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS anchors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                anchor_id TEXT UNIQUE,
                keywords TEXT,
                content TEXT,
                thread_id TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (thread_id) REFERENCES threads(thread_id)
            )
        ''')
        
        # 会話履歴テーブル（現在セッション用）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS session_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT,
                content TEXT,
                ai_type TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_thread(self, thread_id: str, title: str, content: str, updated_at: str):
        """スレッド保存"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO threads (thread_id, title, content, updated_at)
            VALUES (?, ?, ?, ?)
        ''', (thread_id, title, content, updated_at))
        
        conn.commit()
        conn.close()
    
    def extract_and_save_anchors(self, thread_id: str, content: str):
        """アンカー抽出・保存"""
        # <anchor id="xxx" keywords="yyy">...</anchor> パターン
        pattern = r'<anchor\s+id="([^"]+)"\s+keywords="([^"]+)">(.*?)</anchor>'
        matches = re.findall(pattern, content, re.DOTALL)
        
        if not matches:
            return 0
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        saved_count = 0
        for anchor_id, keywords, anchor_content in matches:
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO anchors (anchor_id, keywords, content, thread_id)
                    VALUES (?, ?, ?, ?)
                ''', (anchor_id, keywords, anchor_content.strip(), thread_id))
                saved_count += 1
            except Exception as e:
                print(f"アンカー保存エラー: {e}")
        
        conn.commit()
        conn.close()
        
        return saved_count
    
    def search_anchors(self, query: str, limit: int = 5) -> List[Dict]:
        """アンカー検索
        
        Args:
            query: 検索キーワード（空文字列で全件取得）
            limit: 最大取得件数
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if query:
            # キーワード部分一致検索
            cursor.execute('''
                SELECT anchor_id, keywords, content, thread_id
                FROM anchors
                WHERE keywords LIKE ? OR content LIKE ?
                ORDER BY id DESC
                LIMIT ?
            ''', (f'%{query}%', f'%{query}%', limit))
        else:
            # 全件取得
            cursor.execute('''
                SELECT anchor_id, keywords, content, thread_id
                FROM anchors
                ORDER BY id DESC
                LIMIT ?
            ''', (limit,))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'anchor_id': row[0],
                'keywords': row[1],
                'content': row[2],
                'thread_id': row[3]
            })
        
        conn.close()
        return results
    
    def get_recent_threads(self, limit: int = 10) -> List[Dict]:
        """直近N件のスレッド取得"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT thread_id, title, content, updated_at
            FROM threads
            ORDER BY updated_at DESC
            LIMIT ?
        ''', (limit,))
        
        threads = []
        for row in cursor.fetchall():
            threads.append({
                'thread_id': row[0],
                'title': row[1],
                'content': row[2],
                'updated_at': row[3]
            })
        
        conn.close()
        return threads
    
    def add_session_message(self, role: str, content: str, ai_type: str = None):
        """現在セッションのメッセージ追加"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO session_history (role, content, ai_type)
            VALUES (?, ?, ?)
        ''', (role, content, ai_type))
        
        conn.commit()
        conn.close()
    
    def get_session_history(self, limit: int = None) -> List[Dict]:
        """現在セッションの履歴取得"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if limit:
            cursor.execute('''
                SELECT role, content, ai_type, timestamp
                FROM session_history
                ORDER BY id DESC
                LIMIT ?
            ''', (limit,))
        else:
            cursor.execute('''
                SELECT role, content, ai_type, timestamp
                FROM session_history
                ORDER BY id ASC
            ''')
        
        history = []
        for row in cursor.fetchall():
            history.append({
                'role': row[0],
                'content': row[1],
                'ai_type': row[2],
                'timestamp': row[3]
            })
        
        conn.close()
        return history
    
    def clear_session(self):
        """セッション履歴クリア"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM session_history')
        conn.commit()
        conn.close()
    
    def get_history_until(self, target_timestamp: str) -> List[Dict]:
        """指定タイムスタンプまでの履歴を取得（復元用）
        
        Args:
            target_timestamp: 復元したい最後のメッセージのタイムスタンプ
            
        Returns:
            該当タイムスタンプまでの全メッセージリスト
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT role, content, ai_type, timestamp
            FROM session_history
            WHERE timestamp <= ?
            ORDER BY id ASC
        ''', (target_timestamp,))
        
        history = []
        for row in cursor.fetchall():
            history.append({
                'role': row[0],
                'content': row[1],
                'ai_type': row[2],
                'timestamp': row[3]
            })
        
        conn.close()
        return history
    
    def build_memory_context(self, user_query: str) -> str:
        """記憶コンテキスト生成"""
        context_parts = []
        
        # 1. 直近10件のスレッド（必須）
        recent_threads = self.get_recent_threads(10)
        if recent_threads:
            context_parts.append("=== 直近10件のスレッド記憶 ===")
            for thread in recent_threads:
                context_parts.append(f"[{thread['title']}]")
                context_parts.append(thread['content'][:500] + "..." if len(thread['content']) > 500 else thread['content'])
                context_parts.append("")
        
        # 2. アンカー検索
        anchors = self.search_anchors(user_query)
        if anchors:
            context_parts.append("=== 関連アンカー ===")
            for anchor in anchors:
                context_parts.append(f"[{anchor['anchor_id']}] Keywords: {anchor['keywords']}")
                context_parts.append(anchor['content'])
                context_parts.append("")
        
        # 3. セッション履歴
        session_history = self.get_session_history(limit=20)
        if session_history:
            context_parts.append("=== 現在セッションの履歴 ===")
            for msg in session_history[-10:]:  # 直近10件
                context_parts.append(f"{msg['role']}: {msg['content'][:200]}...")
        
        return "\n".join(context_parts)

# グローバルインスタンス
memory = ConversationMemory()
