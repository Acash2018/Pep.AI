from langgraph.graph import END, StateGraph

from app.data.player_repository import retrieve_player_data
from app.services.prompts import (
    REPORT_WRITER_AGENT_PROMPT,
    STATS_AGENT_PROMPT,
    TACTICAL_FIT_AGENT_PROMPT,
)
from app.services.knowledge_base import knowledge_base_service
from app.services.player_comparison import PlayerComparisonEngine
from app.services.role_matching import RoleMatchingService
from app.services.state import ScoutState
from app.services.tactical_scoring import TacticalFitScoringService

role_matching_service = RoleMatchingService()
tactical_scoring_service = TacticalFitScoringService()
player_comparison_engine = PlayerComparisonEngine()


def _format_stat_notes(player: dict) -> list[str]:
    stats = player['stats']
    notes = [
        f"{stats['goals']} goals and {stats['assists']} assists show direct attacking output.",
        f"{stats['passAccuracy']}% pass accuracy supports possession reliability.",
    ]

    if stats['assists'] >= 8:
        notes.append('Chance creation profile is above the mock pool baseline.')
    if stats['passAccuracy'] < 85:
        notes.append('Ball security may dip under aggressive pressure.')

    return notes


def load_player_node(state: ScoutState) -> ScoutState:
    player = retrieve_player_data(state['player_id'])
    if not player:
        raise ValueError('Player not found')

    return {
        **state,
        'player': player,
        'similar_players': player_comparison_engine.find_similar_players(player),
        'transfer_value': player['estimatedValue'],
    }


def stats_agent_node(state: ScoutState) -> ScoutState:
    player = state['player']
    stats = player['stats']

    strengths = list(player['strengths'])
    weaknesses = list(player['weaknesses'])

    if stats['assists'] >= 10 and 'chance creation' not in strengths:
        strengths.append('chance creation')
    if stats['passAccuracy'] >= 87 and 'ball retention' not in strengths:
        strengths.append('ball retention')
    if stats['goals'] < 5 and 'limited goal threat' not in weaknesses:
        weaknesses.append('limited goal threat')

    return {
        **state,
        'stats_analysis': {
            'agent': 'Stats Agent',
            'prompt': STATS_AGENT_PROMPT.strip(),
            'goals': stats['goals'],
            'assists': stats['assists'],
            'pass_accuracy': stats['passAccuracy'],
            'strengths': strengths,
            'weaknesses': weaknesses,
            'notes': _format_stat_notes(player),
        },
    }


def tactical_fit_agent_node(state: ScoutState) -> ScoutState:
    player = state['player']
    requested_system = state['preferred_system']
    player_style = player['tacticalStyle']
    role_match = role_matching_service.match_role(player)
    tactical_context = knowledge_base_service.retrieve_tactical_system_context(requested_system)
    role_context = knowledge_base_service.retrieve_role_context(role_match['primary_role']['role_id'], player)
    general_context = knowledge_base_service.retrieve_for_tactical_fit(player, requested_system, limit=2)
    retrieved_knowledge = _dedupe_knowledge(tactical_context + role_context + general_context)
    tactical_score = tactical_scoring_service.score_fit(player, requested_system, role_match, retrieved_knowledge)

    system_words = set(requested_system.lower().replace('&', ' ').replace('-', ' ').split())
    style_words = set(player_style.lower().replace('&', ' ').replace('-', ' ').split())
    overlap = len(system_words.intersection(style_words))
    fit_score = tactical_score['score']
    knowledge_note = _format_knowledge_note(retrieved_knowledge)

    notes = (
        f"{player['name']} projects as a {fit_score}/100 {tactical_score['grade']} for {requested_system}. "
        f"Primary role projection: {role_match['primary_role']['label']}. "
        f"System compatibility is driven by {_format_compatibility_drivers(player, tactical_score, role_match)}, "
        f"with {', '.join(tactical_score['system_compatibility']['risk_factors']) or 'no major system-specific red flags'} as the main risk area. "
        f"{knowledge_note}"
    )

    return {
        **state,
        'role_match': role_match,
        'tactical_score': tactical_score,
        'retrieved_knowledge': retrieved_knowledge,
        'tactical_fit': {
            'agent': 'Tactical Fit Agent',
            'prompt': TACTICAL_FIT_AGENT_PROMPT.strip(),
            'system': requested_system,
            'identified_system': tactical_score['system'],
            'current_style': player_style,
            'fit_score': fit_score,
            'fit_score_100': fit_score,
            'fit_grade': tactical_score['grade'],
            'notes': notes,
            'role_projection': f"{player['position']} for {state.get('buying_club') or 'the target club'}",
            'role_match': role_match,
            'role_suitability': role_match,
            'system_compatibility': tactical_score['system_compatibility'],
            'tactical_strengths': tactical_score['tactical_strengths'],
            'tactical_weaknesses': tactical_score['tactical_weaknesses'],
            'why_fit': tactical_score['why_fit'],
            'why_not': tactical_score['why_not'],
            'retrieved_knowledge': retrieved_knowledge,
            'style_overlap_score': overlap,
        },
    }


