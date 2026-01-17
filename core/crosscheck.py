# core/crosscheck.py
# 行数: 95行
# クロスチェック機能

from langchain_core.messages import HumanMessage
from config import get_commander, get_auditor, get_coder, get_searcher, get_data_processor
from utils import extract_content

def cross_check(agent_type: str, result: str, original_task: str) -> dict:
    """
    クロスチェック機能: 全5つのAIが結果を100点満点で採点（実行者も含む）
    
    Args:
        agent_type: 実行したエージェント ("auditor", "coder", "data", "searcher", "commander", "coder_loop")
        result: エージェントの出力結果
        original_task: 元のタスク内容
    
    Returns:
        dict: 採点結果と改善提案
    """
    # 全AIリスト（5つ全て）
    all_checkers = [
        ("commander", get_commander(), "👑 司令塔(Gemini 3 Pro)"),
        ("auditor", get_auditor(), "👮‍♂️ 監査役(GPT-5.2)"),
        ("coder", get_coder(), "👨‍💻 コード役(Claude Sonnet 4.5)"),
        ("searcher", get_searcher(), "🔍 検索役(Grok 4.1 Thinking)"),
        ("data", get_data_processor(), "🦙 データ役(Llama 3.3 70B)")
    ]
    
    # 全AIが採点（実行者も自己評価として参加）
    checkers = all_checkers
    
    check_results = []
    
    for checker_type, checker_model, checker_name in checkers:
        prompt = f"""以下の出力結果を100点満点で採点してください。

【元のタスク】
{original_task}

【実行エージェントの出力】
{result}

【採点基準】
1. 正確性 (25点): タスクの要求を正確に満たしているか
2. 妥当性 (25点): ロジックや論理展開が妥当か
3. セキュリティ (25点): セキュリティリスクはないか
4. パフォーマンス (25点): 効率的で最適な実装/回答か

【出力形式】
正確性: X/25点
妥当性: Y/25点
セキュリティ: Z/25点
パフォーマンス: W/25点
合計: N/100点

改善提案:
- 具体的な改善点を箇条書きで記載
"""
        
        try:
            messages = [HumanMessage(content=prompt)]
            response = checker_model.invoke(messages)
            check_results.append({
                "checker": checker_name,
                "evaluation": response.content
            })
        except Exception as e:
            check_results.append({
                "checker": checker_name,
                "evaluation": f"❌ 評価エラー: {str(e)}"
            })
    
    return {
        "checks": check_results,
        "total_checkers": len(check_results)
    }

def generate_crosscheck_summary(check_results: list) -> str:
    """
    クロスチェック結果をまとめる
    
    Args:
        check_results: 各AIの採点結果リスト
    
    Returns:
        str: まとめテキスト
    """
    # 全評価を連結
    all_evaluations = "\n\n".join([
        f"{check['checker']}の評価:\n{check['evaluation']}"
        for check in check_results
    ])
    
    prompt = f"""以下は、複数のAIエージェントが同じ出力結果を採点した結果です。
これらの評価を総合的に分析し、以下の形式でまとめてください：

【各AIの評価】
{all_evaluations}

【出力形式】
総合得点: X/100点 (各AIの合計得点の平均)

共通する評価:
- ポジティブな点を箇条書き

改善が必要な点:
- 複数のAIが指摘した共通の問題点を箇条書き

総合評価:
- 1-2文で総括
"""
    
    try:
        commander = get_commander()
        messages = [HumanMessage(content=prompt)]
        response = commander.invoke(messages)
        return extract_content(response)
    except Exception as e:
        return f"❌ まとめ生成エラー: {str(e)}"
