'use client';

import { useEffect, useState } from 'react';
import Sidebar from '../../../components/Sidebar';
import type { PlayerTimeline } from '../../../types/player';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000/api';

export default function PlayerProfilePage({ params }: { params: { id: string } }) {
  const [timeline, setTimeline] = useState<PlayerTimeline | null>(null);

  useEffect(() => {
    fetch(`${API_BASE_URL}/memory/players/${params.id}/timeline`)
      .then((response) => response.json())
      .then(setTimeline);
  }, [params.id]);

  return (
    <main className="min-h-screen bg-pitch px-6 py-6 lg:px-10">
      <div className="grid gap-6 xl:grid-cols-[280px_1fr]">
        <Sidebar />
        <section className="space-y-6">
          {timeline ? (
            <>
              <div className="rounded-lg border border-white/10 bg-[#111827]/90 p-6">
                <p className="text-sm uppercase text-slate-400">Player Profile</p>
                <h1 className="mt-3 text-4xl font-semibold text-white">{timeline.player.name}</h1>
                <p className="mt-2 text-sm text-slate-400">{timeline.player.position} - {timeline.player.club}</p>
              </div>
              <div className="grid gap-6 lg:grid-cols-3">
                <Metric label="Reports" value={timeline.reports.length} />
                <Metric label="Latest Fit" value={timeline.tactical_profiles[0]?.fit_score ?? 0} />
                <Metric label="Latest Risk" value={timeline.tactical_profiles[0]?.risk_score ?? 0} />
              </div>
              <section className="rounded-lg border border-white/10 bg-white/5 p-6">
                <h2 className="text-2xl font-semibold text-white">Development Timeline</h2>
                <div className="mt-5 space-y-3">
                  {timeline.reports.map((report) => (
                    <article key={report.id} className="rounded-lg bg-slate-950/70 p-4">
                      <p className="font-semibold text-white">{report.requested_system}</p>
                      <p className="mt-1 text-sm text-slate-400">{new Date(report.created_at).toLocaleString()}</p>
                      <p className="mt-3 text-sm text-slate-300">{report.development_trajectory_notes}</p>
                    </article>
                  ))}
                </div>
              </section>
            </>
          ) : (
            <div className="rounded-lg border border-white/10 bg-white/5 p-6 text-slate-300">No saved profile found.</div>
          )}
        </section>
      </div>
    </main>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-white/10 bg-white/5 p-5">
      <p className="text-xs uppercase text-slate-500">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-white">{value}</p>
    </div>
  );
}
