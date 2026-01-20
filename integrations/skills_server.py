# integrations/skills_server.py
# Skills Server API連携モジュール（読み取り専用）

import requests
from typing import Optional, List, Dict
import streamlit as st

SKILLS_SERVER_API = "https://api-shdzav64xq-an.a.run.app"


class SkillsServerClient:
    """Skills Server APIクライアント（読み取り専用）"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or self._get_api_key_from_secrets()
        self.base_url = SKILLS_SERVER_API
    
    def _get_api_key_from_secrets(self) -> Optional[str]:
        """Streamlit SecretsからAPI Keyを取得"""
        try:
            if hasattr(st, 'secrets') and 'SKILLS_API_KEY' in st.secrets:
                return st.secrets['SKILLS_API_KEY']
        except Exception:
            pass
        return None
    
    def _headers(self) -> Dict:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers
    
    def get_public_skills(self) -> List[Dict]:
        """公開スキル一覧を取得"""
        try:
            response = requests.get(
                f"{self.base_url}/skills",
                headers=self._headers(),
                timeout=10
            )
            if response.status_code == 200:
                return response.json().get("skills", [])
        except Exception as e:
            print(f"公開スキル取得エラー: {e}")
        return []
    
    def get_user_skills(self) -> List[Dict]:
        """マイスキル一覧を取得（API Key認証必須）"""
        if not self.api_key:
            return []
        
        try:
            response = requests.get(
                f"{self.base_url}/user-skills",
                headers=self._headers(),
                timeout=10
            )
            if response.status_code == 200:
                return response.json().get("skills", [])
        except Exception as e:
            print(f"マイスキル取得エラー: {e}")
        return []
    
    def get_skill_content(self, skill_name: str, is_user_skill: bool = False) -> Optional[str]:
        """スキル内容を取得"""
        try:
            endpoint = f"/user-skills/{skill_name}" if is_user_skill else f"/skills/{skill_name}"
            response = requests.get(
                f"{self.base_url}{endpoint}",
                headers=self._headers(),
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("content") or data.get("skill", {}).get("content")
        except Exception as e:
            print(f"スキル内容取得エラー: {e}")
        return None
    
    def get_all_skills(self) -> List[Dict]:
        """公開スキル + マイスキルを統合取得"""
        public = self.get_public_skills()
        user = self.get_user_skills()
        
        # マイスキルにフラグを付与
        for skill in user:
            skill["is_user_skill"] = True
        
        return public + user
    
    def is_connected(self) -> bool:
        """API接続確認"""
        try:
            response = requests.get(
                f"{self.base_url}/skills",
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False


def get_skills_client() -> SkillsServerClient:
    """キャッシュ付きクライアント取得"""
    return SkillsServerClient()
