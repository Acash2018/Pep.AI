import json
import logging
import os
from dataclasses import dataclass
from enum import Enum
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

from dotenv import load_dotenv

from app.services.prompts import (
    COMPARISON_AGENT_LLM_PROMPT,
    REPORT_WRITER_LLM_PROMPT,
    SCOUT_AGENT_LLM_PROMPT,
    TACTICAL_FIT_LLM_PROMPT,
)

load_dotenv()

OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434').rstrip('/')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3.1')
OLLAMA_TIMEOUT_SECONDS = float(os.getenv('OLLAMA_TIMEOUT_SECONDS', '8'))
logger = logging.getLogger(__name__)


class OllamaFailureKind(str, Enum):
    UNAVAILABLE = 'unavailable'
    INVALID_JSON = 'invalid_json'
    EMPTY_RESPONSE = 'empty_response'
    REQUEST_ERROR = 'request_error'


@dataclass
class OllamaCompletionResult:
    content: str | None
    failure_kind: OllamaFailureKind | None = None
    detail: str = ''


class OllamaService:
    @property
    def enabled(self) -> bool:
        return self.health_status()['available']

    def health_status(self) -> dict[str, Any]:
        try:
            request = Request(f'{OLLAMA_BASE_URL}/api/tags', method='GET')
            with urlopen(request, timeout=2) as response:
                data = json.loads(response.read().decode('utf-8'))
                models = [
                    model.get('name', '')
                    for model in data.get('models', [])
                    if isinstance(model, dict)
                ]
                return {
                    'available': True,
                    'base_url': OLLAMA_BASE_URL,
                    'model': OLLAMA_MODEL,
                    'models': models,
                    'model_loaded': any(name.split(':')[0] == OLLAMA_MODEL.split(':')[0] for name in models),
                }
        except (OSError, URLError, json.JSONDecodeError) as exc:
            return {
                'available': False,
                'base_url': OLLAMA_BASE_URL,
                'model': OLLAMA_MODEL,
                'models': [],
                'model_loaded': False,
                'error': str(exc),
            }

    @property
    def model_name(self) -> str:
        return f'ollama:{OLLAMA_MODEL}' if self.enabled else 'deterministic-fallback'

    def generate_scout_reasoning(self, context: dict[str, Any]) -> dict[str, Any]:
        fallback = _fallback_scout_reasoning(context)
        return self._json_completion(SCOUT_AGENT_LLM_PROMPT, context, fallback)

    def generate_tactical_reasoning(self, context: dict[str, Any]) -> dict[str, Any]:
        fallback = _fallback_tactical_reasoning(context)
        return self._json_completion(TACTICAL_FIT_LLM_PROMPT, context, fallback)

    def generate_comparison_analysis(self, context: dict[str, Any]) -> dict[str, Any]:
        fallback = _fallback_comparison_analysis(context)
        return self._json_completion(COMPARISON_AGENT_LLM_PROMPT, context, fallback)

    def generate_final_report(self, context: dict[str, Any]) -> str:
        fallback = _fallback_final_report(context)
        response = self._chat_completion(REPORT_WRITER_LLM_PROMPT, context, json_output=False)
        if not response.content:
            _log_fallback('final_report', response)
            return fallback
        return response.content

    def _json_completion(self, system_prompt: str, context: dict[str, Any], fallback: dict[str, Any]) -> dict[str, Any]:
        response = self._chat_completion(
            system_prompt + '\nReturn strict JSON only. Do not wrap in markdown.',
            context,
            json_output=True,
        )
        if not response.content:
            _log_fallback('json_completion', response)
            return fallback

        try:
            return json.loads(response.content)
        except json.JSONDecodeError as exc:
            _log_fallback(
                'json_completion',
                OllamaCompletionResult(
                    content=response.content,
                    failure_kind=OllamaFailureKind.INVALID_JSON,
                    detail=str(exc),
                ),
            )
            return fallback

    def _chat_completion(self, system_prompt: str, context: dict[str, Any], json_output: bool) -> OllamaCompletionResult:
        payload: dict[str, Any] = {
            'model': OLLAMA_MODEL,
            'stream': False,
            'messages': [
                {'role': 'system', 'content': system_prompt.strip()},
                {'role': 'user', 'content': _compact_json(context)},
            ],
            'options': {
                'temperature': 0.2,
                'num_predict': 256,
            },
        }
        if json_output:
            payload['format'] = 'json'

        try:
            request = Request(
                f'{OLLAMA_BASE_URL}/api/chat',
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'},
                method='POST',
            )
            with urlopen(request, timeout=OLLAMA_TIMEOUT_SECONDS) as response:
                data = json.loads(response.read().decode('utf-8'))
                content = data.get('message', {}).get('content')
                if not content:
                    return OllamaCompletionResult(
                        content=None,
                        failure_kind=OllamaFailureKind.EMPTY_RESPONSE,
                        detail='Ollama returned no message content.',
                    )
                return OllamaCompletionResult(content=content)
        except json.JSONDecodeError as exc:
            return OllamaCompletionResult(
                content=None,
                failure_kind=OllamaFailureKind.INVALID_JSON,
                detail=str(exc),
            )
        except (OSError, URLError) as exc:
            return OllamaCompletionResult(
                content=None,
                failure_kind=OllamaFailureKind.UNAVAILABLE,
                detail=str(exc),
            )


def _log_fallback(operation: str, result: OllamaCompletionResult) -> None:
    if result.failure_kind:
        logger.warning(
            'Ollama fallback used for %s: %s (%s)',
            operation,
            result.failure_kind.value,
            result.detail,
        )


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


ollama_service = OllamaService()
