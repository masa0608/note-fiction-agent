import re
from dataclasses import dataclass, field


@dataclass
class CheckResult:
    passed: bool
    issues: list[str] = field(default_factory=list)
    char_count: int = 0


class QualityChecker:
    SAFETY_PATTERNS = [
        r"株式会社[^\s「」]{2,10}",
        r"[A-Z][a-z]+\s+[A-Z][a-z]+\s+(?:Co\.|Inc\.|Ltd\.)",
    ]

    FORBIDDEN_WORDS = [
        "殺す方法", "自殺", "自傷", "死に方", "爆弾の作り方",
    ]

    def check(self, content: str, weekday: int, is_weekend: bool) -> list[str]:
        issues = []

        # Extract body text
        body = self._extract_body(content)
        char_count = len(body)

        # Check character count
        if is_weekend:
            if char_count < 3000:
                issues.append(f"本文が短すぎます（{char_count}字）。土日は4,000〜6,000字が目安です。")
        else:
            if char_count < 1500:
                issues.append(f"本文が短すぎます（{char_count}字）。平日は2,000〜3,500字が目安です。")

        # Check title candidates
        title_section = self._extract_section(content, "タイトル案")
        if title_section:
            title_count = len(re.findall(r"^\d+\.", title_section, re.MULTILINE))
            if title_count < 5:
                issues.append(f"タイトル案が{title_count}個しかありません。5個必要です。")

        # Check hashtags
        hashtag_section = self._extract_section(content, "ハッシュタグ")
        if hashtag_section:
            hashtags = re.findall(r"#\S+", hashtag_section)
            if len(hashtags) < 5:
                issues.append(f"ハッシュタグが{len(hashtags)}個しかありません。5〜8個必要です。")
            elif len(hashtags) > 8:
                issues.append(f"ハッシュタグが{len(hashtags)}個あります。5〜8個に絞ってください。")

        # Check posting memo
        memo_section = self._extract_section(content, "投稿文メモ")
        if memo_section:
            memo_count = len(re.findall(r"^\d+\.", memo_section, re.MULTILINE))
            if memo_count < 3:
                issues.append(f"投稿文メモが{memo_count}案しかありません。3案必要です。")

        # Check safety
        for pattern in self.SAFETY_PATTERNS:
            if re.search(pattern, content):
                issues.append("実在する会社名・個人名が含まれている可能性があります。確認してください。")
                break

        for word in self.FORBIDDEN_WORDS:
            if word in content:
                issues.append(f"不適切なワードが含まれています：{word}")

        # Check weekday-specific requirements
        if not is_weekend:
            # Monday-Thursday should have a cliffhanger
            if weekday in [0, 1, 2, 3]:
                carry_over = self._extract_section(content, "明日への引き継ぎメモ")
                if carry_over and "完結済み" in carry_over:
                    issues.append("平日（月〜木）なのに「完結済み」となっています。")

            # Friday should be concluded
            if weekday == 4:
                carry_over = self._extract_section(content, "明日への引き継ぎメモ")
                if carry_over and "完結済み" not in carry_over and "未回収" in carry_over:
                    issues.append("金曜日なのに伏線が未回収です。完結させてください。")

        return issues

    def _extract_body(self, content: str) -> str:
        """Extract the main body text (## 本文 section)."""
        match = re.search(r"## 本文\n+(.*?)(?=\n## |\Z)", content, re.DOTALL)
        if match:
            return match.group(1).strip()
        return content

    def _extract_section(self, content: str, section_name: str) -> str:
        """Extract a specific section."""
        pattern = rf"## {section_name}\n+(.*?)(?=\n## |\Z)"
        match = re.search(pattern, content, re.DOTALL)
        if match:
            return match.group(1).strip()
        return ""
