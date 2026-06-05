import './globals.css';

export const metadata = {
  title: 'Pep.AI | Football Scouting',
  description: 'AI-powered football scouting dashboard',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-pitch text-white">{children}</body>
    </html>
  );
}
