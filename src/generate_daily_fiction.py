#!/usr/bin/env python3
"""
Note Fiction Auto-Generator
毎日17時(JST)に実行され、note投稿用の創作小説を生成する
"""

import os
import sys
import json
import re
from pathlib import Path
from datetime import datetime

import anthropic

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from utils import (
    BASE_DIR, JST, WEEKDAY_NAMES, EPISODE_ROLES,
    get_jst_now, load_prompt, load_json, save_json
)
from story_planner import StoryPlanner
from quality_checker import QualityChecker


def build_weekday_prompt(planner: StoryPlanner, date_str: str, weekday: int) -> str:
    template = load_prompt("weekday_serial_prompt.md")

    current_week = planner.get_current_week()
    protagonist = current_week.get("protagonist", {})
    protagonist_desc = (
        f"{protagonist.get('name', '?')}（{protagonist.get('age', '?')}歳、"
        f"{protagonist.get('occupation', '?')}）。欠落：{protagonist.get('flaw', '?')}"
    )

    used_titles = planner.get_used_titles()
    used_titles_str = "\n".join(f"- {t}" for t in used_titles[-20:]) if used_titles else "なし"

    return template.format(
        date=date_str,
        weekday_name=WEEKDAY_NAMES[weekday],
        episode_role=EPISODE_ROLES[weekday],
        series_title=current_week.get("series_title", ""),
        theme=current_week.get("theme", ""),
        setting=current_week.get("setting", ""),
        protagonist_desc=protagonist_desc,
        central_mystery=current_week.get("central_mystery", ""),
        final_destination=current_week.get("final_destination", ""),
        previous_summaries=planner.format_previous_summaries(weekday),
        unresolved_foreshadowing=planner.format_unresolved_foreshadowing(),
        episode_number=weekday + 1,
        episode_instructions=EPISODE_ROLES[weekday],
        used_titles=used_titles_str,
    )


def build_weekend_prompt(planner: StoryPlanner, date_str: str, weekday: int) -> tuple[str, str]:
    template = load_prompt("weekend_standalone_prompt.md")
    theme = planner.select_weekend_theme()

    used_themes = planner.get_used_themes()
    used_themes_str = "\n".join(f"- {t}" for t in used_themes[-10:]) if used_themes else "なし"

    used_titles = planner.get_used_titles()
    used_titles_str = "\n".join(f"- {t}" for t in used_titles[-20:]) if used_titles else "なし"

    day_type = "土曜日" if weekday == 5 else "日曜日"
    sunday_note = "- 日曜日は少し静かで内省的なトーンにしても良い" if weekday == 6 else ""

    prompt = template.format(
        date=date_str,
        weekday_name=WEEKDAY_NAMES[weekday],
        day_type=day_type,
        theme=theme,
        used_themes=used_themes_str,
        used_titles=used_titles_str,
        sunday_note=sunday_note,
    )
    return prompt, theme


def call_claude(client: anthropic.Anthropic, prompt: str) -> str:
    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=8192,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def extract_title_from_content(content: str) -> str:
    """Extract the recommended title from generated content."""
    # Try YAML frontmatter first
    match = re.search(r"^title:\s*(.+)$", content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    # Try H1 heading
    match = re.search(r"^# (.+)$", content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    return ""


def extract_summary_from_handover(content: str) -> str:
    """Extract today's summary from the handover memo."""
    match = re.search(
        r"(?:今回のあらすじ|あらすじ)[（\(][^）\)]+[）\)]\s*：\s*(.+?)(?=\n-|\n#|\Z)",
        content,
        re.DOTALL,
    )
    if match:
        return match.group(1).strip()[:200]
    return ""


def ensure_output_format(content: str, date_str: str) -> str:
    """Ensure the content starts with YAML frontmatter."""
    if not content.strip().startswith("---"):
        content = f"---\ndate: {date_str}\n---\n\n" + content
    return content


def generate_fiction(
    client: anthropic.Anthropic,
    planner: StoryPlanner,
    checker: QualityChecker,
    date_str: str,
    weekday: int,
    is_weekend: bool,
) -> tuple[str, str, str]:
    """
    Generate fiction with quality check and retry.
    Returns (content, title, theme)
    """
    theme = ""

    for attempt in range(3):
        print(f"Generation attempt {attempt + 1}...")

        if is_weekend:
            prompt, theme = build_weekend_prompt(planner, date_str, weekday)
        else:
            prompt = build_weekday_prompt(planner, date_str, weekday)

        content = call_claude(client, prompt)
        content = ensure_output_format(content, date_str)

        issues = checker.check(content, weekday, is_weekend)

        if not issues:
            print("Quality check passed.")
            break

        print(f"Quality issues found: {issues}")
        if attempt < 2:
            print("Regenerating...")
        else:
            print("Max retries reached. Using last generation with issues noted.")
            # Append quality issues to content
            content += f"\n\n> **自動品質チェック警告**\n"
            for issue in issues:
                content += f"> - {issue}\n"

    title = extract_title_from_content(content)
    return content, title, theme


def main():
    # Setup
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY is not set.")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    now = get_jst_now()
    date_str = now.strftime("%Y-%m-%d")
    weekday = now.weekday()  # 0=Monday, 6=Sunday
    is_weekend = weekday >= 5

    print(f"Date: {date_str} ({WEEKDAY_NAMES[weekday]})")
    print(f"Type: {'Weekend standalone' if is_weekend else 'Weekday serial'}")

    # Initialize components
    planner = StoryPlanner()
    checker = QualityChecker()

    # If Monday, create new weekly plan
    if weekday == 0:
        print("Monday: Creating new weekly plan...")
        planner.create_weekly_plan(client)
        print(f"Weekly plan created: {planner.get_current_week().get('series_title', '')}")

    # Generate fiction
    content, title, theme = generate_fiction(client, planner, checker, date_str, weekday, is_weekend)

    # Save output
    output_dir = BASE_DIR / "output"
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / f"{date_str}_note.md"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Output saved: {output_path}")
    print(f"Title: {title}")

    # Update state
    if is_weekend:
        planner.update_weekend_theme(theme, title)
    else:
        summary = extract_summary_from_handover(content)
        planner.update_episode_summary(weekday, summary, title)

    print("Done.")


if __name__ == "__main__":
    main()
