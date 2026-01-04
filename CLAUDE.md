# echo-me Project Context

## Overview
echo-meは、音声ファイルやMarkdownファイルからブログ・SNS投稿を自動生成するシステムです。

### 背景
- 会議の議事録や技術トピックを効率的にコンテンツ化したい
- 複数のプラットフォーム（ブログ、X、LinkedIn）向けに最適化された投稿を生成
- SAP/IT技術系のコンテンツを発信するワークフローを自動化

## System Flow

```
【INPUT】
音声(Plaud) / MDファイル
       ↓
Google Drive → NotebookLM（手動）
       ↓
【PROCESSING】
Claude API（ブログ/X/LinkedIn形式生成）
       ↓
【REVIEW】
Notion（レビュー・承認）
       ↓
【OUTPUT】
SAP Community / LinkedIn / X / JSUG / ASUG
+ Notion公式（ポートフォリオ）
```

## File Structure

```
echo-me/
├── CLAUDE.md                  # このファイル（Claude Code用コンテキスト）
├── src/
│   └── content_generator.py   # メインスクリプト
├── input/                     # 入力ファイル置き場
├── output/                    # 出力ファイル置き場
├── .env                       # API Key（.gitignore対象）
├── .gitignore
├── requirements.txt
└── README.md
```

## File Descriptions

| ファイル | 役割 |
|----------|------|
| `src/content_generator.py` | Claude APIを使用してコンテンツを生成するメインスクリプト |
| `input/` | Plaud AIの文字起こしやMDファイルを配置 |
| `output/` | 生成されたblog.md、x_post.txt、linkedin_post.txtを出力 |
| `.env` | ANTHROPIC_API_KEYを格納（Git管理外） |

## Input File Types

| 種類 | 形式 | 内容 |
|------|------|------|
| A | テキスト/MD | Plaud AIによる文字起こしMTG議事 |
| B | MD | Google Drive格納のSAP/IT技術系トピック |

## Output Files

| ファイル | 形式 | 説明 |
|----------|------|------|
| `blog.md` | Markdown | ブログ記事（構造化された長文） |
| `x_post.txt` | Plain Text | X(Twitter)投稿（280文字以内、ハッシュタグ付き） |
| `linkedin_post.txt` | Plain Text | LinkedIn投稿用テキスト |

## Development Rules

### コーディング規約
- Python 3.9+を使用
- PEP 8スタイルガイドに準拠
- 型ヒントを積極的に使用
- docstringはGoogle styleで記述
- エラーハンドリングは適切に実装

### 環境変数
- APIキーは必ず`.env`ファイルで管理
- `.env`ファイルは絶対にコミットしない

### 使用API
- Anthropic Claude API
- モデル: `claude-sonnet-4-20250514`

### 実行ルール
- 長時間処理はバックグラウンド実行を基本とする
- 実行ログはoutput.logに出力

## Usage

### 通常実行

```bash
# 基本的な使用方法
python src/content_generator.py input/sample.txt
python src/content_generator.py input/sample.md

# 出力は output/ ディレクトリに生成される
```

### バックグラウンド実行（推奨）

```powershell
# Windows PowerShell
Start-Process -NoNewWindow python -ArgumentList "src/content_generator.py", "input/sample.txt"
```

```bash
# Linux/Mac
nohup python src/content_generator.py input/sample.txt > output.log 2>&1 &
```

## Future Development (Phase 2以降)

### Phase 2: 自動化強化
- Google Drive連携によるファイル自動取得
- Notion API連携によるレビューワークフロー

### Phase 3: 配信自動化
- X API連携による自動投稿
- LinkedIn API連携による自動投稿
- SAP Community連携

### Phase 4: AI強化
- コンテンツの品質スコアリング
- トレンド分析による最適投稿時間提案
- マルチ言語対応（日英）
