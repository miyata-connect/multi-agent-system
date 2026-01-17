# skills_downloader.py
# GitHub Skills検索・ダウンロード機能

import os
import re
import json
import sqlite3
import base64
import requests
from typing import Optional, List
from datetime import datetime
from pathlib import Path
from langchain_core.messages import HumanMessage, SystemMessage


class SkillsDownloader:
    """GitHub上のSkillsを検索・ダウンロードするクラス"""
    
    GITHUB_API_BASE = "https://api.github.com"
    SKILLS_SEARCH_QUERY = "SKILL.md in:path"
    
    def __init__(self, db_path: str = "data/skills_usage.db", skills_dir: str = "data/external_skills"):
        self.db_path = db_path
        self.skills_dir = skills_dir
        self.github_token = os.getenv("GITHUB_TOKEN")
        self._init_db()
        self._init_dirs()
    
    def _init_dirs(self):
        """必要なディレクトリを作成"""
        Path(self.skills_dir).mkdir(parents=True, exist_ok=True)
        Path("data").mkdir(parents=True, exist_ok=True)
    
    def _init_db(self):
        """SQLiteデータベース初期化"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS skills_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                skill_id TEXT NOT NULL,
                skill_name TEXT,
                skill_source TEXT,
                execution_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                task_type TEXT,
                success BOOLEAN,
                response_time_ms INTEGER,
                quality_score INTEGER
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS downloaded_skills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                skill_id TEXT UNIQUE NOT NULL,
                skill_name TEXT,
                github_url TEXT,
                repo_owner TEXT,
                repo_name TEXT,
                file_path TEXT,
                stars INTEGER,
                description TEXT,
                content TEXT,
                downloaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                usage_count INTEGER DEFAULT 0,
                avg_quality_score REAL DEFAULT 0
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS synthesized_skills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                skill_name TEXT NOT NULL,
                parent_skill_ids TEXT,
                content TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                usage_count INTEGER DEFAULT 0,
                quality_score REAL DEFAULT 0
            )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_skill_id ON skills_usage(skill_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_task_type ON skills_usage(task_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_downloaded_skill_id ON downloaded_skills(skill_id)')
        
        conn.commit()
        conn.close()
    
    def _get_headers(self):
        """GitHub API用ヘッダー"""
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Multi-Agent-System-Skills-Downloader"
        }
        if self.github_token:
            headers["Authorization"] = f"token {self.github_token}"
        return headers
    
    def translate_to_search_keywords(self, japanese_query: str) -> str:
        """日本語クエリを英語検索キーワードに変換（Gemini使用）"""
        try:
            from config import get_commander
            
            model = get_commander()
            messages = [
                SystemMessage(content="""あなたは検索キーワード変換の専門家です。
ユーザーの日本語入力をGitHub検索に最適な英語キーワードに変換してください。

ルール:
- 3-5個の英語キーワードをスペース区切りで返す
- 技術用語は正確に（例: 認証→authentication, エラー処理→error handling）
- 余計な説明は不要、キーワードのみ返す

例:
入力: 「Firebase認証のベストプラクティス」
出力: firebase authentication best practices

