import re

from app.schemas.skills import LoadedSkill, SkillRuntimeRef
from app.skills.registry import AGENT_SKILLS, SkillRegistry


_DEFAULT_SECTION_IDS = ["input", "output"]

_SECTION_IDS_BY_INTENT: dict[str, list[str]] = {
    "build_profile": ["input", "output", "evidence"],
    "analyze_job": ["input", "output", "requirements"],
    "gap_analysis": ["input", "output", "rubric", "gaps"],
    "match": ["input", "output", "rubric", "gaps"],
    "plan": ["input", "output", "milestones"],
    "create_training": ["input", "output", "practice"],
    "submit_training": ["input", "output", "scoring"],
    "start_interview": ["input", "output", "questions"],
    "answer_interview": ["input", "output", "scoring"],
    "export_report": ["input", "output", "report"],
    "clarify": ["input", "output"],
}


class SkillLoader:
    def __init__(
        self,
        registry: SkillRegistry,
        agent_skills: dict[str, list[str]] | None = None,
    ) -> None:
        self.registry = registry
        self.agent_skills = agent_skills or AGENT_SKILLS

    @classmethod
    def builtin(cls) -> "SkillLoader":
        return cls(SkillRegistry.builtin())

    def resolve_for_agent(self, agent_id: str, intent: str, budget: int) -> list[LoadedSkill]:
        remaining_budget = budget
        loaded: list[LoadedSkill] = []
        for skill_id in self.agent_skills.get(agent_id, []):
            document = self.registry.get(skill_id)
            if remaining_budget <= 0:
                detail_level = "skipped"
                content = ""
            elif document.token_budget <= remaining_budget:
                detail_level = "full"
                content = document.body
                remaining_budget -= document.token_budget
            else:
                detail_level = "summary"
                content = document.summary

            loaded.append(
                LoadedSkill(
                    ref=f"{document.id}@v{document.version}",
                    summary=document.summary,
                    content=content,
                    runtime_ref=SkillRuntimeRef(
                        skill_id=document.id,
                        version=str(document.version),
                        section_ids=_section_ids_for_intent(intent),
                        detail_level=detail_level,
                        summary_digest=_summary_digest(document.summary),
                    ),
                )
            )

        return loaded


def _section_ids_for_intent(intent: str) -> list[str]:
    return list(_SECTION_IDS_BY_INTENT.get(intent, _DEFAULT_SECTION_IDS))


def _summary_digest(summary: str) -> str:
    digest = re.sub(r"#+\s*", "", summary)
    digest = re.sub(r"\s+", " ", digest).strip()
    return digest[:240]
