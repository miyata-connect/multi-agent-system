# Multi-Agent System 🤖

4つの最新LLMが協力してタスクを実行するマルチエージェントシステム

## チーム構成（2026年1月版）

| 役割 | モデル | 担当 |
|------|--------|------|
| 👑 司令塔 | Gemini 3 Pro | タスク振り分け |
| 👮‍♂️ 監査役 | GPT-5.2 | リスク分析 |
| 👨‍💻 コード役 | Claude Sonnet 4.5 | コード実装 |
| 🦙 データ役 | Llama 3.3 70B | データ要約 |

## ローカル実行

```bash
cd ~/Desktop/multi-agent-system
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Streamlit Cloudへのデプロイ

1. GitHubにリポジトリをプッシュ
2. [Streamlit Cloud](https://share.streamlit.io/) でアカウント作成
3. 「New app」→ リポジトリを選択
4. Settings > Secrets に以下を追加:

```toml
GEMINI_API_KEY = "your-gemini-api-key"
OPENAI_API_KEY = "your-openai-api-key"
ANTHROPIC_API_KEY = "your-anthropic-api-key"
GROQ_API_KEY = "your-groq-api-key"
```

5. デプロイ完了！URLでアクセス可能

## 使用例

- 「Pythonでソート関数を書いて」→ Claude コード役が実装
- 「この計画のリスクを分析して」→ GPT 監査役が分析
- 「この文章を要約して」→ Llama データ役が要約
