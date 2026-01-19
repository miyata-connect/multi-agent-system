# agents/data_team/team.py
# 行数: 105行
# データ確認・保存チーム（データ処理・整合性チェック）

from langchain_core.messages import HumanMessage, SystemMessage

from agents.base import TeamExecutor
from config import AI_MODELS


class DataTeam(TeamExecutor):
    """
    データ確認・保存チーム
    - 長: Llama 3.3 70B（最終判断）
    - 作成役: Llama 3.3 70B（保存処理）
    - チェック役: Grok 4.1 Thinking（整合性チェック）
    """
    
    def __init__(self):
        super().__init__("data")
    
    def run(self, data: str, operation: str = "process") -> dict:
        """
        データ処理タスクを実行
        operation: process / save / validate / transform
        """
        # 1. 作成役（Llama）がデータ処理
        creator_result = self._run_creator(data, operation)
        
        # 2. チェック役（Grok）が整合性チェック
        checker_result = self._run_checker(data, creator_result, operation)
        
        # 3. 長（Llama）が最終判断
        leader_result = self._run_leader(data, creator_result, checker_result, operation)
        
        # 4. 調停
        return self.resolve(
            leader_result=leader_result,
            checker_scores=[{
                "checker": AI_MODELS[self.config["checker"]]["name"],
                "evaluation": checker_result,
            }]
        )
    
    def _run_creator(self, data: str, operation: str) -> str:
        """作成役: データ処理"""
        system_prompt = f"""あなたはデータ処理の専門家です。
指定された操作（{operation}）を実行してください。

操作種別:
- process: データの加工・変換
- save: データの保存形式提案
- validate: データの検証
- transform: データ形式の変換

出力は構造化された形式で。"""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"操作: {operation}\n\nデータ:\n{data}")
        ]
        
        response = self.creator_ai.invoke(messages)
        return response.content
    
    def _run_checker(self, data: str, creator_result: str, operation: str) -> str:
        """チェック役: 整合性チェック"""
        system_prompt = """あなたはデータ整合性チェックの専門家です。
作成役の処理結果を検証してください。

確認項目:
1. データの完全性
2. 形式の正確性
3. 欠損・異常値
4. 処理の妥当性

採点: 100点満点"""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"操作: {operation}\n\n元データ:\n{data}\n\n処理結果:\n{creator_result}")
        ]
        
        response = self.checker_ai.invoke(messages)
        return response.content
    
    def _run_leader(self, data: str, creator_result: str, checker_result: str, operation: str) -> str:
        """長: 最終判断"""
        system_prompt = """あなたはデータチームの長です。
作成役の処理結果とチェック役の検証結果を踏まえ、最終的なデータ処理結果を出力してください。

問題があれば修正を反映してください。"""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"""操作: {operation}

元データ:
{data}

作成役の処理結果:
{creator_result}

チェック役の検証:
{checker_result}

上記を踏まえ、最終的な処理結果を出力してください。""")
        ]
        
        response = self.leader_ai.invoke(messages)
        return response.content
