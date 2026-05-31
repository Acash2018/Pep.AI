'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import Sidebar from '../components/Sidebar';
import SearchBar from '../components/SearchBar';
import PlayerCard from '../components/PlayerCard';
import TacticalFit from '../components/TacticalFit';
import LoadingSkeleton from '../components/LoadingSkeleton';
import type { Player, ScoutPlayerResponse } from '../types/player';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000/api';

const fallbackPlayers: Player[] = [
  {
    id: 'p1',
    name: 'Luca Moreno',
    position: 'Attacking Midfielder',
    club: 'Atletico Verde',
    age: 22,
    nationality: 'Spain',
    estimatedValue: 'EUR 52m',
    summary: 'Creative midfielder with strong vision and fast transition play.',
    strengths: ['vision', 'dribbling', 'passing'],
    weaknesses: ['aerial duels', 'defensive work rate'],
    tacticalStyle: 'High press & quick transitions',
    fitScore: 8,
    reportHighlights: ['Driving runs in behind', 'Strong ball retention', 'Accelerates tempo'],
  },
  {
    id: 'p2',
    name: 'Mikael Sorensen',
    position: 'Left Wing-Back',
    club: 'Northern City',
    age: 24,
    nationality: 'Denmark',
    estimatedValue: 'EUR 39m',
    summary: 'Energetic full-back who combines width with ball-carrying ability.',
    strengths: ['stamina', 'crossing', 'tackling'],
    weaknesses: ['concentration', 'vertical passing'],
    tacticalStyle: 'Wide build-up and overlapping runs',
    fitScore: 7,
    reportHighlights: ['Consistent defensive cover', 'Excellent crossing range'],
  },
];

