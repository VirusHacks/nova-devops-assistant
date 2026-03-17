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

const GRADE_BG: Record<string, string> = {
  A: "bg-[#2ECC71]", B: "bg-[#2ECC71]", C: "bg-[#FFD600]", D: "bg-[#FF5252]", F: "bg-[#FF5252]",
};

const SEV_BG: Record<string, string> = {
  CRITICAL: "bg-[#FF5252] text-white", HIGH: "bg-[#FFD600]", MEDIUM: "bg-[#00C2FF]", LOW: "bg-[#f0f0f0]",
};

function ScoreBadge({ score, grade }: { score: number; grade: string }) {
  return (
    <div className={`w-[56px] h-[56px] border-[2px] border-[#111] rounded-[10px] shadow-[4px_4px_0px_#000] flex flex-col items-center justify-center ${GRADE_BG[grade] || "bg-white"}`}>
      <span className="text-[22px] font-black leading-none">{grade}</span>
      <span className="text-[10px] font-bold mt-[2px]">{score}</span>
    </div>
  );
}

function ScanCard({ scan }: { scan: Scan }) {
  const counts = scan.severity_counts || {};
  const when = new Date(scan.created_at).toLocaleDateString(undefined, {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
  });

  return (
    <Link href={`/scans/${scan.id}`} className="block group">
      <article className="brutal-card h-full flex flex-col">
        {/* Header */}
        <div className="flex items-start justify-between gap-[16px] mb-[16px]">
          <div className="space-y-[8px] min-w-0">
            <p className="font-bold text-[18px] text-[#111] truncate">{scan.repo}</p>
            <div className="flex items-center gap-[8px] text-[12px] font-semibold text-[#444]">
              <span className="brutal-badge bg-[#f0f0f0]">
                {scan.pr_number ? `PR #${scan.pr_number}` : "PUSH"}
              </span>
              <span>{when}</span>
            </div>
          </div>
          <ScoreBadge score={scan.overall_score} grade={scan.overall_grade} />
        </div>

        {/* Severity */}
        <div className="flex flex-wrap gap-[8px] mb-[16px]">
          {(["CRITICAL", "HIGH", "MEDIUM", "LOW"] as const).map((sev) =>
            (counts[sev] || 0) > 0 ? (
              <span key={sev} className={`brutal-badge ${SEV_BG[sev]}`}>
                {counts[sev]} {sev}
              </span>
            ) : null
          )}
          {scan.total_findings === 0 && (
            <span className="brutal-badge bg-[#2ECC71]">CLEAN</span>
          )}
        </div>

        {/* Footer */}
        <div className="mt-auto pt-[16px] border-t-[2px] border-[#111] flex items-center justify-between">
          <span className="text-[12px] font-bold uppercase tracking-[0.1em]">
            {scan.files_scanned} file(s) scanned
          </span>
          <div className="h-[8px] w-[100px] border-[2px] border-[#111] rounded-[4px] bg-white overflow-hidden">
            <div className="h-full bg-[#111] transition-all duration-1000" style={{ width: `${scan.overall_score}%` }} />
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
      } catch (e: unknown) {
        if (e instanceof Error) {
          setError(e.message);
        } else {
          setError("An unknown error occurred");
        }
      } finally {
        setLoading(false);
      }
    };
    fetchScans();
    const iv = setInterval(fetchScans, 15_000);
    return () => clearInterval(iv);
  }, [repoFilter]);

  const avgScore = scans.length ? Math.round(scans.reduce((a, s) => a + s.overall_score, 0) / scans.length) : 0;
  const totalFindings = scans.reduce((a, s) => a + s.total_findings, 0);
  const repos = new Set(scans.map((s) => s.repo)).size;

  return (
    <div className="space-y-[32px]">
      {/* ── Page Header ── */}
      <div className="page-header flex flex-col md:flex-row items-start md:items-center justify-between gap-[16px]">
        <div>
          <h1>
            Operational <span className="bg-white px-[8px] py-[2px] border-[2px] border-[#111] rounded-[8px] inline-block">Overview</span>
          </h1>
          <p>Monitoring {repos} active repositories for compliance and cost.</p>
        </div>
        <input
          className="brutal-input w-full md:w-[280px] bg-white"
          placeholder="Filter by repository..."
          value={repoFilter}
          onChange={(e) => setRepoFilter(e.target.value)}
        />
      </div>

      {/* ── Stat Cards (3-col) ── */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-[24px]">
        {[
          { label: "Active Nodes", value: repos, sub: "Healthy Connections", icon: "🌐", bg: "bg-[#00C2FF]" },
          { label: "Average Grade", value: avgScore, sub: "Global Score Baseline", icon: "📈", unit: "/100", bg: "bg-[#FFD600]" },
          { label: "Risk Alerts", value: totalFindings, sub: "Total Findings Found", icon: "🚨", bg: totalFindings > 20 ? "bg-[#FF5252]" : "bg-[#FFF3F3]" },
        ].map((stat) => (
          <div key={stat.label} className={`border-[2px] border-[#111] rounded-[10px] shadow-[6px_6px_0px_#000] p-[24px] relative overflow-hidden ${stat.bg}`}>
            <div className="absolute top-[16px] right-[16px] text-[32px] opacity-30">{stat.icon}</div>
            <p className="text-[12px] font-bold uppercase tracking-[0.15em] mb-[8px]">{stat.label}</p>
            <div className="flex items-baseline gap-[4px]">
              <span className="text-[48px] font-black leading-none">{stat.value}</span>
              {stat.unit && <span className="text-[18px] font-bold opacity-70">{stat.unit}</span>}
            </div>
            <p className="text-[14px] font-medium mt-[8px] opacity-60">{stat.sub}</p>
          </div>
        ))}
      </div>

      {/* ── Audit List ── */}
      <section className="space-y-[24px]">
        <div className="flex items-center justify-between">
          <h2 className="text-[28px] font-bold uppercase tracking-tight">Latest Security Audits</h2>
          <div className="flex items-center gap-[8px]">
            <div className="w-[10px] h-[10px] border-[2px] border-[#111] rounded-full bg-[#2ECC71]" />
            <span className="text-[12px] font-bold uppercase tracking-[0.1em]">Live Feed</span>
          </div>
        </div>

        {loading ? (
          <div className="grid gap-[24px] md:grid-cols-2">
            {[1, 2, 3, 4].map(i => (
              <div key={i} className="h-[200px] brutal-card-static bg-[#f0f0f0] animate-pulse" />
            ))}
          </div>
        ) : scans.length === 0 ? (
          <div className="brutal-card-static py-[64px] flex flex-col items-center justify-center text-center space-y-[16px]">
            <div className="w-[64px] h-[64px] border-[2px] border-[#111] rounded-[10px] bg-[#FFD600] flex items-center justify-center text-[32px] shadow-[4px_4px_0px_#000]">🏗️</div>
            <h3 className="text-[20px] font-bold uppercase">No data streams detected</h3>
            <p className="text-[16px] text-[#444] font-medium max-w-[400px]">Deploy the Nova Guardian to your GitHub repositories to begin real-time infrastructure auditing.</p>
            <Link href="/install" className="brutal-btn mt-[8px]">Deploy Guardian</Link>
          </div>
        ) : (
          <div className="grid gap-[24px] md:grid-cols-2">
            {scans.map((scan) => (
              <ScanCard key={scan.id} scan={scan} />
            ))}
          </div>
        )}
      </section>

      {error && (
        <div className="brutal-card-static bg-[#FF5252] text-white flex items-center gap-[16px]">
          <span className="text-[24px]">⚠️</span>
          <p className="text-[16px] font-bold uppercase flex-1">Connectivity Issue: {error}</p>
        </div>
      )}
    </div>
  );
}
