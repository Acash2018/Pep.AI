'use client';

import { useEffect, useState } from 'react';
import Sidebar from '../../components/Sidebar';
import type { Player } from '../../types/player';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000/api';

type SavedComparison = {
  id: number;
  compared_player_id: string;
  compared_player_name: string;
  similarity_score: number;
  tactical_score: number;
  risk_delta: number;
  matrix: {
    strengths_weaknesses?: {
      shared_strengths: string[];
      player_unique_strengths: string[];
      candidate_unique_strengths: string[];
      shared_weaknesses: string[];
    };
  };
  created_at: string;
};

export default function ComparePage() {
  const [players, setPlayers] = useState<Player[]>([]);
  const [selectedPlayerId, setSelectedPlayerId] = useState('');
  const [comparisons, setComparisons] = useState<SavedComparison[]>([]);

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
    fetch(`${API_BASE_URL}/memory/comparisons/${selectedPlayerId}`)
      .then((response) => response.json())
      .then((data) => setComparisons(data.comparisons ?? []));
  }, [selectedPlayerId]);

  return (
    <main className="min-h-screen bg-pitch px-6 py-6 lg:px-10">
      <div className="grid gap-6 xl:grid-cols-[280px_1fr]">
        <Sidebar />
        <section className="space-y-6">
          <div className="rounded-lg border border-white/10 bg-[#111827]/90 p-6">
            <p className="text-sm uppercase text-slate-400">Comparison Dashboard</p>
            <h1 className="mt-3 text-4xl font-semibold text-white">Historical Player Comparisons</h1>
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
          <div className="grid gap-4 lg:grid-cols-2">
            {comparisons.map((comparison) => (
              <article key={comparison.id} className="rounded-lg border border-white/10 bg-white/5 p-6">
                <h2 className="text-xl font-semibold text-white">{comparison.compared_player_name}</h2>
                <div className="mt-4 grid grid-cols-3 gap-3">
                  <Metric label="Similarity" value={comparison.similarity_score} />
                  <Metric label="Tactical" value={comparison.tactical_score} />
                  <Metric label="Risk Delta" value={comparison.risk_delta} />
                </div>
                <div className="mt-5 rounded-lg bg-slate-950/70 p-4 text-sm text-slate-300">
                  <p className="text-xs uppercase text-slate-500">Strengths Matrix</p>
                  <p className="mt-2">Shared: {comparison.matrix.strengths_weaknesses?.shared_strengths?.join(', ') || 'None'}</p>
                  <p className="mt-1">Target unique: {comparison.matrix.strengths_weaknesses?.player_unique_strengths?.join(', ') || 'None'}</p>
                  <p className="mt-1">Comparison unique: {comparison.matrix.strengths_weaknesses?.candidate_unique_strengths?.join(', ') || 'None'}</p>
                </div>
              </article>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg bg-slate-950/70 p-3 text-center">
      <p className="text-xs uppercase text-slate-500">{label}</p>
      <p className="mt-1 font-semibold text-white">{value}</p>
    </div>
  );
}
