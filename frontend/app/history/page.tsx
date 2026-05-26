'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import Sidebar from '../../components/Sidebar';
import type { Player, PlayerTimeline } from '../../types/player';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000/api';

export default function HistoryPage() {
  const [players, setPlayers] = useState<Player[]>([]);
  const [selectedPlayerId, setSelectedPlayerId] = useState('');
  const [timeline, setTimeline] = useState<PlayerTimeline | null>(null);

  useEffect(() => {
    fetch(`${API_BASE_URL}/memory/players`)
      .then((response) => response.json())
      .then((data) => {
        const analyzed = data.players ?? [];
        setPlayers(analyzed);
        setSelectedPlayerId(analyzed[0]?.id ?? '');
      });
  }, []);

  useEffect(() => {
    if (!selectedPlayerId) {
      return;
    }
    fetch(`${API_BASE_URL}/memory/players/${selectedPlayerId}/timeline`)
      .then((response) => response.json())
      .then(setTimeline);
  }, [selectedPlayerId]);

  return (
    <main className="min-h-screen bg-pitch px-6 py-6 lg:px-10">
      <div className="grid gap-6 xl:grid-cols-[280px_1fr]">
        <Sidebar />
        <section className="space-y-6">
          <div className="rounded-lg border border-white/10 bg-[#111827]/90 p-6">
            <p className="text-sm uppercase text-slate-400">Historical Analysis</p>
            <h1 className="mt-3 text-4xl font-semibold text-white">Player Timeline</h1>
            <select
              value={selectedPlayerId}
              onChange={(event) => setSelectedPlayerId(event.target.value)}
              className="mt-5 w-full max-w-md rounded-lg border border-white/10 bg-slate-950/80 px-4 py-3 text-white"
            >
              {players.map((player) => (
                <option key={player.id} value={player.id}>{player.name}</option>
              ))}
            </select>
          </div>
          {timeline ? (
            <div className="grid gap-6 lg:grid-cols-[1fr_1fr]">
              <section className="rounded-lg border border-white/10 bg-white/5 p-6">
                <Link href={`/players/${timeline.player.id}`} className="text-2xl font-semibold text-white hover:text-emerald-300">
                  {timeline.player.name}
                </Link>
                <p className="mt-2 text-sm text-slate-400">{timeline.player.position} - {timeline.player.club}</p>
                <div className="mt-5 space-y-3">
                  {timeline.reports.map((report) => (
                    <div key={report.id} className="rounded-lg bg-slate-950/70 p-4">
                      <p className="font-semibold text-white">{report.requested_system}</p>
                      <p className="text-sm text-slate-400">Fit {report.fit_score}/100 - Risk {report.risk_score}/100 - Confidence {report.scouting_confidence_score}/100</p>
                      <p className="mt-2 text-sm text-slate-300">{report.development_trajectory_notes}</p>
                    </div>
                  ))}
                </div>
              </section>
              <section className="rounded-lg border border-white/10 bg-white/5 p-6">
                <h2 className="text-2xl font-semibold text-white">Tactical Fit Evolution</h2>
                <div className="mt-5 space-y-3">
                  {timeline.tactical_profiles.map((profile) => (
                    <div key={profile.id} className="rounded-lg bg-slate-950/70 p-4">
                      <p className="font-semibold text-white">{profile.system}</p>
                      <p className="text-sm text-slate-400">{profile.role} - {profile.identified_system}</p>
                      <p className="mt-2 text-sm text-emerald-300">Fit {profile.fit_score}/100</p>
                    </div>
                  ))}
                </div>
              </section>
            </div>
          ) : null}
        </section>
      </div>
    </main>
  );
}
