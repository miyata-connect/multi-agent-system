# integrations/skills_server.py
# Skills Server API連携モジュール

import requests
from typing import Optional, List, Dict

SKILLS_SERVER_API = "https://api-shdzav64xq-an.a.run.app"


class SkillsServerClient:
    """Skills Server APIクライアント"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.base_url = SKILLS_SERVER_API
    
    def _headers(self) -> Dict:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers
    
    def get_public_skills(self) -> List[Dict]:
        """公開スキル一覧を取得"""
        try:
            resp = requests.get(
                f"{self.base_url}/skills/list",
                headers=self._headers(),
                timeout=10
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("skills", [])
            return []
        except Exception as e:
            print(f"Skills Server error: {e}")
            return []
    
    def get_user_skills(self) -> List[Dict]:
        """ユーザースキル一覧を取得（API Key必須）"""
        if not self.api_key:
            return []
        try:
            resp = requests.get(
                f"{self.base_url}/user-skills/list",
                headers=self._headers(),
                timeout=10
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("skills", [])
            return []
        except Exception as e:
            print(f"Skills Server error: {e}")
            return []
    
    def get_skill_content(self, skill_name: str, is_public: bool = True) -> Optional[str]:
        """スキルの内容を取得"""
        try:
            endpoint = "/skills/get" if is_public else "/user-skills/get"
            resp = requests.get(
                f"{self.base_url}{endpoint}/{skill_name}",
                headers=self._headers(),
                timeout=10
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("content", "")
            return None
        except Exception as e:
            print(f"Skills Server error: {e}")
            return None
    
    def search_skills(self, query: str) -> List[Dict]:
        """スキルを検索"""
        try:
            resp = requests.get(
                f"{self.base_url}/skills/search",
                params={"q": query},
                headers=self._headers(),
                timeout=10
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("skills", [])
            return []
        except Exception as e:
            print(f"Skills Server error: {e}")
            return []
    
    def test_connection(self) -> bool:
        """接続テスト"""
        try:
            resp = requests.get(
                f"{self.base_url}/health",
                timeout=5
            )
            return resp.status_code == 200
        except:
            return False
