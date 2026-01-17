import os
import sys
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, SystemMessage

from tools import call_auditor, call_coder, call_data_processor

# 環境変数を読み込む
load_dotenv()

# ==========================================
# APIキー確認
# ==========================================
gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
openai_key = os.getenv("OPENAI_API_KEY")
anthropic_key = os.getenv("ANTHROPIC_API_KEY")
groq_key = os.getenv("GROQ_API_KEY")

missing_keys = []
if not gemini_key:
    missing_keys.append("GEMINI_API_KEY")
if not openai_key:
    missing_keys.append("OPENAI_API_KEY")
if not anthropic_key:
    missing_keys.append("ANTHROPIC_API_KEY")
if not groq_key:
    missing_keys.append("GROQ_API_KEY")

if missing_keys:
    print(f"❌ エラー: 以下のAPIキーが.envファイルにありません: {', '.join(missing_keys)}")
    sys.exit(1)

# Google APIキーを環境変数にセット（langchain-google-genai用）
os.environ["GOOGLE_API_KEY"] = gemini_key

# ==========================================
# 司令塔 (Gemini 3 Pro) の設定
# ==========================================
llm = ChatGoogleGenerativeAI(
    model="gemini-3-pro-preview",
    temperature=0.5,
)

# ==========================================
# チーム結成（ツールを持たせる）
# ==========================================
tools = [call_auditor, call_coder, call_data_processor]

# システムプロンプト
SYSTEM_PROMPT = """あなたは優秀なプロジェクトマネージャー（司令塔）です。
ユーザーからの依頼に応じて、適切な部下（ツール）を選んでタスクを実行してください。

利用可能な部下:
1. call_auditor: 監査役（GPT-5.2）- 計画のリスク分析、懸念点の指摘
2. call_coder: コード役（Claude Sonnet 4.5）- コード実装、プログラミング
3. call_data_processor: データ役（Llama 3.3 70B）- データ要約、情報整理

必ず日本語で回答してください。
複雑なタスクは複数の部下を順番に使って解決してください。"""

# エージェント作成（promptパラメータを使用）
agent_executor = create_react_agent(
    llm,
    tools,
    prompt=SYSTEM_PROMPT
)

# ==========================================
# 実行ループ
# ==========================================
def main():
    print("\n" + "=" * 60)
    print("🚀 最強のエージェントチームが起動しました (2026年1月版)")
    print("=" * 60)
    print("   👑 司令塔: Gemini 3 Pro")
    print("   👮‍♂️ 監査役: GPT-5.2")
    print("   👨‍💻 コード役: Claude Sonnet 4.5")
    print("   🦙 データ役: Llama 3.3 70B (Groq)")
    print("=" * 60)
    print("終了するには 'exit' または 'quit' と入力してください。\n")

    while True:
        try:
            user_input = input("あなた: ").strip()
            
            # 終了コマンド
            if user_input.lower() in ["exit", "quit", "終了", "q"]:
                print("👋 システムを終了します。お疲れ様でした！")
                break
            
            # 空入力は無視
            if not user_input:
                continue

            print("\n⏳ Gemini 3 Proが思考中... 必要な部下を選定しています...\n")
            
            # エージェント実行
            result = agent_executor.invoke({
                "messages": [HumanMessage(content=user_input)]
            })
            
            # 最終回答を取得
            final_message = result["messages"][-1]
            if hasattr(final_message, 'content') and final_message.content:
                print(f"🤖 Gemini: {final_message.content}\n")

        except KeyboardInterrupt:
            print("\n👋 中断されました。システムを終了します。")
            break
        except Exception as e:
            print(f"\n❌ エラーが発生しました: {e}")
            import traceback
            traceback.print_exc()
            print("ヒント: APIキーが正しいか、ライブラリが最新かを確認してください。\n")

if __name__ == "__main__":
    main()
