"""
3段階記憶検索システム
Stage 1: 直近10件 → Stage 2: 全アンカー → Stage 3: 全セッション
"""

from typing import Dict, List, Optional
from conversation_memory import memory
from firebase_history_manager import get_firebase_manager

class ThreeStageSearch:
    def __init__(self):
        self.firebase = get_firebase_manager()
    
    def search(self, query: str) -> Dict:
        """
        3段階検索実行
        
        Args:
            query: 検索クエリ
            
        Returns:
            {
                'stage': int (1/2/3),
                'data': List[Dict],
                'search_info': {
                    'stage1_checked': int,
                    'stage2_checked': int,
                    'stage3_checked': int,
                    'query': str
                }
            }
        """
        print(f"\n🔍 3段階記憶検索開始: '{query}'")
        
        search_info = {
            'query': query,
            'stage1_checked': 0,
            'stage2_checked': 0,
            'stage3_checked': 0
        }
        
        # Stage 1: 直近10件検索
        print("📚 Stage 1: 直近10件検索中...")
        stage1_result = self._search_recent_10(query)
        search_info['stage1_checked'] = 10
        
        if stage1_result:
            print(f"✅ Stage 1でヒット: {len(stage1_result)}件")
            return {
                'stage': 1,
                'data': stage1_result,
                'search_info': search_info
            }
        
        print("⚠️ Stage 1: ヒットなし")
        
        # Stage 2: 全アンカー検索
        print("🔖 Stage 2: 全アンカー検索中...")
        stage2_result = self._search_all_anchors(query)
        search_info['stage2_checked'] = len(memory.search_anchors(''))  # 全アンカー数取得
        
        if stage2_result:
            print(f"✅ Stage 2でヒット: {len(stage2_result)}件")
            return {
                'stage': 2,
                'data': stage2_result,
                'search_info': search_info
            }
        
        print("⚠️ Stage 2: ヒットなし")
        
        # Stage 3: 全セッション検索
        print("🌐 Stage 3: 全セッション検索中（重い処理）...")
        stage3_result = self._search_all_sessions(query)
        search_info['stage3_checked'] = len(self.firebase.get_all_sessions())
        
        if stage3_result:
            print(f"✅ Stage 3でヒット: {len(stage3_result)}件")
        else:
            print("❌ Stage 3: ヒットなし（全検索完了）")
        
        return {
            'stage': 3,
            'data': stage3_result,
            'search_info': search_info
        }
    
    def _search_recent_10(self, query: str) -> Optional[List[Dict]]:
        """Stage 1: 直近10件検索"""
        try:
            recent_sessions = self.firebase.get_recent_sessions(10)
            if not recent_sessions:
                return None
            
            results = self.firebase.search_sessions_by_keyword(query, recent_sessions)
            return results if results else None
            
        except Exception as e:
            print(f"❌ Stage 1エラー: {e}")
            return None
    
    def _search_all_anchors(self, query: str) -> Optional[List[Dict]]:
        """Stage 2: 全アンカー検索"""
        try:
            anchors = memory.search_anchors(query)
            return anchors if anchors else None
            
        except Exception as e:
            print(f"❌ Stage 2エラー: {e}")
            return None
    
    def _search_all_sessions(self, query: str) -> Optional[List[Dict]]:
        """Stage 3: 全セッション検索"""
        try:
            all_sessions = self.firebase.get_all_sessions(limit=1000)
            if not all_sessions:
                return None
            
            results = self.firebase.search_sessions_by_keyword(query, all_sessions)
            return results if results else None
            
        except Exception as e:
            print(f"❌ Stage 3エラー: {e}")
            return None
    
    def format_search_results(self, search_result: Dict) -> str:
        """
        検索結果を整形してプロンプト用テキスト生成
        
        Args:
            search_result: searchメソッドの戻り値
            
        Returns:
            整形されたテキスト
        """
        stage = search_result['stage']
        data = search_result['data']
        info = search_result['search_info']
        
        output = []
        output.append(f"=== 記憶検索結果（Stage {stage}でヒット） ===")
        output.append(f"検索クエリ: {info['query']}")
        output.append(f"検索範囲: Stage1({info['stage1_checked']}件) → Stage2({info['stage2_checked']}件) → Stage3({info['stage3_checked']}件)")
        output.append("")
        
        if not data:
            output.append("⚠️ 関連する記憶が見つかりませんでした")
            return "\n".join(output)
        
        # Stage 1/3: セッションデータ
        if stage in [1, 3]:
            output.append(f"【関連セッション: {len(data)}件】")
            for i, session in enumerate(data[:5], 1):  # 最大5件表示
                output.append(f"\n{i}. セッション {session.get('sessionId', 'unknown')}")
                output.append(f"   時刻: {session.get('timestamp', 'unknown')}")
                output.append(f"   入力: {session.get('userInput', '')[:100]}...")
                output.append(f"   応答: {session.get('geminiResponse', '')[:100]}...")
        
        # Stage 2: アンカーデータ
        elif stage == 2:
            output.append(f"【関連アンカー: {len(data)}件】")
            for i, anchor in enumerate(data[:5], 1):
                output.append(f"\n{i}. [{anchor['anchor_id']}]")
                output.append(f"   Keywords: {anchor['keywords']}")
                output.append(f"   内容: {anchor['content'][:200]}...")
        
        return "\n".join(output)

# グローバルインスタンス
search_engine = ThreeStageSearch()
