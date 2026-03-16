import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Nova-Devops-Automate | Infrastructure Guardian",
  description: "AI-Powered FinOps and Security for Infrastructure-as-Code",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${geistSans.variable} ${geistMono.variable} antialiased flex h-screen overflow-hidden`}>
        {/* Sidebar Nav */}
        <aside className="w-64 border-r border-slate-800 bg-slate-950/50 flex flex-col shrink-0">
          <div className="p-6 border-b border-slate-800 flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
              <span className="text-xl">🛡️</span>
            </div>
            <div>
              <h1 className="text-sm font-bold tracking-tight">NOVA DEVOPS</h1>
              <p className="text-[10px] text-emerald-500 font-mono tracking-widest">GUARDIAN V1</p>
            </div>
          </div>
          
          <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
            <Link href="/dashboard" className="flex items-center gap-3 px-3 py-2.5 text-sm font-medium text-slate-400 hover:text-emerald-400 hover:bg-emerald-500/5 rounded-lg transition-all group">
              <span className="group-hover:scale-110 transition-transform">📊</span>
              Dashboard
            </Link>
            <Link href="/" className="flex items-center gap-3 px-3 py-2.5 text-sm font-medium text-slate-400 hover:text-emerald-400 hover:bg-emerald-500/5 rounded-lg transition-all group">
              <span className="group-hover:scale-110 transition-transform">⚡</span>
              Manual Audit
            </Link>
            <Link href="/install" className="flex items-center gap-3 px-3 py-2.5 text-sm font-medium text-slate-400 hover:text-emerald-400 hover:bg-emerald-500/5 rounded-lg transition-all group">
              <span className="group-hover:scale-110 transition-transform">🔗</span>
              Integrations
            </Link>
            <div className="pt-4 pb-2 px-3">
              <span className="text-[10px] font-bold text-slate-600 uppercase tracking-widest">Resources</span>
            </div>
            <Link href="/docs" className="flex items-center gap-3 px-3 py-2.5 text-sm font-medium text-slate-400 hover:text-emerald-400 hover:bg-emerald-500/5 rounded-lg transition-all group">
              <span className="group-hover:scale-110 transition-transform">📖</span>
              Documentation
            </Link>
            <Link href="/settings" className="flex items-center gap-3 px-3 py-2.5 text-sm font-medium text-slate-400 hover:text-emerald-400 hover:bg-emerald-500/5 rounded-lg transition-all group">
              <span className="group-hover:scale-110 transition-transform">⚙️</span>
              Settings
            </Link>
          </nav>
          
          <div className="p-4 border-t border-slate-800">
            <div className="rounded-xl bg-slate-900/50 p-4 border border-slate-800">
              <p className="text-[10px] text-slate-500 font-bold uppercase tracking-wider mb-2">Cloud Status</p>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
                <span className="text-xs text-slate-300">Nova API Online</span>
              </div>
            </div>
          </div>
        </aside>

        {/* Main Content Area */}
        <div className="flex-1 flex flex-col min-w-0 bg-slate-950">
          <main className="flex-1 overflow-y-auto">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
