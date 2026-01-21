#!/bin/bash
# Git追跡ファイル整理スクリプト
# 実行場所: /Users/miyatayasuhiro/Desktop/multi-agent-system

echo "======================================"
echo "Git追跡ファイル整理開始"
echo "======================================"
echo ""

# 現在のディレクトリを確認
echo "📂 作業ディレクトリ: $(pwd)"
echo ""

# Step 1: .gitignoreを追加
echo "Step 1: .gitignoreを更新..."
git add .gitignore
echo "✅ .gitignore追加完了"
echo ""

# Step 2: 既存機能ファイルを追加
echo "Step 2: 既存機能ファイルを追加..."
git add cross_context_manager.py
git add firebase_history_manager.py
git add past_threads_loader.py
git add team_evaluator.py
git add three_stage_search.py
git add ui/todo_panel.py
echo "✅ 6ファイル追加完了"
echo ""

# Step 3: 状態確認
echo "Step 3: Git状態確認..."
git status
echo ""

# Step 4: コミット
echo "Step 4: コミット実行..."
git commit -m "chore: 既存機能ファイルをGit追跡に追加、機密情報を除外

追加ファイル:
- cross_context_manager.py: AI間のコンテキスト共有
- firebase_history_manager.py: Firebase履歴管理
- past_threads_loader.py: 過去スレッド読み込み
- team_evaluator.py: チーム評価システム
- three_stage_search.py: 3段階検索システム
- ui/todo_panel.py: ToDoパネルUI

.gitignore更新:
- service-account-key.json除外（機密情報）
- data/*.db除外（個人データベース）
- ファイルバージョン・会話履歴・チーム評価のDB除外"
echo ""

# Step 5: Push
echo "Step 5: GitHubへPush..."
git push origin main
echo ""

echo "======================================"
echo "✅ 完了！"
echo "======================================"
