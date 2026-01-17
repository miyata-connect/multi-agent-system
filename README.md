# Multi-Agent System 🤖

**AIの嘘を減らす** - 5つの最先端LLMが協力して相互検証するマルチエージェントシステム

## 🎯 コンセプト

従来の単一AI（ChatGPT/Claude/Cursor）は便利だが、**間違った回答や動かないコードを生成する**問題がありました。

Multi-Agent Systemは**複数のAIが互いをチェックする**ことで、この問題を大幅に軽減します。

```
従来: ユーザー → AI → 回答（検証なし・嘘が混じる）
本システム: ユーザー → コンシェルジュ → 適切なAI → 高品質な回答
```

---

## 👥 エージェントチーム（2026年1月版）

| 役割 | モデル | 担当 |
|------|--------|------|
| 👑 コンシェルジュ | Gemini 3 Pro | タスク分析・振り分け・即答 |
| 👮‍♂️ 監査・レビュー | GPT-5.2 | コードレビュー・品質チェック |
| 👨‍💻 コード役 | Claude Sonnet 4.5 | コード実装 |
| 🔍 検索役 | Grok 4.1 Thinking | リアルタイム情報検索 |
| 🦙 データ役 | Llama 3.3 70B | データ要約・整理 |

---

## ✨ 主な機能

### 1. **コンシェルジュ方式（効率重視）**
```
簡単な質問 → Geminiが即答（API 1回）
コード依頼 → Claude実装 + GPTレビュー（API 2-4回）
検索依頼 → Grokが検索（API 2回）
```
**メリット**: 無駄なAPI呼び出しを削減し、コストと時間を節約

### 2. **コードレビューループ**
```
コード生成 → GPT監査役がレビュー → Claude修正 → 再レビュー（最大3回）
```
バグやセキュリティ問題を自動検出して修正します。

### 3. **クロスチェック（100点満点採点）**
```
実行AI以外の全AI（最大4つ）が結果を採点
- 正確性: /25点
- 妥当性: /25点  
- セキュリティ: /25点
- パフォーマンス: /25点
```
**注意**: デフォルトOFF。重要なタスク時のみ手動でONにすることを推奨。

### 4. **Skillsライブラリ（GitHub連携）**
```
GitHub上の6万件以上のSKILL.mdを検索・ダウンロード
- キーワード検索（langchain, python等）
- 使用履歴をSQLiteで記録
- よく使うSkillsの自動学習
```

### 5. **失敗透明性システム**
- SQLiteで全実行履歴を記録
- 24時間/7日間の失敗率をリアルタイム表示
- 失敗からの自動学習（SkillsMP統合予定）

---

## 📁 プロジェクト構造（モジュール化済み）

```
multi-agent-system/
├── app.py                  # メインUI
├── config.py               # APIキー・モデル設定
├── agents/                 # エージェント機能
│   ├── commander.py        # コンシェルジュ
│   ├── auditor.py          # 監査・レビュー
│   ├── coder.py            # コード役
│   ├── searcher.py         # 検索役（Grok）
│   └── data_processor.py   # データ役
├── core/                   # コア機能
│   ├── code_loop.py        # コードレビューループ
│   └── crosscheck.py       # クロスチェック機能
├── utils/                  # ヘルパー
│   └── helpers.py          # ユーティリティ関数
├── data/                   # データフォルダ
│   ├── skills_usage.db     # Skills使用履歴DB
│   └── external_skills/    # ダウンロードしたSkills
├── skills_downloader.py    # GitHub Skills検索・ダウンロード
├── failure_tracker.py      # 失敗記録システム
├── failure_analyzer.py     # 失敗分析エンジン
└── learning_integrator.py  # Skills学習統合
```

---

## 🚀 ローカル実行

### 前提条件
- Python 3.10以上
- 各AIサービスのAPIキー

### セットアップ

```bash
# 1. リポジトリをクローン
git clone https://github.com/miyata-connect/multi-agent-system.git
cd multi-agent-system

# 2. 仮想環境作成
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 依存関係インストール
pip install -r requirements.txt

# 4. .envファイル作成
cp .env.example .env
# .envを編集してAPIキーを設定

# 5. 起動
streamlit run app.py
```

