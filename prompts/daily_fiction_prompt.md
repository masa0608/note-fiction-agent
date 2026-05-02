---
created: '2026-05-02'
status: active
tags:
- llm
title: Daily Fiction Generation Prompt
updated: '2026-05-02'
---

# Daily Fiction Generation Prompt

このファイルはプロンプトのメタドキュメントです。
実際のプロンプトは weekday_serial_prompt.md と weekend_standalone_prompt.md を使用します。

## プロンプト生成の流れ

1. 曜日を判定（JST）
2. 平日（月〜金）→ weekday_serial_prompt.md
3. 土日 → weekend_standalone_prompt.md
4. テンプレートにコンテキストを埋め込む
5. Claude APIに送信