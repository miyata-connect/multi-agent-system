# agents/coder_team/team.py
# 行数: 112行
# コーディングチーム（実装・レビュー・破壊テスト）

from langchain_core.messages import HumanMessage, SystemMessage

from agents.base import TeamExecutor
from config import AI_MODELS


class CoderTeam(TeamExecutor):
    """
    コーディングチーム
    - 長: Claude Sonnet 4.5（最終判断）
    - 作成役: Claude Sonnet 4.5（実装）
    - チェック役: GPT-5.2（レビュー/破壊テスト）
    """
    
    def __init__(self):
        super().__init__("coder")
    
    def run(self, task: str, context: str = "") -> dict:
        """
        コーディングタスクを実行
        """
        # 1. 作成役（Claude）がコード作成
        creator_result = self._run_creator(task, context)
        
        # 2. チェック役（GPT）がレビュー・破壊テスト
        checker_result = self._run_checker(task, creator_result)
        
        # 3. 長（Claude）が最終判断・修正
        leader_result = self._run_leader(task, creator_result, checker_result)
        
        # 4. 調停
        return self.resolve(
            leader_result=leader_result,
            checker_scores=[{
                "checker": AI_MODELS[self.config["checker"]]["name"],
                "evaluation": checker_result,
            }]
        )
    
    def _run_creator(self, task: str, context: str) -> str:
        """作成役: コード実装"""
        system_prompt = """あなたは優秀なソフトウェアエンジニアです。
要求されたコードを実装してください。

ルール:
- コードは省略せず完全版を出力
- 行数を明記
- エラーハンドリングを含める
- コメントは日本語で"""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"タスク: {task}\n\nコンテキスト:\n{context}" if context else f"タスク: {task}")
        ]
        
        response = self.creator_ai.invoke(messages)
        return response.content
    
    def _run_checker(self, task: str, creator_result: str) -> str:
        """チェック役: レビュー・破壊テスト"""
        system_prompt = """あなたはコードレビューと破壊テストの専門家です。

以下の観点で評価してください:
1. バグ・脆弱性の有無
2. エッジケースの考慮
3. パフォーマンス問題
4. 可読性・保守性
5. ベストプラクティス準拠

採点: 100点満点
問題があれば具体的な修正案を提示してください。"""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"タスク: {task}\n\n作成されたコード:\n{creator_result}")
        ]
        
        response = self.checker_ai.invoke(messages)
        return response.content
    
    def _run_leader(self, task: str, creator_result: str, checker_result: str) -> str:
        """長: 最終判断・修正"""
        system_prompt = """あなたはコーディングチームの長です。
作成役のコードとチェック役のレビュー結果を踏まえ、最終的なコードを出力してください。

ルール:
- チェック役の指摘が妥当なら修正を反映
- コードは省略せず完全版を出力
- 行数を明記"""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"""タスク: {task}

作成役のコード:
{creator_result}

チェック役のレビュー:
{checker_result}

上記を踏まえ、最終的なコードを出力してください。""")
        ]
        
        response = self.leader_ai.invoke(messages)
        return response.content
