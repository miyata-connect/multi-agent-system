# file_version_manager.py
# ファイルバージョン管理システム
# 行数: 185行

import sqlite3
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
import hashlib

# データベースパス
DB_PATH = Path(__file__).parent / 'data' / 'file_versions.db'

class FileVersionManager:
    """ファイルのバージョン管理を行うクラス"""
    
    def __init__(self, retention_days: int = 3):
        """
        Args:
            retention_days: バージョン保持期間（日数）デフォルト3日
        """
        self.db_path = DB_PATH
        self.retention_days = retention_days
        self._init_database()
    
    def _init_database(self):
        """データベース初期化"""
        DB_PATH.parent.mkdir(exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # ファイルバージョンテーブル
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS file_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL,
                content TEXT NOT NULL,
                content_hash TEXT,
                version INTEGER NOT NULL,
                file_size INTEGER,
                updated_at TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # インデックス作成（検索高速化）
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_file_path 
            ON file_versions(file_path)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_updated_at 
            ON file_versions(updated_at)
        ''')
        
        conn.commit()
        conn.close()
    
    def _calculate_hash(self, content: str) -> str:
        """コンテンツのハッシュ値を計算"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def save_version(self, file_path: str, content: str) -> int:
        """ファイルのバージョンを保存
        
        Args:
            file_path: ファイルパス
            content: ファイル内容
            
        Returns:
            保存されたバージョン番号
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 現在時刻
        now = datetime.now().isoformat()
        
        # 最新バージョン番号を取得
        cursor.execute('''
            SELECT MAX(version) FROM file_versions WHERE file_path = ?
        ''', (file_path,))
        
        result = cursor.fetchone()
        next_version = (result[0] or 0) + 1
        
        # コンテンツハッシュ計算
        content_hash = self._calculate_hash(content)
        
        # 前回と同じ内容ならスキップ
        cursor.execute('''
            SELECT content_hash FROM file_versions 
            WHERE file_path = ? 
            ORDER BY version DESC 
            LIMIT 1
        ''', (file_path,))
        
        last_hash = cursor.fetchone()
        if last_hash and last_hash[0] == content_hash:
            conn.close()
            return next_version - 1  # 既存バージョンを返す
        
        # ファイルサイズ計算
        file_size = len(content.encode('utf-8'))
        
        # バージョン保存
        cursor.execute('''
            INSERT INTO file_versions (file_path, content, content_hash, version, file_size, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (file_path, content, content_hash, next_version, file_size, now))
        
        conn.commit()
        conn.close()
        
        # 古いバージョンを削除
        self.cleanup_old_versions()
        
        return next_version
    
    def get_version(self, file_path: str, version: int) -> Optional[Dict]:
        """特定バージョンのファイルを取得
        
        Args:
            file_path: ファイルパス
            version: バージョン番号
            
        Returns:
            ファイル情報の辞書、存在しない場合はNone
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, file_path, content, version, file_size, updated_at
            FROM file_versions
            WHERE file_path = ? AND version = ?
        ''', (file_path, version))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return {
            'id': row[0],
            'file_path': row[1],
            'content': row[2],
            'version': row[3],
            'file_size': row[4],
            'updated_at': row[5]
        }
    
    def get_file_history(self, file_path: str, limit: int = 20) -> List[Dict]:
        """ファイルの履歴を取得
        
        Args:
            file_path: ファイルパス
            limit: 取得する最大件数
            
        Returns:
            バージョン情報のリスト（新しい順）
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, file_path, version, file_size, updated_at
            FROM file_versions
            WHERE file_path = ?
            ORDER BY version DESC
            LIMIT ?
        ''', (file_path, limit))
        
        history = []
        for row in cursor.fetchall():
            history.append({
                'id': row[0],
                'file_path': row[1],
                'version': row[2],
                'file_size': row[3],
                'updated_at': row[4]
            })
        
        conn.close()
        return history
    
    def get_all_files(self) -> List[str]:
        """管理中の全ファイルパスを取得"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT DISTINCT file_path FROM file_versions
            ORDER BY file_path
        ''')
        
        files = [row[0] for row in cursor.fetchall()]
        conn.close()
        return files
    
    def restore_version(self, file_path: str, version: int) -> Optional[str]:
        """指定バージョンのファイル内容を復元
        
        Args:
            file_path: ファイルパス
            version: バージョン番号
            
        Returns:
            ファイル内容、存在しない場合はNone
        """
        version_data = self.get_version(file_path, version)
        if version_data:
            return version_data['content']
        return None
    
    def cleanup_old_versions(self):
        """保持期間を過ぎた古いバージョンを削除"""
        cutoff_date = (datetime.now() - timedelta(days=self.retention_days)).isoformat()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM file_versions
            WHERE updated_at < ?
        ''', (cutoff_date,))
        
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        return deleted_count
    
    def get_stats(self) -> Dict:
        """統計情報を取得"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 総バージョン数
        cursor.execute('SELECT COUNT(*) FROM file_versions')
        total_versions = cursor.fetchone()[0]
        
        # ユニークファイル数
        cursor.execute('SELECT COUNT(DISTINCT file_path) FROM file_versions')
        unique_files = cursor.fetchone()[0]
        
        # 総サイズ
        cursor.execute('SELECT SUM(file_size) FROM file_versions')
        total_size = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            'total_versions': total_versions,
            'unique_files': unique_files,
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2)
        }

# グローバルインスタンス
file_version_manager = FileVersionManager(retention_days=3)
