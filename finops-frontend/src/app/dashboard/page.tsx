"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

interface SeverityCounts {
  CRITICAL: number;
  HIGH: number;
  MEDIUM: number;
  LOW: number;
  INFO: number;
}

interface Scan {
  id: string;
  repo: string;
  pr_number: number | null;
  commit_sha: string | null;
  overall_score: number;
  overall_grade: string;
  files_scanned: number;
  total_findings: number;
  severity_counts: SeverityCounts;
  created_at: string;
}

const GRADE_COLOR: Record<string, string> = {
  A: "text-emerald-400 border-emerald-500/30 bg-emerald-500/5",
  B: "text-green-400 border-green-500/30 bg-green-500/5",
  C: "text-yellow-400 border-yellow-500/30 bg-yellow-500/5",
  D: "text-orange-400 border-orange-500/30 bg-orange-500/5",
  F: "text-red-400 border-red-500/30 bg-red-500/5",
};

const SEVERITY_DOT: Record<string, string> = {
  CRITICAL: "bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.5)]",
  HIGH: "bg-orange-500",
  MEDIUM: "bg-yellow-500",
  LOW: "bg-blue-500",
};

function ScoreBadge({ score, grade }: { score: number; grade: string }) {
  const style = GRADE_COLOR[grade] || "text-slate-400 border-slate-800 bg-slate-900";
  return (
    <div className={`px-4 py-2 rounded-xl border ${style} flex flex-col items-center justify-center min-w-[64px]`}>
      <span className="text-xl font-black">{grade}</span>
      <span className="text-[10px] opacity-60 font-bold uppercase">{score}</span>
    </div>
  );
}

