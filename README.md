# note創作小説 自動生成エージェント

毎日17時（日本時間）に、noteに投稿できる創作小説を自動生成し、GitHubリポジトリに保存するシステムです。

## 概要

- **平日（月〜金）**：10分で読める連載小説（1週間で完結）
- **土日**：20分で読める単発小説
- GitHub Actionsで毎日UTC 08:00（JST 17:00）に自動実行
- Claude APIを使って高品質な小説を生成
- 品質チェックで内容を自動検証・再生成

## セットアップ手順

### 1. リポジトリをGitHubにPush

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/note-fiction-agent.git
git push -u origin main
```

### 2. GitHub Secretsを設定

GitHubリポジトリの **Settings > Secrets and variables > Actions** を開き、以下を追加：

| Secret名 | 値 |
|---|---|
| `ANTHROPIC_API_KEY` | AnthropicのAPIキー（[console.anthropic.com](https://console.anthropic.com)で取得） |

### 3. GitHub Actionsを有効化

リポジトリの **Actions** タブを開き、ワークフローを有効化します。

## 実行の仕組み

```
毎日JST 17:00（UTC 08:00）
    ↓
GitHub Actions起動
    ↓
generate_daily_fiction.py 実行
    ↓
月曜日の場合 → 今週の連載企画を作成
平日の場合  → 前話の続きを生成
土日の場合  → 単発小説を生成
    ↓
品質チェック（問題があれば最大2回再生成）
    ↓
output/YYYY-MM-DD_note.md に保存
    ↓
GitHubにコミット・プッシュ
```

## 手動実行方法

### GitHub上で手動実行

1. **Actions** タブを開く
2. **Daily Fiction Generator** をクリック
3. **Run workflow** ボタンをクリック

### ローカルで実行（テスト用）

```bash
# 依存関係インストール
pip install anthropic

# APIキーを設定
export ANTHROPIC_API_KEY=your_api_key_here

# 実行
cd note-fiction-agent
python src/generate_daily_fiction.py
```

## 出力ファイルの見方

生成されたファイルは `output/YYYY-MM-DD_note.md` に保存されます。

```
output/
  2026-05-05_note.md  ← 月曜日：連載第1話
  2026-05-06_note.md  ← 火曜日：連載第2話
  ...
  2026-05-10_note.md  ← 土曜日：単発小説
```

ファイルの構成：
- **YAMLフロントマター**：タイトル・タイプ・ハッシュタグ等のメタデータ
- **タイトル案**：5つのタイトル候補
- **本文**：投稿用の小説本文
- **ハッシュタグ**：note投稿用タグ
- **投稿文メモ**：一言コメント3案
- **明日への引き継ぎメモ**：連載管理用（投稿不要）
- **品質レビュー**：自動評価スコア（投稿不要）

## note投稿時の使い方

1. `output/` フォルダから当日のファイルを開く
2. **本文** セクションをコピーしてnoteに貼り付け
3. **タイトル案** から好きなものを選択（または推奨タイトルを使用）
4. **ハッシュタグ** をコピーしてnoteのタグ欄に入力
5. **投稿文メモ** から一言コメントを選択（任意）
6. 内容を軽く確認してから投稿

> 自動投稿機能は含まれていません。必ず内容を確認してから投稿してください。

## テーマや文体を変更する方法

### テーマを変更する

`src/utils.py` の `WEEKDAY_THEMES` または `WEEKEND_THEMES` リストを編集してください。

### 文体ルールを変更する

`config/writing_rules.md` を編集してください。

### 文字数を変更する

`config/writing_rules.md` の文字数セクションを編集し、`src/quality_checker.py` の数値も合わせて変更してください。

### ハッシュタグのデフォルトを変更する

`config/hashtag_rules.md` を編集してください。

## 注意事項

- 生成された小説は必ず投稿前に内容を確認してください
- Claude APIの利用料金が発生します（月の使用量によって変動）
- 品質チェックは基本的な確認のみです。センシティブな内容が含まれないか確認してください
- 連載状態は `data/story_state.json` で管理されています。手動でリセットしたい場合はこのファイルを編集してください

## ファイル構成

```
note-fiction-agent/
├── .github/workflows/daily-fiction.yml  # GitHub Actions
├── config/                              # 設定ファイル
├── data/                                # 状態管理ファイル
├── output/                              # 生成済み原稿
├── prompts/                             # プロンプトテンプレート
└── src/                                 # Pythonスクリプト
    ├── generate_daily_fiction.py        # メインスクリプト
    ├── story_planner.py                 # 連載管理
    ├── quality_checker.py               # 品質チェック
    └── utils.py                         # ユーティリティ
```
