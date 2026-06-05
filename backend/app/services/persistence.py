import hashlib
import json
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.db.models import (
    Comparison,
    KnowledgeSource,
    Player,
    PlayerSearchHistory,
    ScoutingReport,
    TacticalProfile,
)
from app.services.intelligence_metrics import (
    consistency_score,
    development_trajectory_notes,
    risk_profile_score,
    scouting_confidence_score,
)

CACHE_VERSION = 'football-intelligence-v5-ollama'


class PlayerPersistenceService:
    def __init__(self, db: Session):
        self.db = db

    def upsert_player(self, player_data: dict[str, Any]) -> Player:
        player = self.db.scalar(select(Player).where(Player.external_id == player_data['id']))
        if not player:
            player = Player(external_id=player_data['id'])
            self.db.add(player)

        player.name = player_data.get('name', '')
        player.position = player_data.get('position', '')
        player.club = player_data.get('club', '')
        player.nationality = player_data.get('nationality', '')
        player.age = player_data.get('age')
        player.estimated_value = player_data.get('estimatedValue', '')
        player.source = player_data.get('source', 'Pep.AI')
        player.raw_profile = player_data
        self.db.flush()
        return player

    def get_analyzed_players(self, limit: int = 50) -> list[Player]:
        return list(
            self.db.scalars(
                select(Player)
                .join(ScoutingReport)
                .order_by(desc(ScoutingReport.created_at))
                .limit(limit)
            ).unique()
        )

    def timeline(self, external_id: str) -> dict[str, Any] | None:
        player = self.db.scalar(select(Player).where(Player.external_id == external_id))
        if not player:
            return None

        reports = self.db.scalars(
            select(ScoutingReport)
            .where(ScoutingReport.player_id == player.id)
            .order_by(desc(ScoutingReport.created_at))
        ).all()
        tactical_profiles = self.db.scalars(
            select(TacticalProfile)
            .where(TacticalProfile.player_id == player.id)
            .order_by(desc(TacticalProfile.created_at))
        ).all()

        return {
            'player': serialize_player(player),
            'reports': [serialize_report(report) for report in reports],
            'tactical_profiles': [serialize_tactical_profile(profile) for profile in tactical_profiles],
        }


class ScoutingReportPersistenceService:
    def __init__(self, db: Session):
        self.db = db

    def cache_key(self, player_id: str, club: str, preferred_system: str) -> str:
        raw = json.dumps(
            {
                'version': CACHE_VERSION,
                'player_id': player_id,
                'club': club,
                'preferred_system': preferred_system,
            },
            sort_keys=True,
        )
        return hashlib.sha256(raw.encode('utf-8')).hexdigest()

    def get_cached_report(self, player_id: str, club: str, preferred_system: str) -> dict[str, Any] | None:
        key = self.cache_key(player_id, club, preferred_system)
        report = self.db.scalar(select(ScoutingReport).where(ScoutingReport.cache_key == key))
        if not report:
            return None
        payload = dict(report.report_payload)
        payload['cached'] = True
        return payload

    def save_report(self, player: Player, request: Any, payload: dict[str, Any]) -> ScoutingReport:
        tactical_fit = payload['tactical_fit']
        key = self.cache_key(request.player_id, request.club, request.preferred_system)
        report = self.db.scalar(select(ScoutingReport).where(ScoutingReport.cache_key == key))
        if not report:
            report = ScoutingReport(player_id=player.id, cache_key=key)
            self.db.add(report)

        report.requested_system = request.preferred_system
        report.buying_club = request.club
        report.fit_score = tactical_fit.get('fit_score', 0)
        report.risk_score = risk_profile_score(payload['player'], tactical_fit)
        report.consistency_score = consistency_score(payload['player'])
        report.confidence_score = scouting_confidence_score(payload['player'], tactical_fit, payload.get('similar_players', []))
        report.development_notes = development_trajectory_notes(payload['player'], tactical_fit)
        report.report_payload = {
            **payload,
            'memory': {
                'risk_profile_score': report.risk_score,
                'consistency_score': report.consistency_score,
                'scouting_confidence_score': report.confidence_score,
                'development_trajectory_notes': report.development_notes,
            },
        }
        self.db.flush()
        return report

    def list_reports(self, limit: int = 50) -> list[ScoutingReport]:
        return list(self.db.scalars(select(ScoutingReport).order_by(desc(ScoutingReport.created_at)).limit(limit)))


