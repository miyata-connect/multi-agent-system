# dev_manager/parts_store.py
# 行数: 156行
# 作業パーツ一時保存管理

import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, List
import json
import zipfile
import io


class PartsStore:
    """作業パーツの一時保存・管理クラス"""
    
    def __init__(self, db_path: str = "data/app.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """テーブル作成"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS work_parts (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                content TEXT DEFAULT '',
                version TEXT DEFAULT 'v0.1',
                progress INTEGER DEFAULT 0,
                status TEXT DEFAULT 'in_progress',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_parts_status ON work_parts(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_parts_updated ON work_parts(updated_at DESC)')
        
        conn.commit()
        conn.close()
    
    def create_part(self, name: str, description: str = "") -> dict:
        """新規パーツ作成"""
        part_id = str(uuid.uuid4())[:8]
        now = datetime.now().isoformat()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO work_parts (id, name, description, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (part_id, name, description, now, now))
        
        conn.commit()
        conn.close()
        
        return self.get_part(part_id)
    
    def get_part(self, part_id: str) -> Optional[dict]:
        """パーツ取得"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM work_parts WHERE id = ?', (part_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return self._row_to_dict(row)
        return None
    
    def get_all_parts(self) -> List[dict]:
        """全パーツ取得（更新日時降順）"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM work_parts ORDER BY updated_at DESC')
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_dict(row) for row in rows]
    
    def update_part(self, part_id: str, **kwargs) -> Optional[dict]:
        """パーツ更新"""
        allowed_fields = ['name', 'description', 'content', 'version', 'progress', 'status']
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        if not updates:
            return self.get_part(part_id)
        
        updates['updated_at'] = datetime.now().isoformat()
        
        # 進捗100%なら自動でcompleted
        if updates.get('progress', 0) >= 100:
            updates['status'] = 'completed'
        
        set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [part_id]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(f'UPDATE work_parts SET {set_clause} WHERE id = ?', values)
        conn.commit()
        conn.close()
        
        return self.get_part(part_id)
    
    def delete_part(self, part_id: str) -> bool:
        """パーツ削除"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM work_parts WHERE id = ?', (part_id,))
        deleted = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        return deleted
    
    def export_part_md(self, part_id: str) -> Optional[str]:
        """パーツをMarkdown形式でエクスポート"""
        part = self.get_part(part_id)
        if not part:
            return None
        
        md = f"""# {part['name']} ({part['version']})

## 概要
{part['description']}

## 進捗率
{part['progress']}%

## ステータス
{part['status']}

## 最終更新
{part['updated_at']}

---

## 内容

{part['content']}
"""
        return md
    
    def export_part_zip(self, part_id: str) -> Optional[io.BytesIO]:
        """パーツをZIP形式でエクスポート"""
        part = self.get_part(part_id)
        if not part:
            return None
        
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            # メタデータ
            meta = {
                'id': part['id'],
                'name': part['name'],
                'description': part['description'],
                'version': part['version'],
                'progress': part['progress'],
                'status': part['status'],
                'created_at': part['created_at'],
                'updated_at': part['updated_at'],
            }
            zf.writestr('metadata.json', json.dumps(meta, ensure_ascii=False, indent=2))
            
            # コンテンツ
            zf.writestr('content.md', part['content'] or '')
            
            # README
            zf.writestr('README.md', self.export_part_md(part_id))
        
        buffer.seek(0)
        return buffer
    
    def _row_to_dict(self, row) -> dict:
        """SQLite行を辞書に変換"""
        return {
            'id': row[0],
            'name': row[1],
            'description': row[2],
            'content': row[3],
            'version': row[4],
            'progress': row[5],
            'status': row[6],
            'created_at': row[7],
            'updated_at': row[8],
        }