入力: 「Pythonでリトライ処理」
出力: python retry error handling"""),
                HumanMessage(content=japanese_query)
            ]
            
            response = model.invoke(messages)
            keywords = response.content.strip().lower()
            print(f"🔄 キーワード変換: '{japanese_query}' → '{keywords}'")
            return keywords
            
        except Exception as e:
            print(f"⚠️ キーワード変換エラー: {e}")
            return japanese_query
    
    def _is_japanese(self, text: str) -> bool:
        """日本語が含まれているか判定"""
        return bool(re.search(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]', text))
    
    def search_skills(self, query: str = "", max_results: int = 100) -> List[dict]:
        """GitHubでSKILL.mdファイルを検索"""
        search_query = f"{self.SKILLS_SEARCH_QUERY} {query}".strip()
        
        results = []
        page = 1
        per_page = min(100, max_results)
        
        while len(results) < max_results:
            url = f"{self.GITHUB_API_BASE}/search/code"
            params = {"q": search_query, "per_page": per_page, "page": page}
            
            try:
                response = requests.get(url, headers=self._get_headers(), params=params, timeout=30)
                
                if response.status_code == 403:
                    print("⚠️ GitHub APIレート制限。GITHUB_TOKENを設定してください。")
                    break
                
                response.raise_for_status()
                data = response.json()
                
                items = data.get("items", [])
                if not items:
                    break
                
                for item in items:
                    repo = item.get("repository", {})
                    skill_info = {
                        "skill_id": f"{repo.get('full_name', '')}:{item.get('path', '')}",
                        "skill_name": item.get("name", ""),
                        "github_url": item.get("html_url", ""),
                        "repo_owner": repo.get("owner", {}).get("login", ""),
                        "repo_name": repo.get("name", ""),
                        "file_path": item.get("path", ""),
                        "stars": repo.get("stargazers_count", 0),
                        "description": repo.get("description", ""),
                        "raw_url": item.get("url", "")
                    }
                    results.append(skill_info)
                    
                    if len(results) >= max_results:
                        break
                
                page += 1
                total_count = data.get("total_count", 0)
                if page * per_page >= total_count:
                    break
                    
            except requests.RequestException as e:
                print(f"❌ GitHub API エラー: {e}")
                break
        
        print(f"✅ {len(results)}件のSkillsを検索しました")
        return results
    
    def smart_search(self, query: str, max_results: int = 100) -> List[dict]:
        """日本語対応のスマート検索（自動で英語変換）"""
        if self._is_japanese(query):
            query = self.translate_to_search_keywords(query)
        return self.search_skills(query, max_results)
    
    def download_skill(self, skill_info: dict) -> Optional[dict]:
        """単一のSkillをダウンロードしてDBに保存"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM downloaded_skills WHERE skill_id = ?", (skill_info["skill_id"],))
            if cursor.fetchone():
                conn.close()
                return None
            conn.close()
            
            raw_url = skill_info.get("raw_url", "")
            if not raw_url:
                return None
            
            response = requests.get(raw_url, headers=self._get_headers(), timeout=30)
            response.raise_for_status()
            content_data = response.json()
            
            content = ""
            if content_data.get("encoding") == "base64":
                content = base64.b64decode(content_data.get("content", "")).decode("utf-8", errors="ignore")
            else:
                content = content_data.get("content", "")
            
            safe_name = skill_info["skill_id"].replace("/", "_").replace(":", "_")
            skill_path = Path(self.skills_dir) / safe_name
            skill_path.mkdir(parents=True, exist_ok=True)
            
            with open(skill_path / "SKILL.md", "w", encoding="utf-8") as f:
                f.write(content)
            
            metadata = {**skill_info, "downloaded_at": datetime.now().isoformat(), "local_path": str(skill_path)}
            with open(skill_path / "metadata.json", "w", encoding="utf-8") as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO downloaded_skills 
                (skill_id, skill_name, github_url, repo_owner, repo_name, file_path, stars, description, content)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                skill_info["skill_id"], skill_info["skill_name"], skill_info["github_url"],
                skill_info["repo_owner"], skill_info["repo_name"], skill_info["file_path"],
                skill_info.get("stars", 0), skill_info.get("description", ""), content
            ))
            conn.commit()
            conn.close()
            
            return {**skill_info, "content": content, "local_path": str(skill_path)}
            
        except Exception as e:
            print(f"❌ ダウンロードエラー [{skill_info.get('skill_id', 'unknown')}]: {e}")
            return None
    
    def batch_download(self, query: str = "", max_skills: int = 50) -> List[dict]:
        """複数Skillsを一括ダウンロード"""
        print(f"🔍 Skills検索中: '{query}'")
        skills = self.search_skills(query, max_results=max_skills * 2)
        
        downloaded = []
        for i, skill in enumerate(skills[:max_skills]):
            result = self.download_skill(skill)
            if result:
                downloaded.append(result)
                print(f"  ✅ [{i+1}/{max_skills}] {skill['repo_name']}/{skill['file_path']}")
        
        print(f"\n📦 {len(downloaded)}件のSkillsをダウンロードしました")
        return downloaded
    
    def smart_batch_download(self, query: str, max_skills: int = 50) -> List[dict]:
        """日本語対応の一括ダウンロード"""
        if self._is_japanese(query):
            query = self.translate_to_search_keywords(query)
        return self.batch_download(query, max_skills)
    
    def record_usage(self, skill_id: str, task_type: str, success: bool, 
                     response_time_ms: int = 0, quality_score: int = 0):
        """Skill使用履歴を記録"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO skills_usage (skill_id, task_type, success, response_time_ms, quality_score)
            VALUES (?, ?, ?, ?, ?)
        ''', (skill_id, task_type, success, response_time_ms, quality_score))
        
        cursor.execute('''
            UPDATE downloaded_skills 
            SET usage_count = usage_count + 1,
                avg_quality_score = (avg_quality_score * usage_count + ?) / (usage_count + 1)
            WHERE skill_id = ?
        ''', (quality_score, skill_id))
        
        conn.commit()
        conn.close()
    
    def get_top_skills(self, limit: int = 10, min_usage: int = 1) -> List[dict]:
        """使用頻度の高いSkillsを取得"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT skill_id, skill_name, github_url, stars, usage_count, avg_quality_score
            FROM downloaded_skills
            WHERE usage_count >= ?
            ORDER BY usage_count DESC, avg_quality_score DESC
            LIMIT ?
        ''', (min_usage, limit))
        
        results = [{"skill_id": r[0], "skill_name": r[1], "github_url": r[2], 
                    "stars": r[3], "usage_count": r[4], "avg_quality_score": r[5]} 
                   for r in cursor.fetchall()]
        conn.close()
        return results
    
    def find_similar_skills(self, keywords: List[str], limit: int = 5) -> List[dict]:
        """キーワードに基づいて類似Skillsを検索（ローカルDB内）"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        conditions = " OR ".join(["content LIKE ? OR description LIKE ?" for _ in keywords])
        params = []
        for kw in keywords:
            params.extend([f"%{kw}%", f"%{kw}%"])
        
        cursor.execute(f'''
            SELECT skill_id, skill_name, description, content, stars, usage_count
            FROM downloaded_skills WHERE {conditions}
            ORDER BY stars DESC, usage_count DESC LIMIT ?
        ''', (*params, limit))
        
        results = [{"skill_id": r[0], "skill_name": r[1], "description": r[2],
                    "content_preview": r[3][:500] if r[3] else "", "stars": r[4], "usage_count": r[5]}
                   for r in cursor.fetchall()]
        conn.close()
        return results
    
    def get_stats(self) -> dict:
        """統計情報を取得"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM downloaded_skills")
        total_skills = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM skills_usage")
        total_usages = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM skills_usage WHERE success = 1")
        successful_usages = cursor.fetchone()[0]
        
        cursor.execute("SELECT AVG(quality_score) FROM skills_usage WHERE quality_score > 0")
        avg_quality = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            "total_downloaded_skills": total_skills,
            "total_usages": total_usages,
            "successful_usages": successful_usages,
            "success_rate": round(successful_usages / total_usages * 100, 2) if total_usages > 0 else 0,
            "avg_quality_score": round(avg_quality, 2)
        }
