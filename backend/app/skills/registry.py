from pathlib import Path
from typing import Any

from app.schemas.skills import SkillDocument


AGENT_SKILLS: dict[str, list[str]] = {
    "supervisor": ["memory/context_compaction"],
    "memory_manager": ["memory/long_term_write_policy", "memory/context_compaction"],
    "profile": ["profile/resume_parsing", "profile/evidence_chain"],
    "job": ["job/jd_analysis", "job/agent_developer_role"],
    "match": ["match/match_scoring_rubric", "match/gap_diagnosis"],
    "planning": ["planning/career_path_planning", "planning/three_month_plan"],
    "training": ["training/workplace_task_generation", "training/submission_scoring"],
    "interview": ["interview/mock_interview_flow", "interview/answer_scoring"],
    "report": ["report/markdown_report"],
}


class SkillRegistry:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    @classmethod
    def builtin(cls) -> "SkillRegistry":
        return cls(Path(__file__).parent / "builtin")

    def get(self, skill_id: str) -> SkillDocument:
        path = self._path_for(skill_id)
        raw = path.read_text(encoding="utf-8")
        frontmatter, body = self._split_frontmatter(raw, path)

        document = SkillDocument(**frontmatter, body=body.strip())
        if document.id != skill_id:
            raise ValueError(f"Skill id mismatch in {path}: expected {skill_id}, got {document.id}")
        return document

    def _path_for(self, skill_id: str) -> Path:
        path = self.root / f"{skill_id}.md"
        root = self.root.resolve()
        resolved = path.resolve()
        if root not in resolved.parents:
            raise ValueError(f"Skill id escapes registry root: {skill_id}")
        return resolved

    def _split_frontmatter(self, raw: str, path: Path) -> tuple[dict[str, Any], str]:
        lines = raw.splitlines()
        if not lines or lines[0].strip() != "---":
            raise ValueError(f"Skill file is missing frontmatter: {path}")

        for index, line in enumerate(lines[1:], start=1):
            if line.strip() == "---":
                frontmatter = "\n".join(lines[1:index])
                body = "\n".join(lines[index + 1 :])
                return self._parse_frontmatter(frontmatter), body

        raise ValueError(f"Skill file has unterminated frontmatter: {path}")

    def _parse_frontmatter(self, text: str) -> dict[str, Any]:
        data: dict[str, Any] = {}
        list_key: str | None = None

        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if list_key and stripped.startswith("- "):
                data[list_key].append(stripped[2:].strip())
                continue
            if ":" not in line:
                raise ValueError(f"Invalid frontmatter line: {line}")

            key, raw_value = line.split(":", 1)
            key = key.strip()
            value = raw_value.strip()
            if not value:
                data[key] = []
                list_key = key
                continue

            list_key = None
            data[key] = int(value) if value.isdigit() else value

        return data
