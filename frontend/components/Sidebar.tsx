import Link from 'next/link';

const navItems = [
  { label: 'Dashboard', href: '/' },
  { label: 'Saved Reports', href: '/reports' },
  { label: 'Compare', href: '/compare' },
  { label: 'History', href: '/history' },
];

export default function Sidebar() {
  return (
    <aside className="w-full max-w-[280px] rounded-lg border border-white/10 bg-[#111827]/90 p-6 shadow-2xl shadow-black/20">
      <div className="mb-8">
        <p className="text-sm uppercase text-slate-400">Pep.AI</p>
        <h1 className="mt-4 text-3xl font-semibold text-white">Scout Hub</h1>
        <p className="mt-2 text-sm text-slate-400">AI football scouting made simple.</p>
      </div>
      <nav className="space-y-3">
        {navItems.map((item) => (
          <Link key={item.href} href={item.href} className="block rounded-lg px-4 py-3 text-sm font-medium text-slate-200 transition hover:bg-white/10">
            {item.label}
          </Link>
        ))}
      </nav>
    </aside>
  );
}