def report_writer_agent_node(state: ScoutState) -> ScoutState:
    player = state['player']
    stats = state['stats_analysis']
    tactical_fit = state['tactical_fit']
    tactical_score = state['tactical_score']
    role_match = state['role_match']

    recommendation = 'Monitor'
    if tactical_fit['fit_score'] >= 80:
        recommendation = 'Strong candidate'
    elif tactical_fit['fit_score'] <= 55:
        recommendation = 'Only pursue at reduced fee'

    summary = (
        f"{player['name']} is a {player['age']}-year-old {player['position']} at {player['club']} "
        f"with a {tactical_fit['fit_score']}/100 fit for {tactical_fit['system']} "
        f"(closest archetype: {tactical_fit['identified_system']}). "
        f"The strongest recruitment case is {', '.join(tactical_score['why_fit'])}"
    )

    return {
        **state,
        'report': {
            'agent': 'Report Writer Agent',
            'prompt': REPORT_WRITER_AGENT_PROMPT.strip(),
            'summary': summary,
            'recommendation': recommendation,
            'tactical_reasoning': {
                'why_fit': tactical_score['why_fit'],
                'why_not': tactical_score['why_not'],
                'tactical_strengths': tactical_score['tactical_strengths'],
                'tactical_weaknesses': tactical_score['tactical_weaknesses'],
            },
            'role_suitability': role_match,
            'system_compatibility': tactical_score['system_compatibility'],
            'strengths': stats['strengths'],
            'weaknesses': stats['weaknesses'],
            'transfer_value': state['transfer_value'],
            'similar_players': state['similar_players'],
            'retrieved_knowledge': state.get('retrieved_knowledge', []),
        },
    }


def _format_knowledge_note(retrieved_knowledge: list[dict]) -> str:
    if not retrieved_knowledge:
        return 'No indexed knowledge-base context was available, so the fit is based on player data only.'

    takeaways = _knowledge_takeaways(retrieved_knowledge)
    return f"Retrieved football intelligence emphasizes {', '.join(takeaways)}."


def _format_compatibility_drivers(player: dict, tactical_score: dict, role_match: dict) -> str:
    matched_principles = tactical_score['system_compatibility']['matched_principles']
    if matched_principles:
        return ', '.join(matched_principles)

    evidence = []
    stats = player['stats']
    if stats['passAccuracy'] >= 86:
        evidence.append(f"{stats['passAccuracy']}% pass accuracy")
    if stats['assists'] >= 5:
        evidence.append(f"{stats['assists']} assists")
    if stats['goals'] >= 5:
        evidence.append(f"{stats['goals']} goals")
    if role_match['primary_role']['matched_traits']:
        evidence.append(f"{role_match['primary_role']['label']} traits")
    if player['tacticalStyle']:
        evidence.append(f"experience in {player['tacticalStyle'].lower()}")

    return ', '.join(evidence[:4]) or 'available statistical and role evidence'


def _knowledge_takeaways(retrieved_knowledge: list[dict]) -> list[str]:
    takeaways = []
    combined_text = ' '.join(item.get('text', '').lower() for item in retrieved_knowledge[:4])

    if 'counter-pressure' in combined_text or 'counter press' in combined_text or 'counter-press' in combined_text:
        takeaways.append('immediate counter-pressing after turnovers')
    if 'compact' in combined_text or 'spacing' in combined_text:
        takeaways.append('compact team spacing')
    if 'ball retention' in combined_text or 'technical security' in combined_text:
        takeaways.append('secure possession under pressure')
    if 'wide' in combined_text or 'overlap' in combined_text:
        takeaways.append('wide support and overlapping timing')
    if 'vertical' in combined_text or 'forward passing' in combined_text:
        takeaways.append('quick vertical progression')
    if 'defensive discipline' in combined_text or 'concentration' in combined_text:
        takeaways.append('defensive concentration')

    return takeaways[:3] or ['system principles from the indexed tactical and role documents']


def _dedupe_knowledge(items: list[dict]) -> list[dict]:
    seen = set()
    unique = []
    for item in items:
        item_id = item.get('id')
        if item_id in seen:
            continue
        seen.add(item_id)
        unique.append(item)
    return unique


def build_scouting_graph():
    graph = StateGraph(ScoutState)
    graph.add_node('load_player', load_player_node)
    graph.add_node('stats_agent', stats_agent_node)
    graph.add_node('tactical_fit_agent', tactical_fit_agent_node)
    graph.add_node('report_writer_agent', report_writer_agent_node)

    graph.set_entry_point('load_player')
    graph.add_edge('load_player', 'stats_agent')
    graph.add_edge('stats_agent', 'tactical_fit_agent')
    graph.add_edge('tactical_fit_agent', 'report_writer_agent')
    graph.add_edge('report_writer_agent', END)

    return graph.compile()


scouting_graph = build_scouting_graph()
