# agents/concierge/team.py
# 行数: 89行
# コンシェルジュチーム（聞き取り・情報収集）

from langchain_core.messages import HumanMessage, SystemMessage

from agents.base import TeamExecutor, get_ai_instance
from config import AI_MODELS, get_team_config


class ConciergeTeam(TeamExecutor):
    """
    コンシェルジュチーム
    - 長: Grok 4.1 Thinking（最終判断）
    - 作成役: Gemini 3 Pro（聞き取り）
    - チェック役: Perplexity（情報補完）
    """
    
    def __init__(self):
        super().__init__("concierge")
    
    def run(self, user_input: str, history: list = None) -> dict:
        """
        ユーザー入力を処理し、適切なチームに振り分ける
        """
        history = history or []
        
        # 1. 作成役（Gemini）が聞き取り・分析
        creator_result = self._run_creator(user_input, history)
        
        # 2. チェック役（Perplexity）が情報補完
        checker_result = self._run_checker(user_input, creator_result)
        
        # 3. 長（Grok）が最終判断
        leader_result = self._run_leader(user_input, creator_result, checker_result)
        
        # 4. 調停
        return self.resolve(
            leader_result=leader_result,
            checker_scores=[{
                "checker": AI_MODELS[self.config["checker"]]["name"],
                "evaluation": checker_result,
            }]
        )
    
    def _run_creator(self, user_input: str, history: list) -> str:
        """作成役: ユーザーの意図を分析"""
        system_prompt = """あなたは優秀なコンシェルジュです。
ユーザーの要求を正確に理解し、以下の形式で分析してください：

1. 要求の種類: [CODER] / [AUDITOR] / [DATA] / [SEARCH] / [SELF]
2. 具体的なタスク内容
3. 必要な追加情報（あれば）

ユーザーの話をよく聞き、曖昧な点があれば確認してください。"""
        
        messages = [SystemMessage(content=system_prompt)]
        for h in history[-10:]:
            messages.append(HumanMessage(content=str(h)))
        messages.append(HumanMessage(content=user_input))
        
        response = self.creator_ai.invoke(messages)
        return response.content
    
    def _run_checker(self, user_input: str, creator_result: str) -> str:
        """チェック役: 情報を補完"""
        system_prompt = """あなたは情報補完の専門家です。
作成役の分析結果を確認し、不足している情報や最新の関連情報を追加してください。
独立した評価を行い、採点してください（100点満点）。"""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"ユーザー入力: {user_input}\n\n作成役の分析:\n{creator_result}")
        ]
        
        response = self.checker_ai.invoke(messages)
        return response.content
    
    def _run_leader(self, user_input: str, creator_result: str, checker_result: str) -> str:
        """長: 最終判断"""
        system_prompt = """あなたはコンシェルジュチームの長です。
作成役とチェック役の結果を総合し、最終的な判断を下してください。

出力形式:
[タスク種別] タスク内容

タスク種別: CODER / AUDITOR / DATA / SEARCH / SELF"""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"""ユーザー入力: {user_input}

作成役の分析:
{creator_result}

チェック役の補完:
{checker_result}

上記を踏まえ、最終判断を下してください。""")
        ]
        
        response = self.leader_ai.invoke(messages)
        return response.content
