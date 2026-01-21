# ファイルバージョン管理システム

## 概要

Multi-Agent Systemにファイルの自動バージョン管理機能を追加しました。

### 主な機能

1. **自動バージョン保存**
   - ファイル作成・編集時に自動的にバージョンを保存
   - 日時秒単位でバージョン管理
   - 保存期間: 3日間

2. **履歴からの復元**
   - チャット履歴から会話を復元
   - ファイルバージョンから過去の状態を復元

3. **UI統合**
   - サイドバーからファイル履歴を閲覧
   - ワンクリックでバージョン復元

## ファイル構成

```
multi-agent-system/
├── file_version_manager.py      # バージョン管理システム本体
├── auto_version_hooks.py        # ファイル操作フック
├── file_operations.py           # ファイル操作ユーティリティ
├── test_file_operations.py      # テストコード
├── ui/
│   ├── file_history_panel.py   # ファイル履歴UI
│   └── conversation_history.py # 会話履歴UI (復元機能追加)
└── data/
    ├── file_versions.db         # ファイルバージョンDB
    └── conversation_memory.db   # 会話履歴DB
```

## 使い方

### 1. ファイル操作時の自動バージョン保存

```python
from file_operations import create_file_with_version, edit_file_with_version

# ファイル作成 (自動でバージョン保存)
result = create_file_with_version(
    "path/to/file.py",
    "print('Hello, World!')"
)

# ファイル編集 (自動でバージョン保存)
result = edit_file_with_version(
    "path/to/file.py",
    "print('Hello, Claude!')"
)
```

### 2. 手動バージョン保存

```python
from auto_version_hooks import save_current_file_version

# 既存ファイルの現在状態を保存
version = save_current_file_version("path/to/file.py")
```

### 3. バージョン履歴の確認

```python
from file_version_manager import file_version_manager

# ファイルの履歴取得
history = file_version_manager.get_file_history("path/to/file.py")

for h in history:
    print(f"v{h['version']}: {h['updated_at']}")
```

### 4. バージョンの復元

```python
# 特定バージョンの内容を取得
content = file_version_manager.restore_version("path/to/file.py", version=1)

# 実際のファイルに書き戻す
if content:
    with open("path/to/file.py", 'w') as f:
        f.write(content)
```

## UI操作

### サイドバー

1. **📂 ファイル履歴**
   - 管理中のファイル一覧を表示
   - ファイルを選択してバージョン履歴を閲覧

2. **バージョン操作**
   - 👁️ 表示: バージョンの内容をプレビュー
   - 🔄 復元: バージョンを復元

### メインエリア

- バージョン詳細表示
- ファイル内容のプレビュー
- 復元ボタン

## データベース設計

### file_versions テーブル

| カラム | 型 | 説明 |
|--------|------|------|
| id | INTEGER | 主キー |
| file_path | TEXT | ファイルパス |
| content | TEXT | ファイル内容 |
| content_hash | TEXT | コンテンツハッシュ |
| version | INTEGER | バージョン番号 |
| file_size | INTEGER | ファイルサイズ (バイト) |
| updated_at | TEXT | 更新日時 (ISO形式) |
| created_at | TEXT | 作成日時 |

### インデックス

- `idx_file_path`: file_path でのクエリ高速化
- `idx_updated_at`: 日付範囲検索の高速化

## 注意事項

1. **保存期間**
   - デフォルト: 3日間
   - 古いバージョンは自動削除

2. **重複チェック**
   - 同じ内容のファイルは重複保存しない
   - ハッシュ値で判定

3. **ファイルサイズ**
   - 大容量ファイルは注意
   - データベースサイズが増大する可能性

## テスト実行

```bash
cd /Users/miyatayasuhiro/Desktop/multi-agent-system
python test_file_operations.py
```

## 今後の拡張

- [ ] バージョン間の差分表示
- [ ] ファイル比較機能
- [ ] 圧縮保存対応
- [ ] クラウドバックアップ連携
