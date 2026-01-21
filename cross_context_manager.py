"""
クロスコンテキスト管理システム
全AI（Gemini/GPT/Claude/Llama）が互いの文脈を共有
"""

from typing import Dict, List
from conversation_memory import memory
from firebase_history_manager import get_firebase_manager

class CrossContextManager:
    def __init__(self):
        self.firebase = get_firebase_manager()
    
    def build_cross_context(self, search_result: Dict) -> Dict:
        """
        全AI用のクロスコンテキスト生成
        
        Args:
            search_result: 3段階検索の結果
            
        Returns:
            {
                'session_overview': str,
                'gemini_history': List[Dict],
                'auditor_history': List[Dict],
                'coder_history': List[Dict],
                'data_history': List[Dict],
                'cross_references': Dict,
                'search_context': str
            }
        """
        # 各AIの履歴取得（過去10回）
        session_history = memory.get_session_history(100)  # 十分な量を取得
        
        gemini_history = [msg for msg in session_history if msg.get('ai_type') == 'Gemini'][-10:]
        auditor_history = [msg for msg in session_history if msg.get('ai_type') == 'auditor'][-10:]
        coder_history = [msg for msg in session_history if msg.get('ai_type') == 'coder'][-10:]
        data_history = [msg for msg in session_history if msg.get('ai_type') == 'data_processor'][-10:]
        
        # クロスリファレンス生成
        cross_references = self._build_cross_references(
            gemini_history, auditor_history, coder_history, data_history
        )
        
        # セッション概要
        session_overview = self._generate_session_overview(session_history[-20:])
        
        return {
            'session_overview': session_overview,
            'gemini_history': gemini_history,
            'auditor_history': auditor_history,
            'coder_history': coder_history,
            'data_history': data_history,
            'cross_references': cross_references,
            'search_context': search_result
        }
    
    def _build_cross_references(self, gemini_hist, auditor_hist, coder_hist, data_hist) -> Dict:
        """
        AI間の相互参照情報を構築
        """
        refs = {
            'auditor_warnings': [],
            'coder_implementations': [],
            'data_summaries': [],
            'gemini_decisions': []
        }
        
        # 監査役の警告を抽出
        for msg in auditor_hist:
            content = msg.get('content', '')
            if 'リスク' in content or '懸念' in content or '問題' in content:
                refs['auditor_warnings'].append({
                    'timestamp': msg.get('timestamp', ''),
                    'summary': content[:100] + '...'
                })
        
        # コード役の実装を抽出
        for msg in coder_hist:
            content = msg.get('content', '')
            if '```' in content:  # コードブロックあり
                refs['coder_implementations'].append({
                    'timestamp': msg.get('timestamp', ''),
                    'summary': 'コード実装実施'
                })
        
        # データ役の要約を抽出
        for msg in data_hist:
            refs['data_summaries'].append({
                'timestamp': msg.get('timestamp', ''),
                'summary': msg.get('content', '')[:100] + '...'
            })
        
        # Geminiの決定を抽出
        for msg in gemini_hist:
            content = msg.get('content', '')
            if 'call_' in content:  # ツール呼び出し
                refs['gemini_decisions'].append({
                    'timestamp': msg.get('timestamp', ''),
                    'summary': '部下に指示を出した'
                })
        
        return refs
    
    def _generate_session_overview(self, recent_messages: List[Dict]) -> str:
        """
        セッション概要生成
        """
        if not recent_messages:
            return "新規セッション"
        
        user_messages = [msg for msg in recent_messages if msg.get('role') == 'user']
        
        if len(user_messages) == 0:
            return "会話開始"
        
        topics = []
        for msg in user_messages[-5:]:  # 直近5件のユーザー入力
            content = msg.get('content', '')[:50]
            topics.append(content)
        
        return f"継続中のトピック: {', '.join(topics)}"
    
    def format_for_gemini(self, cross_context: Dict) -> str:
        """
        Gemini司令塔用にフォーマット
        """
        parts = []
        parts.append("=== 全体セッション状況 ===")
        parts.append(cross_context['session_overview'])
        parts.append("")
        
        # Gemini自身の過去
        if cross_context['gemini_history']:
            parts.append("【あなた（Gemini）の過去10回の判断】")
            for i, msg in enumerate(cross_context['gemini_history'][-5:], 1):
                parts.append(f"{i}. {msg.get('content', '')[:100]}...")
            parts.append("")
        
        # 部下たちの状況
        parts.append("【部下たちの最近の活動】")
        
        if cross_context['auditor_history']:
            parts.append(f"📊 監査役: {len(cross_context['auditor_history'])}回の監査実施")
            if cross_context['cross_references']['auditor_warnings']:
                parts.append(f"   ⚠️ {len(cross_context['cross_references']['auditor_warnings'])}件の警告あり")
        
        if cross_context['coder_history']:
            parts.append(f"💻 コード役: {len(cross_context['coder_history'])}回のコード作成")
            if cross_context['cross_references']['coder_implementations']:
                parts.append(f"   ✅ {len(cross_context['cross_references']['coder_implementations'])}件の実装完了")
        
        if cross_context['data_history']:
            parts.append(f"📈 データ役: {len(cross_context['data_history'])}回のデータ処理")
        
        parts.append("")
        
        # 検索結果
        search_info = cross_context['search_context']
        parts.append(f"【記憶検索結果】Stage {search_info['stage']}でヒット")
        
        return "\n".join(parts)
    
    def format_for_subordinate(self, cross_context: Dict, ai_type: str) -> str:
        """
        部下AI用にフォーマット
        
        Args:
            cross_context: クロスコンテキスト
            ai_type: 'auditor', 'coder', 'data_processor'
        """
        parts = []
        parts.append("=== チーム全体の文脈 ===")
        parts.append(cross_context['session_overview'])
        parts.append("")
        
        # Geminiの指示履歴
        if cross_context['gemini_history']:
            parts.append("【司令塔（Gemini）の最近の指示】")
            for msg in cross_context['gemini_history'][-3:]:
                parts.append(f"- {msg.get('content', '')[:100]}...")
            parts.append("")
        
        # 他の部下の活動
        parts.append("【他の部下の活動】")
        
        if ai_type != 'auditor' and cross_context['auditor_history']:
            parts.append(f"監査役: {len(cross_context['auditor_history'])}回活動")
            warnings = cross_context['cross_references']['auditor_warnings']
            if warnings:
                parts.append(f"  最新の警告: {warnings[-1]['summary']}")
        
        if ai_type != 'coder' and cross_context['coder_history']:
            parts.append(f"コード役: {len(cross_context['coder_history'])}回活動")
            impls = cross_context['cross_references']['coder_implementations']
            if impls:
                parts.append(f"  最新実装: {impls[-1]['timestamp']}")
        
        if ai_type != 'data_processor' and cross_context['data_history']:
            parts.append(f"データ役: {len(cross_context['data_history'])}回活動")
        
        parts.append("")
        
        # 自分の過去活動
        history_key = f"{ai_type}_history"
        own_history = cross_context.get(history_key, [])
        if own_history:
            parts.append(f"【あなた自身の過去{len(own_history)}回の活動】")
            for i, msg in enumerate(own_history[-5:], 1):
                parts.append(f"{i}. {msg.get('content', '')[:100]}...")
        
        return "\n".join(parts)

# グローバルインスタンス
cross_context = CrossContextManager()
