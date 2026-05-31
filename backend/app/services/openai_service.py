import json
import os
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

from app.services.prompts import (
    COMPARISON_AGENT_GPT_PROMPT,
    REPORT_WRITER_GPT_PROMPT,
    SCOUT_AGENT_GPT_PROMPT,
    TACTICAL_FIT_GPT_PROMPT,
)

load_dotenv()

OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4.1')


class OpenAIService:
    def __init__(self):
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key and api_key != 'your-openai-api-key':
            self.client = OpenAI(api_key=api_key)
        else:
            self.client = None

    @property
    def enabled(self) -> bool:
        return self.client is not None

    def generate_scout_reasoning(self, context: dict[str, Any]) -> dict[str, Any]:
        fallback = _fallback_scout_reasoning(context)
        return self._json_completion(SCOUT_AGENT_GPT_PROMPT, context, fallback)

    def generate_tactical_reasoning(self, context: dict[str, Any]) -> dict[str, Any]:
        fallback = _fallback_tactical_reasoning(context)
        return self._json_completion(TACTICAL_FIT_GPT_PROMPT, context, fallback)

    def generate_comparison_analysis(self, context: dict[str, Any]) -> dict[str, Any]:
        fallback = _fallback_comparison_analysis(context)
        return self._json_completion(COMPARISON_AGENT_GPT_PROMPT, context, fallback)

    def generate_final_report(self, context: dict[str, Any]) -> str:
        fallback = _fallback_final_report(context)
        if not self.client:
            return fallback

        try:
            response = self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {'role': 'system', 'content': REPORT_WRITER_GPT_PROMPT.strip()},
                    {'role': 'user', 'content': _compact_json(context)},
                ],
                temperature=0.25,
            )
            return response.choices[0].message.content or fallback
        except Exception:
            return fallback

    def _json_completion(self, system_prompt: str, context: dict[str, Any], fallback: dict[str, Any]) -> dict[str, Any]:
        if not self.client:
            return fallback

        try:
            response = self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {
                        'role': 'system',
                        'content': (
                            system_prompt.strip()
                            + '\nReturn strict JSON only. Do not wrap in markdown.'
                        ),
                    },
                    {'role': 'user', 'content': _compact_json(context)},
                ],
                temperature=0.2,
            )
            content = response.choices[0].message.content or ''
            return json.loads(content)
        except Exception:
            return fallback


def _compact_json(context: dict[str, Any]) -> str:
    return json.dumps(context, ensure_ascii=False, default=str)


def _fallback_scout_reasoning(context: dict[str, Any]) -> dict[str, Any]:
    player = context['player']
    stats = player.get('stats', {})
    return {
        'strengths': [
            f"{strength} is a visible profile strength."
            for strength in player.get('strengths', [])[:4]
        ],
        'weaknesses': [
            f"{weakness} remains a recruitment watchpoint."
            for weakness in player.get('weaknesses', [])[:4]
        ],
        'development_areas': [
            f"Improve role execution around {player.get('tactical_archetype', 'current tactical profile')}.",
            f"Use {stats.get('passAccuracy', 0)}% pass accuracy and output trends as monitoring anchors.",
        ],
        'model': 'deterministic-fallback',
    }


def _fallback_tactical_reasoning(context: dict[str, Any]) -> dict[str, Any]:
    tactical_fit = context['tactical_fit']
    return {
        'tactical_suitability': tactical_fit.get('why_fit', []),
        'tactical_risks': tactical_fit.get('why_not', []),
        'formation_fit': [
            f"Formation suitability: {', '.join(context['player'].get('suitable_formations', [])) or 'general structure'}."
        ],
        'model': 'deterministic-fallback',
    }


def _fallback_comparison_analysis(context: dict[str, Any]) -> dict[str, Any]:
    candidates = context.get('comparison_candidates', [])
    return {
        'similarities': [
            f"{candidate.get('name')} overlaps through {', '.join(candidate.get('similarityReasons', []))}."
            for candidate in candidates[:3]
        ],
        'differences': [
            f"{candidate.get('name')} differs by position, risk, or tactical usage in the comparison matrix."
            for candidate in candidates[:3]
        ],
        'recruitment_meaning': 'Use comparable players to calibrate role fit, tactical risk, and market alternatives.',
        'model': 'deterministic-fallback',
    }


def _fallback_final_report(context: dict[str, Any]) -> str:
    player = context['player']
    tactical_fit = context['tactical_fit']
    report = context['deterministic_report']
    return f"""## Executive Summary
{report.get('summary', '')}

## Strengths
{_bullet_list(context.get('strengths', []))}

## Weaknesses
{_bullet_list(context.get('weaknesses', []))}

## Tactical Fit
{tactical_fit.get('notes', '')}

## Recruitment Risks
{_bullet_list(tactical_fit.get('why_not', []))}

## Comparable Players
{_bullet_list([candidate.get('name', '') for candidate in context.get('comparison_candidates', [])[:3]])}

## Final Recommendation
{player.get('name')} is graded as {tactical_fit.get('fit_score')}/100 for {tactical_fit.get('system')}. Recommendation: {report.get('recommendation', 'Monitor')}."""


def _bullet_list(items: list[Any]) -> str:
    return '\n'.join(f"- {item}" for item in items) if items else '- No major item returned.'


openai_service = OpenAIService()