### .env設定例

```bash
# Google Gemini（コンシェルジュ）
GEMINI_API_KEY=your-gemini-api-key

# OpenAI（監査・レビュー）
OPENAI_API_KEY=your-openai-api-key

# Anthropic Claude（コード役）
ANTHROPIC_API_KEY=your-anthropic-api-key

# xAI Grok（検索役）
XAI_API_KEY=your-xai-api-key

# Groq Llama（データ役）
GROQ_API_KEY=your-groq-api-key
```

---

## ☁️ Streamlit Cloudへのデプロイ

### 手順

1. **GitHubにプッシュ**
```bash
git add .
git commit -m "Initial commit"
git push
```

2. **Streamlit Cloudでデプロイ**
   - [Streamlit Cloud](https://share.streamlit.io/)にアクセス
   - 「New app」をクリック
   - リポジトリを選択
   - `app.py`を指定

3. **Secretsを設定**
   - Settings → Secrets
   - 以下をTOML形式で追加:

```toml
GEMINI_API_KEY = "your-gemini-api-key"
OPENAI_API_KEY = "your-openai-api-key"
ANTHROPIC_API_KEY = "your-anthropic-api-key"
XAI_API_KEY = "your-xai-api-key"
GROQ_API_KEY = "your-groq-api-key"
```

4. **デプロイ完了** 🎉

---

## 📊 使用例

### 即答（コンシェルジュ直接回答）
```
入力: 「日本の首都は？」
→ Gemini 3 Proが即答（API 1回のみ）
```

### コード生成
```
入力: 「FizzBuzzを書いて」
→ Claude Sonnet 4.5が実装
→ GPT-5.2がコードレビュー
→ 問題があれば自動修正
```

### 最新情報検索
```
入力: 「今日のビットコイン価格は？」
→ Grok 4.1 Thinkingがリアルタイム検索
```

### 重要タスク（クロスチェックON時）
```
入力: 「本番環境用のログイン認証システムを作って」
→ Claude実装 → GPTレビュー → 全AI採点（100点満点）
```

---

## 🎯 ターゲットユーザー

### こんな方におすすめ
- ✅ ChatGPT/Claude/Cursorに**裏切られた経験**がある開発者
- ✅ AIの**間違った回答**にウンザリしている方
- ✅ コード生成AIが**動かないコード**を出力して困った方
- ✅ 複数AIを**手動で使い分ける**のが面倒な方

### Multi-Agent Systemの価値
「AIの嘘が減る」ことで：
- ✅ デバッグ時間が削減
- ✅ コード品質が向上
- ✅ 安心してAIに任せられる

---

## 🔮 今後の予定

### Phase 1: 完了 ✅
- [x] 5AIシステム構築
- [x] コードレビューループ
- [x] クロスチェック機能
- [x] 失敗透明性システム
- [x] モジュール化
- [x] コンシェルジュ方式（効率化）
- [x] GitHub Skills検索・ダウンロード
- [x] Skills使用履歴DB（SQLite）

### Phase 2: 開発中 🚧
- [ ] Skills合成エンジン（A+B=C）
- [ ] バックグラウンド定期実行
- [ ] 並列処理（クロスチェック高速化）
- [ ] RAG機能（ドキュメント検索）
- [ ] ツール実行（bash/Python実行）

### Phase 3: 計画中 📋
- [ ] カスタムエージェント追加機能
- [ ] UI上でのモデル入れ替え機能
- [ ] チーム協働機能
- [ ] エクスポート機能（PDF/Markdown）

---

## 📝 ライセンス

MIT License

---

## 🙏 謝辞

このプロジェクトは以下の技術を使用しています：
- [Streamlit](https://streamlit.io/) - WebアプリUI
- [LangChain](https://www.langchain.com/) - LLM統合フレームワーク
- [SQLite](https://www.sqlite.org/) - 実行履歴管理

---

## 📞 お問い合わせ

- GitHub Issues: [Issues](https://github.com/miyata-connect/multi-agent-system/issues)
- 開発者: [@miyata-connect](https://github.com/miyata-connect)

---

**AIの嘘を減らし、開発者の生産性を向上させる。**  
**それがMulti-Agent Systemの使命です。**
