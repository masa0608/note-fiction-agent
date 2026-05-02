import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path

JST = timezone(timedelta(hours=9))

BASE_DIR = Path(__file__).parent.parent


def get_jst_now() -> datetime:
    return datetime.now(JST)


def get_base_dir() -> Path:
    return BASE_DIR


def load_json(path: str | Path) -> dict:
    p = Path(path) if isinstance(path, str) else path
    if not p.exists():
        return {}
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: str | Path, data: dict) -> None:
    p = Path(path) if isinstance(path, str) else path
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_prompt(filename: str) -> str:
    prompt_path = BASE_DIR / "prompts" / filename
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()


def load_config(filename: str) -> str:
    config_path = BASE_DIR / "config" / filename
    with open(config_path, "r", encoding="utf-8") as f:
        return f.read()


WEEKDAY_THEMES = [
    "仕事帰りの不思議な出会い",
    "未来から届く手紙",
    "人生をやり直せる駅",
    "記憶を預けられる喫茶店",
    "死ぬ前に一度だけ届く通知",
    "AIが書いたはずの小説が現実になる話",
    "夢でだけ会える人",
    "失くした感情を取り戻す物語",
    "5日間だけ他人の人生を生きる話",
    "通勤電車で毎日同じ時間に現れる謎の人物",
    "会社を辞める前日に起きた小さな奇跡",
    "自分の未来が少しだけ見えるアプリ",
    "誰にも読まれなかった日記が誰かを救う話",
]

WEEKEND_THEMES = [
    "少し泣けるヒューマンドラマ",
    "恋愛未満の余韻が残る話",
    "近未来SF",
    "都市伝説風ミステリー",
    "人生の選択を描く物語",
    "大人向けの静かなファンタジー",
    "読後に解釈が分かれる話",
    "最後の一文で意味が変わる話",
]

WEEKDAY_NAMES = {0: "月曜日", 1: "火曜日", 2: "水曜日", 3: "木曜日", 4: "金曜日", 5: "土曜日", 6: "日曜日"}

EPISODE_ROLES = {
    0: "第1話（月曜）：世界観と主人公を提示し、小さな謎を出す。最後に「明日も読みたい」と思わせる引きを作る。",
    1: "第2話（火曜）：謎を少し深め、主人公の悩みや欠落を見せる。新しい事実を1つ出す。引きを作る。",
    2: "第3話（水曜）：転換点。読者が「そういうことだったのか」と思う情報を出す。ただし真相はまだ明かし切らない。",
    3: "第4話（木曜）：感情が一番動く回。主人公が選択を迫られる。金曜の最終回を読みたくなる強い引きにする。",
    4: "第5話（金曜）：物語を完結させる。伏線を回収する。余韻を残す。切ない希望の結末も可。",
}