class TacticalProfilePersistenceService:
    def __init__(self, db: Session):
        self.db = db

    def save_profile(self, player: Player, payload: dict[str, Any]) -> TacticalProfile:
        tactical_fit = payload['tactical_fit']
        role = tactical_fit.get('role_match', {}).get('primary_role', {}).get('label', '')
        profile = TacticalProfile(
            player_id=player.id,
            system=tactical_fit.get('system', ''),
            identified_system=tactical_fit.get('identified_system', ''),
            role=role,
            fit_score=tactical_fit.get('fit_score', 0),
            risk_score=risk_profile_score(payload['player'], tactical_fit),
            confidence_score=scouting_confidence_score(payload['player'], tactical_fit, payload.get('similar_players', [])),
            strengths=tactical_fit.get('tactical_strengths', []),
            weaknesses=tactical_fit.get('tactical_weaknesses', []),
        )
        self.db.add(profile)
        self.db.flush()
        return profile


class HistoryPersistenceService:
    def __init__(self, db: Session):
        self.db = db

    def record_search(self, query: str, result_count: int) -> None:
        self.db.add(PlayerSearchHistory(query=query, result_count=result_count))
        self.db.flush()

    def save_comparisons(self, player: Player, comparisons: list[dict[str, Any]]) -> None:
        for comparison in comparisons:
            self.db.add(
                Comparison(
                    player_id=player.id,
                    compared_player_external_id=comparison.get('id', ''),
                    compared_player_name=comparison.get('name', ''),
                    similarity_score=comparison.get('similarityScore', 0),
                    tactical_score=comparison.get('tacticalSimilarityScore', 0),
                    risk_delta=comparison.get('riskDelta', 0),
                    matrix=comparison.get('comparisonMatrix', {}),
                )
            )
        self.db.flush()

    def comparison_history(self, external_id: str) -> list[dict[str, Any]]:
        player = self.db.scalar(select(Player).where(Player.external_id == external_id))
        if not player:
            return []
        comparisons = self.db.scalars(
            select(Comparison)
            .where(Comparison.player_id == player.id)
            .order_by(desc(Comparison.created_at))
        ).all()
        return [serialize_comparison(comparison) for comparison in comparisons]


def persist_scouting_result(db: Session, request: Any, payload: dict[str, Any]) -> dict[str, Any]:
    player_service = PlayerPersistenceService(db)
    report_service = ScoutingReportPersistenceService(db)
    profile_service = TacticalProfilePersistenceService(db)
    history_service = HistoryPersistenceService(db)

    player = player_service.upsert_player(payload['player'])
    report = report_service.save_report(player, request, payload)
    profile_service.save_profile(player, report.report_payload)
    history_service.save_comparisons(player, report.report_payload.get('similar_players', []))
    db.commit()
    return dict(report.report_payload)


def get_cached_scouting_result(db: Session, request: Any) -> dict[str, Any] | None:
    return ScoutingReportPersistenceService(db).get_cached_report(
        request.player_id,
        request.club,
        request.preferred_system,
    )


def serialize_player(player: Player) -> dict[str, Any]:
    return {
        'id': player.external_id,
        'database_id': player.id,
        'name': player.name,
        'position': player.position,
        'club': player.club,
        'nationality': player.nationality,
        'age': player.age,
        'estimatedValue': player.estimated_value,
        'source': player.source,
        'created_at': player.created_at.isoformat(),
        'updated_at': player.updated_at.isoformat(),
    }


def serialize_report(report: ScoutingReport) -> dict[str, Any]:
    return {
        'id': report.id,
        'player': serialize_player(report.player),
        'requested_system': report.requested_system,
        'buying_club': report.buying_club,
        'fit_score': report.fit_score,
        'risk_score': report.risk_score,
        'consistency_score': report.consistency_score,
        'scouting_confidence_score': report.confidence_score,
        'development_trajectory_notes': report.development_notes,
        'created_at': report.created_at.isoformat(),
        'payload': report.report_payload,
    }


def serialize_tactical_profile(profile: TacticalProfile) -> dict[str, Any]:
    return {
        'id': profile.id,
        'system': profile.system,
        'identified_system': profile.identified_system,
        'role': profile.role,
        'fit_score': profile.fit_score,
        'risk_score': profile.risk_score,
        'confidence_score': profile.confidence_score,
        'strengths': profile.strengths,
        'weaknesses': profile.weaknesses,
        'created_at': profile.created_at.isoformat(),
    }


def serialize_comparison(comparison: Comparison) -> dict[str, Any]:
    return {
        'id': comparison.id,
        'compared_player_id': comparison.compared_player_external_id,
        'compared_player_name': comparison.compared_player_name,
        'similarity_score': comparison.similarity_score,
        'tactical_score': comparison.tactical_score,
        'risk_delta': comparison.risk_delta,
        'matrix': comparison.matrix,
        'created_at': comparison.created_at.isoformat(),
    }
