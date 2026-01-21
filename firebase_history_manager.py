"""
Firebase会話履歴管理
全AI（Gemini/GPT/Claude/Llama）の会話履歴をFirebaseに保存・取得
"""

import os
import firebase_admin
from firebase_admin import credentials, db
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path

class FirebaseHistoryManager:
    def __init__(self, service_account_path: str, database_url: str, user_id: str):
        """
        Firebase初期化
        
        Args:
            service_account_path: サービスアカウントキーのパス
            database_url: Firebase Realtime DatabaseのURL
            user_id: ユーザーID
        """
        self.user_id = user_id
        self.database_url = database_url
        
        # Firebase初期化（既に初期化済みならスキップ）
        if not firebase_admin._apps:
            cred = credentials.Certificate(service_account_path)
            firebase_admin.initialize_app(cred, {
                'databaseURL': database_url
            })
        
        self.sessions_ref = db.reference(f'users/{user_id}/multiAgentSessions')
    
    def save_session(self, session_data: Dict):
        """
        セッション保存
        
        Args:
            session_data: {
                'userInput': str,
                'geminiResponse': str,
                'auditorCalls': [{input, output}],
                'coderCalls': [{input, output}],
                'dataCalls': [{input, output}]
            }
        """
        session_id = f"session_{int(datetime.now().timestamp() * 1000)}"
        
        self.sessions_ref.child(session_id).set({
            **session_data,
            'timestamp': datetime.now().isoformat(),
            'sessionId': session_id
        })
        
        return session_id
    
    def get_recent_sessions(self, limit: int = 10) -> List[Dict]:
        """
        直近N件のセッション取得
        
        Args:
            limit: 取得件数
            
        Returns:
            セッションデータのリスト（新しい順）
        """
        try:
            # 全セッション取得してソート
            all_sessions = self.sessions_ref.order_by_child('timestamp').get()
            
            if not all_sessions:
                return []
            
            # 辞書をリストに変換してソート
            sessions_list = []
            for session_id, data in all_sessions.items():
                data['sessionId'] = session_id
                sessions_list.append(data)
            
            # タイムスタンプでソート（新しい順）
            sessions_list.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            return sessions_list[:limit]
            
        except Exception as e:
            print(f"❌ Firebase取得エラー: {e}")
            return []
    
    def get_all_sessions(self, limit: int = 1000) -> List[Dict]:
        """
        全セッション取得（Stage 3用）
        
        Args:
            limit: 最大取得件数
            
        Returns:
            全セッションデータのリスト
        """
        try:
            all_sessions = self.sessions_ref.order_by_child('timestamp').limit_to_last(limit).get()
            
            if not all_sessions:
                return []
            
            sessions_list = []
            for session_id, data in all_sessions.items():
                data['sessionId'] = session_id
                sessions_list.append(data)
            
            # タイムスタンプでソート（新しい順）
            sessions_list.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            return sessions_list
            
        except Exception as e:
            print(f"❌ Firebase全件取得エラー: {e}")
            return []
    
    def search_sessions_by_keyword(self, keyword: str, sessions: List[Dict]) -> List[Dict]:
        """
        キーワード検索
        
        Args:
            keyword: 検索キーワード
            sessions: 検索対象セッションリスト
            
        Returns:
            ヒットしたセッションリスト
        """
        results = []
        keyword_lower = keyword.lower()
        
        for session in sessions:
            # ユーザー入力
            if keyword_lower in session.get('userInput', '').lower():
                results.append(session)
                continue
            
            # Gemini応答
            if keyword_lower in session.get('geminiResponse', '').lower():
                results.append(session)
                continue
            
            # 各AI呼び出し
            for ai_type in ['auditorCalls', 'coderCalls', 'dataCalls']:
                calls = session.get(ai_type, [])
                for call in calls:
                    if keyword_lower in str(call.get('input', '')).lower():
                        results.append(session)
                        break
                    if keyword_lower in str(call.get('output', '')).lower():
                        results.append(session)
                        break
        
        return results
    
    def clear_old_sessions(self, keep_days: int = 30):
        """
        古いセッション削除
        
        Args:
            keep_days: 保持日数
        """
        try:
            from datetime import timedelta
            cutoff_date = (datetime.now() - timedelta(days=keep_days)).isoformat()
            
            all_sessions = self.sessions_ref.get()
            if not all_sessions:
                return
            
            deleted_count = 0
            for session_id, data in all_sessions.items():
                if data.get('timestamp', '') < cutoff_date:
                    self.sessions_ref.child(session_id).delete()
                    deleted_count += 1
            
            print(f"🗑️ {deleted_count}件の古いセッションを削除しました")
            
        except Exception as e:
            print(f"❌ セッション削除エラー: {e}")

# グローバルインスタンス（遅延初期化）
_firebase_manager = None

def get_firebase_manager():
    """Firebase History Managerのシングルトン取得"""
    global _firebase_manager
    
    if _firebase_manager is None:
        # 環境変数またはデフォルトパスから設定取得
        service_account_path = os.getenv(
            'FIREBASE_SERVICE_ACCOUNT',
            str(Path(__file__).parent / 'service-account-key.json')
        )
        database_url = os.getenv(
            'FIREBASE_DATABASE_URL',
            'https://skills-server-a34a4-default-rtdb.firebaseio.com'
        )
        user_id = os.getenv('SKILLS_USER_ID', 'default_user')
        
        _firebase_manager = FirebaseHistoryManager(
            service_account_path,
            database_url,
            user_id
        )
    
    return _firebase_manager
