import random
from datetime import datetime
from pathlib import Path
from typing import Optional
import anthropic
import os

from utils import (
    BASE_DIR, JST, WEEKDAY_THEMES, WEEKEND_THEMES,
    load_json, save_json, get_jst_now
)

STATE_PATH = BASE_DIR / "data" / "story_state.json"
PLAN_PATH = BASE_DIR / "data" / "weekly_plan.json"
USED_TITLES_PATH = BASE_DIR / "data" / "used_titles.json"
USED_THEMES_PATH = BASE_DIR / "data" / "used_themes.json"


class StoryPlanner:
    def __init__(self):
        self.state = load_json(STATE_PATH)
        self.used_titles_data = load_json(USED_TITLES_PATH)
        self.used_themes_data = load_json(USED_THEMES_PATH)

        if not self.state:
            self.state = {
                "current_week": {
                    "series_title": "",
                    "theme": "",
                    "protagonist": {},
                    "setting": "",
                    "characters": [],
                    "central_mystery": "",
                    "foreshadowing": [],
                    "resolved_foreshadowing": [],
                    "episode_summaries": {},
                    "final_destination": "",
                    "week_start": "",
                    "status": "completed",
                },
                "past_series": [],
            }

        if not self.used_titles_data:
            self.used_titles_data = {"titles": [], "last_updated": ""}
        if not self.used_themes_data:
            self.used_themes_data = {"themes": [], "last_updated": ""}

    def get_used_titles(self) -> list[str]:
        return self.used_titles_data.get("titles", [])

    def get_used_themes(self) -> list[str]:
        return self.used_themes_data.get("themes", [])

    def select_weekday_theme(self) -> str:
        used = self.get_used_themes()
        available = [t for t in WEEKDAY_THEMES if t not in used]
        if not available:
            available = WEEKDAY_THEMES
            self.used_themes_data["themes"] = []
        return random.choice(available)

    def select_weekend_theme(self) -> str:
        used = self.get_used_themes()
        available = [t for t in WEEKEND_THEMES if t not in used]
        if not available:
            available = WEEKEND_THEMES
        return random.choice(available)

    def create_weekly_plan(self, client: anthropic.Anthropic) -> dict:
        theme = self.select_weekday_theme()
        today = get_jst_now().strftime("%Y-%m-%d")

        prompt = f"""今週の連載小説の企画を作成してください。

テーマ：{theme}

以下をJSON形式で出力してください（他のテキストは一切出力しない）：

{{
  "series_title": "連載タイトル（魅力的なもの）",
  "theme": "{theme}",
  "protagonist": {{
    "name": "主人公の名前",
    "age": "年齢",
    "occupation": "職業",
    "flaw": "主人公の欠落や弱さ"
  }},
  "setting": "物語の舞台（時代・場所）",
  "central_mystery": "物語の中心となる謎",
  "foreshadowing": ["伏線1", "伏線2", "伏線3"],
  "weekly_arc": {{
    "monday": "第1話のポイント（1〜2行）",
    "tuesday": "第2話のポイント（1〜2行）",
    "wednesday": "第3話のポイント（1〜2行）",
    "thursday": "第4話のポイント（1〜2行）",
    "friday": "第5話（最終話）のポイントと着地点（2〜3行）"
  }},
  "final_destination": "物語の最終的な着地点と伝えたいメッセージ"
}}"""

        message = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )

        import json
        text = message.content[0].text.strip()
        # Extract JSON from response
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        plan = json.loads(text.strip())
        plan["planned_at"] = today

        # Save plan
        save_json(PLAN_PATH, plan)

        # Update state
        self.state["current_week"] = {
            "series_title": plan["series_title"],
            "theme": plan["theme"],
            "protagonist": plan["protagonist"],
            "setting": plan["setting"],
            "characters": [],
            "central_mystery": plan["central_mystery"],
            "foreshadowing": plan.get("foreshadowing", []),
            "resolved_foreshadowing": [],
            "episode_summaries": {},
            "final_destination": plan["final_destination"],
            "week_start": today,
            "status": "ongoing",
        }
        save_json(STATE_PATH, self.state)

        # Track used theme
        if plan["theme"] not in self.used_themes_data["themes"]:
            self.used_themes_data["themes"].append(plan["theme"])
            self.used_themes_data["last_updated"] = today
            save_json(USED_THEMES_PATH, self.used_themes_data)

        return plan

    def get_current_week(self) -> dict:
        return self.state.get("current_week", {})

    def update_episode_summary(self, weekday: int, summary: str, title: str) -> None:
        day_names = {0: "monday", 1: "tuesday", 2: "wednesday", 3: "thursday", 4: "friday"}
        day_key = day_names.get(weekday, "")
        if day_key:
            self.state["current_week"]["episode_summaries"][day_key] = summary

        # Track used title
        if title and title not in self.used_titles_data["titles"]:
            self.used_titles_data["titles"].append(title)
            self.used_titles_data["last_updated"] = get_jst_now().strftime("%Y-%m-%d")
            save_json(USED_TITLES_PATH, self.used_titles_data)

        # If Friday, mark as completed
        if weekday == 4:
            self.state["current_week"]["status"] = "completed"
            # Archive to past_series
            self.state["past_series"].append({
                "series_title": self.state["current_week"]["series_title"],
                "theme": self.state["current_week"]["theme"],
                "week_start": self.state["current_week"]["week_start"],
                "status": "completed",
            })
            # Keep only last 10
            self.state["past_series"] = self.state["past_series"][-10:]

        save_json(STATE_PATH, self.state)

    def update_weekend_theme(self, theme: str, title: str) -> None:
        today = get_jst_now().strftime("%Y-%m-%d")
        if theme not in self.used_themes_data["themes"]:
            self.used_themes_data["themes"].append(theme)
            self.used_themes_data["last_updated"] = today
            save_json(USED_THEMES_PATH, self.used_themes_data)

        if title and title not in self.used_titles_data["titles"]:
            self.used_titles_data["titles"].append(title)
            self.used_titles_data["last_updated"] = today
            save_json(USED_TITLES_PATH, self.used_titles_data)

    def format_previous_summaries(self, weekday: int) -> str:
        summaries = self.state["current_week"].get("episode_summaries", {})
        day_names = ["monday", "tuesday", "wednesday", "thursday", "friday"]
        result = []
        for i in range(weekday):
            day = day_names[i]
            if day in summaries:
                result.append(f"第{i+1}話（{['月', '火', '水', '木', '金'][i]}曜）：{summaries[day]}")
        return "\n".join(result) if result else "なし（第1話）"

    def format_unresolved_foreshadowing(self) -> str:
        foreshadowing = self.state["current_week"].get("foreshadowing", [])
        resolved = self.state["current_week"].get("resolved_foreshadowing", [])
        unresolved = [f for f in foreshadowing if f not in resolved]
        return "\n".join(f"- {f}" for f in unresolved) if unresolved else "なし"
