'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import Sidebar from '../../components/Sidebar';
import type { SavedReport } from '../../types/player';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000/api';

export default function ReportsPage() {
  const [reports, setReports] = useState<SavedReport[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_BASE_URL}/memory/reports`)
      .then((response) => response.json())
      .then((data) => setReports(data.reports ?? []))
      .finally(() => setLoading(false));
  }, []);

  return (
    <main className="min-h-screen bg-pitch px-6 py-6 lg:px-10">
      <div className="grid gap-6 xl:grid-cols-[280px_1fr]">
        <Sidebar />
        <section className="space-y-6">
          <Header title="Saved Reports" subtitle="Cached scouting reports and player memory from previous analysis." />
          {loading ? <p className="text-slate-300">Loading reports...</p> : null}
          <div className="grid gap-4">
            {reports.map((report) => (
              <article key={report.id} className="rounded-lg border border-white/10 bg-white/5 p-6">
                <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                  <div>
                    <Link href={`/players/${report.player.id}`} className="text-xl font-semibold text-white hover:text-emerald-300">
                      {report.player.name}
                    </Link>
                    <p className="mt-1 text-sm text-slate-400">{report.player.position} - {report.player.club}</p>
                    <p className="mt-3 text-sm text-slate-300">{report.payload.report.summary}</p>
                  </div>
                  <div className="grid min-w-64 grid-cols-3 gap-2 text-center">
                    <Metric label="Fit" value={report.fit_score} />
                    <Metric label="Risk" value={report.risk_score} />
                    <Metric label="Confidence" value={report.scouting_confidence_score} />
                  </div>
                </div>
                <p className="mt-4 rounded-lg bg-slate-950/70 p-4 text-sm text-slate-300">{report.development_trajectory_notes}</p>
              </article>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}

function Header({ title, subtitle }: { title: string; subtitle: string }) {
  return (
    <div className="rounded-lg border border-white/10 bg-[#111827]/90 p-6">
      <p className="text-sm uppercase text-slate-400">Pep.AI Memory</p>
      <h1 className="mt-3 text-4xl font-semibold text-white">{title}</h1>
      <p className="mt-2 text-sm text-slate-400">{subtitle}</p>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg bg-slate-950/70 p-3">
      <p className="text-xs uppercase text-slate-500">{label}</p>
      <p className="mt-1 font-semibold text-white">{value}</p>
    </div>
  );
}
