from app.schemas.skills import LoadedSkill
from app.skills.registry import AGENT_SKILLS, SkillRegistry


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
        del intent

        remaining_budget = budget
        loaded: list[LoadedSkill] = []
        for skill_id in self.agent_skills.get(agent_id, []):
            document = self.registry.get(skill_id)
            include_body = document.token_budget <= remaining_budget
            content = document.body if include_body else document.summary
            if include_body:
                remaining_budget -= document.token_budget

            loaded.append(
                LoadedSkill(
                    ref=f"{document.id}@v{document.version}",
                    summary=document.summary,
                    content=content,
                )
            )

        return loaded
