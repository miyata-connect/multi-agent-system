# agents/searcher_team/team.py
# 行数: 108行
# 検索チーム（検索実行・結果検証）

from langchain_core.messages import HumanMessage, SystemMessage

from agents.base import TeamExecutor
from config import AI_MODELS


class SearcherTeam(TeamExecutor):
    """
    検索チーム
    - 長: Grok 4.1 Thinking（最終判断）
    - 作成役: Perplexity（検索実行）
    - チェック役: Llama 3.3 70B（結果検証）
    """
    
    def __init__(self):
        super().__init__("searcher")
    
    def run(self, query: str, context: str = "") -> dict:
        """
        検索タスクを実行
        """
        # 1. 作成役（Perplexity）が検索実行
        creator_result = self._run_creator(query, context)
        
        # 2. チェック役（Llama）が結果検証
        checker_result = self._run_checker(query, creator_result)
        
        # 3. 長（Grok）が最終判断・統合
        leader_result = self._run_leader(query, creator_result, checker_result)
        
        # 4. 調停
        return self.resolve(
            leader_result=leader_result,
            checker_scores=[{
                "checker": AI_MODELS[self.config["checker"]]["name"],
                "evaluation": checker_result,
            }]
        )
    
    def _run_creator(self, query: str, context: str) -> str:
        """作成役: 検索実行"""
        system_prompt = """あなたは検索の専門家です。
クエリに基づいて最新かつ正確な情報を検索・収集してください。

出力:
1. 検索結果の要約
2. 主要な情報源
3. 関連する追加情報
4. 信頼度評価"""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"検索クエリ: {query}\n\nコンテキスト:\n{context}" if context else f"検索クエリ: {query}")
        ]
        
        response = self.creator_ai.invoke(messages)
        return response.content
    
    def _run_checker(self, query: str, creator_result: str) -> str:
        """チェック役: 結果検証"""
        system_prompt = """あなたは情報検証の専門家です。
検索結果の信頼性と正確性を検証してください。

確認項目:
1. 情報の信頼性
2. 情報源の質
3. 最新性
4. バイアスの有無
5. 欠落している観点

採点: 100点満点"""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"検索クエリ: {query}\n\n検索結果:\n{creator_result}")
        ]
        
        response = self.checker_ai.invoke(messages)
        return response.content
    
    def _run_leader(self, query: str, creator_result: str, checker_result: str) -> str:
        """長: 最終判断・統合"""
        system_prompt = """あなたは検索チームの長です。
検索結果と検証結果を統合し、最終的な回答を作成してください。

出力:
1. 回答（質問に対する直接的な答え）
2. 根拠（情報源）
3. 注意点・限界
4. 追加調査が必要な点（あれば）"""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"""検索クエリ: {query}

検索結果:
{creator_result}

検証結果:
{checker_result}

上記を踏まえ、最終的な回答を作成してください。""")
        ]
        
        response = self.leader_ai.invoke(messages)
        return response.content