export default function HomePage() {
  const [query, setQuery] = useState('');
  const [players, setPlayers] = useState<Player[]>(fallbackPlayers);
  const [selectedPlayerId, setSelectedPlayerId] = useState(fallbackPlayers[0].id);
  const [preferredSystem, setPreferredSystem] = useState('High press & quick transitions');
  const [report, setReport] = useState<ScoutPlayerResponse | null>(null);
  const [loadingPlayers, setLoadingPlayers] = useState(true);
  const [loadingReport, setLoadingReport] = useState(false);
  const [ingesting, setIngesting] = useState(false);
  const [ingestStatus, setIngestStatus] = useState('');
  const [error, setError] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [allPlayers, setAllPlayers] = useState<Player[]>(fallbackPlayers);
  const scoutingRequestId = useRef(0);

  async function refreshPlayers() {
    const response = await fetch(`${API_BASE_URL}/players`);
    if (!response.ok) {
      throw new Error('Could not load players');
    }
    const data = await response.json();
    setPlayers(data.players);
    setAllPlayers(data.players);
    setSelectedPlayerId((currentId) => {
      if (data.players.some((player: Player) => player.id === currentId)) {
        return currentId;
      }
      return data.players[0]?.id ?? fallbackPlayers[0].id;
    });
    return data.players as Player[];
  }

  useEffect(() => {
    async function loadPlayers() {
      try {
        await refreshPlayers();
      } catch {
        setPlayers(fallbackPlayers);
      } finally {
        setLoadingPlayers(false);
      }
    }

    loadPlayers();
  }, []);

  const filteredPlayers = useMemo(() => {
    const lowerQuery = query.toLowerCase();
    return players.filter((player) =>
      player.name.toLowerCase().includes(lowerQuery) ||
      player.position.toLowerCase().includes(lowerQuery) ||
      player.club.toLowerCase().includes(lowerQuery)
    );
  }, [players, query]);

  const selectedPlayer = players.find((player) => player.id === selectedPlayerId) ?? players[0];

  async function scoutPlayer(playerId = selectedPlayerId) {
    if (!playerId) {
      return;
    }

    const requestId = scoutingRequestId.current + 1;
    scoutingRequestId.current = requestId;
    setLoadingReport(true);
    setError('');

    try {
      const response = await fetch(`${API_BASE_URL}/scout-player`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          player_id: playerId,
          club: 'Pep.AI XI',
          preferred_system: preferredSystem,
          force_refresh: true,
        }),
      });

      if (!response.ok) {
        throw new Error('Scouting request failed');
      }

      const data = await response.json();
      if (requestId === scoutingRequestId.current) {
        setReport(data);
      }
    } catch {
      if (requestId === scoutingRequestId.current) {
        setError('Unable to generate the scouting report. Check that the FastAPI backend is running.');
      }
    } finally {
      if (requestId === scoutingRequestId.current) {
        setLoadingReport(false);
      }
    }
  }

  async function scoutForSystem() {
    if (!preferredSystem.trim()) {
      setError('Enter a tactical system before scouting.');
      return;
    }
    setError('');
    setFilterStatus('');

    try {
      const response = await fetch(
        `${API_BASE_URL}/players/scout-candidates?system=${encodeURIComponent(preferredSystem)}`,
      );
      if (!response.ok) {
        throw new Error('Filter request failed');
      }
      const data = await response.json();
      const candidates = (data.players ?? []) as Player[];

      if (candidates.length === 0) {
        setPlayers([]);
        setFilterStatus(
          `No players score 54+ for ${data.system_label ?? preferredSystem} (evaluated ${data.evaluated ?? 0} position-compatible players).`,
        );
        setReport(null);
        return;
      }

      setPlayers(candidates);
      setFilterStatus(
        `Showing ${candidates.length} player${candidates.length === 1 ? '' : 's'} with 54+ fit for ${data.system_label ?? preferredSystem}.`,
      );

      const stillVisible = candidates.find((p) => p.id === selectedPlayerId);
      const target = stillVisible ?? candidates[0];
      setSelectedPlayerId(target.id);
      await scoutPlayer(target.id);
    } catch {
      setError('Unable to filter candidates. Check that the FastAPI backend is running.');
    }
  }

  function clearSystemFilter() {
    setPlayers(allPlayers);
    setFilterStatus('');
  }

  async function ingestStatsBombPlayers() {
    setIngesting(true);
    setError('');
    setIngestStatus('Ingesting StatsBomb Open Data...');

    try {
      const response = await fetch(`${API_BASE_URL}/players/ingest/statsbomb?max_matches=6`, {
        method: 'POST',
      });
      if (!response.ok) {
        throw new Error('Ingestion failed');
      }

      const result = await response.json();
      const updatedPlayers = await refreshPlayers();
      const firstIngested = updatedPlayers.find((player) => player.id.startsWith('sb-'));
      if (firstIngested) {
        setSelectedPlayerId(firstIngested.id);
        await scoutPlayer(firstIngested.id);
      }
      setIngestStatus(
        `Loaded ${result.players_ingested} StatsBomb players from ${result.matches_ingested} Bundesliga matches.`
      );
    } catch {
      setError('Unable to ingest public player data. Check the backend connection and internet access.');
      setIngestStatus('');
    } finally {
      setIngesting(false);
    }
  }

  useEffect(() => {
    if (selectedPlayerId && !loadingPlayers) {
      scoutPlayer(selectedPlayerId);
    }
  }, [selectedPlayerId, loadingPlayers]);

  return (
    <main className="min-h-screen bg-pitch px-6 py-6 lg:px-10">
      <div className="grid gap-6 xl:grid-cols-[280px_1fr]">
        <Sidebar />
        <section className="space-y-6">
          <div className="rounded-lg border border-white/10 bg-[#111827]/90 p-6 shadow-2xl shadow-black/20">
            <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
              <div>
                <p className="text-sm uppercase text-slate-400">Scout overview</p>
                <h1 className="mt-3 text-4xl font-semibold text-white">Football scouting dashboard</h1>
                <p className="mt-2 text-sm text-slate-400">
                  Selected player: <span className="font-semibold text-emerald-300">{selectedPlayer?.name ?? 'None'}</span>
                </p>
              </div>
              <div className="flex flex-col gap-3 sm:flex-row">
                <input
                  value={preferredSystem}
                  onChange={(event) => setPreferredSystem(event.target.value)}
                  className="min-w-0 rounded-lg border border-white/10 bg-slate-950/80 px-4 py-3 text-sm text-white outline-none transition focus:border-accent sm:w-80"
                  aria-label="Preferred tactical system"
                />
                <button
                  type="button"
                  onClick={scoutForSystem}
                  disabled={loadingReport}
                  className="rounded-lg bg-emerald-500 px-4 py-3 text-sm font-semibold text-slate-950 transition hover:bg-emerald-400 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {loadingReport ? 'Scouting...' : 'Scout player'}
                </button>
                <button
                  type="button"
                  onClick={ingestStatsBombPlayers}
                  disabled={ingesting}
                  className="rounded-lg border border-white/10 bg-slate-950/80 px-4 py-3 text-sm font-semibold text-white transition hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {ingesting ? 'Ingesting...' : 'Ingest public data'}
                </button>
              </div>
            </div>
          </div>

          <SearchBar query={query} onChange={setQuery} />

          {error ? (
            <div className="rounded-lg border border-red-400/30 bg-red-500/10 p-4 text-sm text-red-200">{error}</div>
          ) : null}
          {ingestStatus ? (
            <div className="rounded-lg border border-emerald-400/30 bg-emerald-500/10 p-4 text-sm text-emerald-200">{ingestStatus}</div>
          ) : null}
          {filterStatus ? (
            <div className="flex items-center justify-between gap-4 rounded-lg border border-sky-400/30 bg-sky-500/10 p-4 text-sm text-sky-200">
              <span>{filterStatus}</span>
              <button
                type="button"
                onClick={clearSystemFilter}
                className="rounded-md border border-sky-300/40 px-3 py-1 text-xs font-semibold text-sky-100 transition hover:bg-sky-400/20"
              >
                Show all players
              </button>
            </div>
          ) : null}

          <div className="grid gap-6 xl:grid-cols-[1.35fr_1fr]">
            <div className="space-y-6">
              {loadingPlayers ? (
                <LoadingSkeleton />
              ) : (
                <div className="grid gap-5">
                  {filteredPlayers.map((player) => (
                    <button
                      key={player.id}
                      type="button"
                      onClick={() => {
                        setSelectedPlayerId(player.id);
                        scoutPlayer(player.id);
                      }}
                      className={`rounded-lg text-left transition ${player.id === selectedPlayerId ? 'ring-2 ring-emerald-400' : ''}`}
                    >
                      <PlayerCard player={player} selected={player.id === selectedPlayerId} />
                    </button>
                  ))}
                </div>
              )}
            </div>

            <div className="space-y-6">
              {report ? (
                <>
                  <TacticalFit
                    style={report.tactical_fit.system}
                    fitScore={report.tactical_fit.fit_score}
                    notes={report.tactical_fit.notes}
                    roleProjection={report.tactical_fit.role_projection}
                    fitGrade={report.tactical_fit.fit_grade}
                    roleMatch={report.tactical_fit.role_match}
                    systemCompatibility={report.tactical_fit.system_compatibility}
                    tacticalStrengths={report.tactical_fit.tactical_strengths}
                    tacticalWeaknesses={report.tactical_fit.tactical_weaknesses}
                    whyFit={report.tactical_fit.why_fit}
                    whyNot={report.tactical_fit.why_not}
                    retrievedKnowledge={report.tactical_fit.retrieved_knowledge}
                  />
                  <div className="rounded-lg border border-white/10 bg-white/5 p-6 shadow-lg shadow-black/10">
                    <p className="text-sm uppercase text-slate-400">Final Report</p>
                    <h2 className="mt-2 text-2xl font-semibold text-white">{report.player.name}</h2>
                    <p className="mt-4 text-sm leading-6 text-slate-300">{report.report.summary}</p>
                    {report.report.llm_model ? (
                      <p className="mt-3 text-xs uppercase text-slate-500">Reasoning layer: {report.report.llm_model}</p>
                    ) : null}
                    {report.memory ? (
                      <div className="mt-5 grid gap-3 sm:grid-cols-3">
                        <Metric label="Consistency" value={report.memory.consistency_score} />
                        <Metric label="Risk" value={report.memory.risk_profile_score} />
                        <Metric label="Confidence" value={report.memory.scouting_confidence_score} />
                      </div>
                    ) : null}
                    {report.memory?.development_trajectory_notes ? (
                      <p className="mt-4 rounded-lg bg-slate-950/70 p-4 text-sm text-slate-300">{report.memory.development_trajectory_notes}</p>
                    ) : null}
                    <div className="mt-5 grid gap-3 sm:grid-cols-2">
                      <ReportList title="Strengths" items={report.strengths} />
                      <ReportList title="Weaknesses" items={report.weaknesses} />
                    </div>
                    {report.report.scout_reasoning ? (
                      <div className="mt-5 grid gap-3 sm:grid-cols-3">
                        <ReportList title="GPT Strengths" items={report.report.scout_reasoning.strengths ?? []} />
                        <ReportList title="GPT Weaknesses" items={report.report.scout_reasoning.weaknesses ?? []} />
                        <ReportList title="Development Areas" items={report.report.scout_reasoning.development_areas ?? []} />
                      </div>
                    ) : null}
                    {report.report.gpt_tactical_reasoning ? (
                      <div className="mt-5 grid gap-3 sm:grid-cols-3">
                        <ReportList title="Tactical Suitability" items={report.report.gpt_tactical_reasoning.tactical_suitability ?? []} />
                        <ReportList title="Tactical Risks" items={report.report.gpt_tactical_reasoning.tactical_risks ?? []} />
                        <ReportList title="Formation Fit" items={report.report.gpt_tactical_reasoning.formation_fit ?? []} />
                      </div>
                    ) : null}
                    {report.report.comparison_analysis ? (
                      <div className="mt-5 rounded-lg bg-slate-950/70 p-4">
                        <p className="text-xs uppercase text-slate-500">GPT Comparison Analysis</p>
                        <div className="mt-3 grid gap-3 sm:grid-cols-2">
                          <ReportList title="Similarities" items={report.report.comparison_analysis.similarities ?? []} />
                          <ReportList title="Differences" items={report.report.comparison_analysis.differences ?? []} />
                        </div>
                        {report.report.comparison_analysis.recruitment_meaning ? (
                          <p className="mt-3 text-sm text-slate-300">{report.report.comparison_analysis.recruitment_meaning}</p>
                        ) : null}
                      </div>
                    ) : null}
                    {report.report.final_report_markdown ? (
                      <div className="mt-5 rounded-lg bg-slate-950/70 p-4">
                        <p className="text-xs uppercase text-slate-500">Professional Scouting Report</p>
                        <pre className="mt-3 whitespace-pre-wrap text-sm leading-6 text-slate-300">{report.report.final_report_markdown}</pre>
                      </div>
                    ) : null}
                    <div className="mt-5 rounded-lg bg-slate-950/70 p-4">
                      <p className="text-xs uppercase text-slate-500">Transfer Value</p>
                      <p className="mt-2 text-lg font-semibold text-white">{report.transfer_value}</p>
                    </div>
                  </div>
                  <div className="rounded-lg border border-white/10 bg-white/5 p-6 shadow-lg shadow-black/10">
                    <p className="text-sm uppercase text-slate-400">Similar players</p>
                    <div className="mt-5 space-y-3">
                      {report.similar_players.map((player) => (
                        <div key={player.id} className="rounded-lg bg-slate-950/70 p-4">
                          <p className="font-semibold text-white">{player.name}</p>
                          <p className="text-sm text-slate-400">{player.position} - {player.club}</p>
                          {typeof player.similarityScore === 'number' ? (
                            <p className="mt-2 text-xs text-emerald-300">Similarity {player.similarityScore}/100</p>
                          ) : null}
                          {player.similarityReasons?.length ? (
                            <p className="mt-1 text-xs text-slate-500">{player.similarityReasons.join(', ')}</p>
                          ) : null}
                        </div>
                      ))}
                    </div>
                  </div>
                </>
              ) : (
                <div className="rounded-lg border border-white/10 bg-white/5 p-6 text-sm text-slate-300">
                  Select {selectedPlayer?.name ?? 'a player'} and run a scouting report.
                </div>
              )}
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}

function ReportList({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="rounded-lg bg-slate-950/70 p-4">
      <p className="text-xs uppercase text-slate-500">{title}</p>
      <ul className="mt-3 space-y-2 text-sm text-slate-300">
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg bg-slate-950/70 p-4">
      <p className="text-xs uppercase text-slate-500">{label}</p>
      <p className="mt-2 text-lg font-semibold text-white">{value}/100</p>
    </div>
  );
}