function ScanCard({ scan }: { scan: Scan }) {
  const counts = scan.severity_counts || {};
  const when = new Date(scan.created_at).toLocaleDateString(undefined, {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
  });

  return (
    <Link href={`/scans/${scan.id}`}>
      <article className="group rounded-2xl border border-slate-800 bg-slate-900/30 p-5 hover:border-emerald-500/40 hover:bg-slate-900/50 transition-all cursor-pointer space-y-4 relative overflow-hidden">
        <div className="absolute top-0 right-0 p-2 opacity-0 group-hover:opacity-100 transition-opacity">
          <span className="text-emerald-500 text-xs">View Details →</span>
        </div>
        
        {/* Header */}
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-1">
            <p className="font-bold text-slate-100 tracking-tight">{scan.repo}</p>
            <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-wider text-slate-500">
              <span className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">
                {scan.pr_number ? `PR #${scan.pr_number}` : "PUSH"}
              </span>
              <span>•</span>
              <span>{when}</span>
            </div>
          </div>
          <ScoreBadge score={scan.overall_score} grade={scan.overall_grade} />
        </div>

        {/* Severity pills */}
        <div className="flex flex-wrap gap-2 pt-2">
          {(["CRITICAL", "HIGH", "MEDIUM", "LOW"] as const).map((sev) =>
            (counts[sev] || 0) > 0 ? (
              <span
                key={sev}
                className="inline-flex items-center gap-1.5 rounded-full border border-slate-800 bg-slate-950 px-2.5 py-1 text-[10px] font-bold text-slate-300"
              >
                <span className={`w-1.5 h-1.5 rounded-full ${SEVERITY_DOT[sev]}`} />
                {counts[sev]} {sev}
              </span>
            ) : null
          )}
          {scan.total_findings === 0 && (
            <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-500/20 bg-emerald-500/5 px-2.5 py-1 text-[10px] font-bold text-emerald-400">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
              CLEAN
            </span>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between pt-2 border-t border-slate-800/50">
          <p className="text-[10px] font-bold text-slate-600 uppercase tracking-widest">
            {scan.files_scanned} FILE(S) SCANNED
          </p>
          <div className="h-1.5 w-24 bg-slate-800 rounded-full overflow-hidden">
            <div 
              className="h-full bg-emerald-500 rounded-full transition-all duration-1000" 
              style={{ width: `${scan.overall_score}%` }}
            />
          </div>
        </div>
      </article>
    </Link>
  );
}

export default function DashboardPage() {
  const [scans, setScans] = useState<Scan[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [repoFilter, setRepoFilter] = useState("");

  useEffect(() => {
    const fetchScans = async () => {
      try {
        const params = repoFilter ? `?repo=${encodeURIComponent(repoFilter)}` : "";
        const res = await fetch(`/api/scans${params}`);
        if (!res.ok) throw new Error("Failed to connect to scanner API");
        const data = await res.json();
        setScans(data.scans || []);
      } catch (e: any) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    };
    fetchScans();
    const iv = setInterval(fetchScans, 15_000); // Faster refresh for "real-time" feel
    return () => clearInterval(iv);
  }, [repoFilter]);

  // Stats
  const avgScore = scans.length
    ? Math.round(scans.reduce((a, s) => a + s.overall_score, 0) / scans.length)
    : 0;
  const totalFindings = scans.reduce((a, s) => a + s.total_findings, 0);
  const repos = new Set(scans.map((s) => s.repo)).size;

  return (
    <div className="p-8 space-y-8 animate-in fade-in duration-700">
      {/* Page Header */}
      <div className="flex items-end justify-between">
        <div>
          <h2 className="text-3xl font-black tracking-tight uppercase">Operational <span className="gradient-text">Overview</span></h2>
          <p className="text-slate-500 font-medium">Monitoring {repos} active repositories for compliance and cost.</p>
        </div>
        <div className="flex gap-3">
           <input
            className="rounded-xl border border-slate-800 bg-slate-900/50 px-4 py-2 text-sm outline-none focus:ring-2 focus:ring-emerald-500/40 w-64 transition-all"
            placeholder="Filter by repository..."
            value={repoFilter}
            onChange={(e) => setRepoFilter(e.target.value)}
          />
        </div>
      </div>

      {/* Hero Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {[
          { label: "Active Nodes", value: repos, sub: "Healthy Connections", icon: "🌐" },
          { label: "Average Grade", value: avgScore, sub: "Global Score Baseline", icon: "📈", unit: "/100" },
          {
            label: "Risk Alerts",
            value: totalFindings,
            sub: "Total Findings Found",
            icon: "🚨",
            critical: totalFindings > 20
          },
        ].map((stat) => (
          <div
            key={stat.label}
            className={`relative rounded-3xl border p-6 overflow-hidden ${
              stat.critical ? "border-red-500/20 bg-red-500/5" : "border-slate-800 bg-slate-900/40"
            }`}
          >
            <div className="absolute top-4 right-4 text-3xl opacity-20">{stat.icon}</div>
            <p className="text-[11px] font-black text-slate-500 uppercase tracking-widest">{stat.label}</p>
            <div className="flex items-baseline gap-1 mt-1">
              <p className="text-4xl font-black text-slate-100">{stat.value}</p>
              {stat.unit && <span className="text-lg font-bold text-slate-600">{stat.unit}</span>}
            </div>
            <p className="text-xs text-slate-500 font-medium mt-1">{stat.sub}</p>
          </div>
        ))}
      </div>

      {/* Main List */}
      <section className="space-y-4">
        <div className="flex items-center justify-between px-2">
            <h3 className="text-sm font-black text-slate-400 uppercase tracking-[0.2em]">Latest Security Audits</h3>
            <div className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                <span className="text-[10px] font-bold text-slate-500 uppercase">Live Feed</span>
            </div>
        </div>

        {loading ? (
            <div className="grid gap-4 md:grid-cols-2">
                {[1, 2, 3, 4].map(i => (
                    <div key={i} className="h-40 rounded-2xl border border-slate-900 bg-slate-900/20 animate-pulse"></div>
                ))}
            </div>
        ) : scans.length === 0 ? (
          <div className="rounded-3xl border border-dashed border-slate-800 py-24 flex flex-col items-center justify-center text-center space-y-4">
            <div className="w-20 h-20 rounded-full bg-slate-900 flex items-center justify-center text-4xl">🏗️</div>
            <div className="space-y-2">
                <h3 className="text-xl font-bold">No data streams detected</h3>
                <p className="text-slate-500 max-w-xs mx-auto text-sm">Deploy the Nova Guardian to your GitHub repositories to begin real-time infrastructure auditing.</p>
            </div>
            <Link
              href="/install"
              className="rounded-xl bg-emerald-500 px-6 py-2.5 text-sm font-black text-slate-950 hover:bg-emerald-400 transition-colors"
            >
              DEPLOY GUARDIAN
            </Link>
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2">
            {scans.map((scan) => (
              <ScanCard key={scan.id} scan={scan} />
            ))}
          </div>
        )}
      </section>
      
      {error && (
        <div className="p-4 rounded-xl border border-red-500/20 bg-red-500/5 flex items-center gap-3">
            <span className="text-red-500 text-xl">⚠️</span>
            <p className="text-sm text-red-400 font-medium">Connectivity Issue: {error}</p>
        </div>
      )}
    </div>
  );
}
