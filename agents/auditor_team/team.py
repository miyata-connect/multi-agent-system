# agents/auditor_team/team.py
# 行数: 105行
# 監査・レビューチーム（分析・穴探し）

from langchain_core.messages import HumanMessage, SystemMessage

from agents.base import TeamExecutor
from config import AI_MODELS


class AuditorTeam(TeamExecutor):
    """
    監査・レビューチーム
    - 長: GPT-5.2（最終判断）
    - 作成役: Claude Sonnet 4.5（分析）
    - チェック役: Gemini 3 Pro（穴探し）
    """
    
    def __init__(self):
        super().__init__("auditor")
    
    def run(self, target: str, context: str = "") -> dict:
        """
        監査・レビュータスクを実行
        """
        # 1. 作成役（Claude）が分析
        creator_result = self._run_creator(target, context)
        
        # 2. チェック役（Gemini）が穴探し
        checker_result = self._run_checker(target, creator_result)
        
        # 3. 長（GPT）が最終判断
        leader_result = self._run_leader(target, creator_result, checker_result)
        
        # 4. 調停
        return self.resolve(
            leader_result=leader_result,
            checker_scores=[{
                "checker": AI_MODELS[self.config["checker"]]["name"],
                "evaluation": checker_result,
            }]
        )
    
    def _run_creator(self, target: str, context: str) -> str:
        """作成役: 分析"""
        system_prompt = """あなたは優秀な監査・分析の専門家です。
対象を詳細に分析し、以下の観点でレポートしてください：

1. 構造・設計の妥当性
2. リスク・問題点
3. 改善提案
4. 総合評価（100点満点）"""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"対象:\n{target}\n\nコンテキスト:\n{context}" if context else f"対象:\n{target}")
        ]
        
        response = self.creator_ai.invoke(messages)
        return response.content
    
    def _run_checker(self, target: str, creator_result: str) -> str:
        """チェック役: 穴探し"""
        system_prompt = """あなたは批判的分析の専門家です。
作成役の分析を検証し、見落としている問題点や穴を探してください。

出力:
1. 見落とし・盲点
2. 追加のリスク
3. 反論・別視点
4. 独立採点（100点満点）"""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"対象:\n{target}\n\n作成役の分析:\n{creator_result}")
        ]
        
        response = self.checker_ai.invoke(messages)
        return response.content
    
    def _run_leader(self, target: str, creator_result: str, checker_result: str) -> str:
        """長: 最終判断"""
        system_prompt = """あなたは監査チームの長です。
作成役の分析とチェック役の穴探し結果を総合し、最終的な監査レポートを作成してください。

出力:
1. 総合評価
2. 主要な発見事項
3. リスクと対策
4. 結論"""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"""対象:
{target}

作成役の分析:
{creator_result}

チェック役の穴探し:
{checker_result}

上記を踏まえ、最終的な監査レポートを作成してください。""")
        ]
        
        response = self.leader_ai.invoke(messages)
        return response.content
