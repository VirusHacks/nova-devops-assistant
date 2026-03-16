"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";

interface Finding {
  id: string;
  severity: string;
  category: string;
  line: number;
  message: string;
  suggestion: string;
  resource: string;
}

interface FileResult {
  file: string;
  type: string;
  findings: Finding[];
  score: number;
  grade: string;
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
  severity_counts: Record<string, number>;
  results: {
    file_results: FileResult[];
  };
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

const SEVERITY_LABEL: Record<string, string> = {
  CRITICAL: "text-red-400 bg-red-500/10 border-red-500/20",
  HIGH: "text-orange-400 bg-orange-500/10 border-orange-500/20",
  MEDIUM: "text-yellow-400 bg-yellow-500/10 border-yellow-500/20",
  LOW: "text-blue-400 bg-blue-500/10 border-blue-500/20",
};

export default function ScanDetailPage() {
  const params = useParams();
  const id = params.id;
  const [scan, setScan] = useState<Scan | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchScan = async () => {
      try {
        const res = await fetch(`/api/scans/${id}`);
        if (!res.ok) throw new Error("Cloud report not accessible");
        const data = await res.json();
        setScan(data);
      } catch (e: any) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    };
    if (id) fetchScan();
  }, [id]);

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center bg-slate-950">
        <div className="flex flex-col items-center gap-4">
            <div className="w-12 h-12 border-4 border-slate-800 border-t-emerald-500 rounded-full animate-spin"></div>
            <p className="text-[10px] font-black text-slate-500 uppercase tracking-[0.3em]">Decrypting Report...</p>
        </div>
      </div>
    );
  }

  if (error || !scan) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-8 text-center space-y-6 bg-slate-950">
        <div className="w-20 h-20 rounded-full bg-red-500/10 flex items-center justify-center text-4xl">⚠️</div>
        <div className="space-y-2">
            <h1 className="text-2xl font-black uppercase">Report Connectivity Failure</h1>
            <p className="text-slate-500 max-w-sm mx-auto text-sm">{error || "The requested scan record could not be found in the local database."}</p>
        </div>
        <Link href="/dashboard" className="rounded-xl border border-slate-800 bg-slate-900 px-6 py-2.5 text-xs font-black uppercase tracking-widest hover:border-emerald-500 transition-colors">
          Return to Dashboard
        </Link>
      </div>
    );
  }

  const fileResults = scan.results?.file_results || [];

  return (
    <div className="flex-1 bg-slate-950 overflow-y-auto">
      {/* Hero Header */}
      <section className="relative h-64 border-b border-slate-800 flex items-end overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-t from-slate-950 to-transparent"></div>
        <div className="absolute top-0 right-0 p-8 opacity-10">
            <span className="text-[150px] font-black leading-none uppercase tracking-tighter select-none">SCAN</span>
        </div>
        
        <div className="relative w-full max-w-6xl mx-auto px-8 pb-10 flex items-end justify-between gap-8">
            <div className="flex items-center gap-6">
                <div className={`w-24 h-24 rounded-3xl border-2 flex flex-col items-center justify-center ${GRADE_COLOR[scan.overall_grade]}`}>
                    <span className="text-4xl font-black leading-none">{scan.overall_grade}</span>
                    <span className="text-[10px] uppercase font-bold tracking-widest opacity-60 mt-1">{scan.overall_score}</span>
                </div>
                <div className="space-y-2">
                    <Link href="/dashboard" className="text-[10px] font-black text-emerald-500 uppercase tracking-[0.2em] hover:opacity-80 transition-opacity">← BACK TO OPS</Link>
                    <h1 className="text-3xl font-black tracking-tight uppercase leading-none">{scan.repo}</h1>
                    <div className="flex items-center gap-4 text-xs font-medium text-slate-500">
                        <span className="flex items-center gap-1.5"><span className="text-lg">📦</span> PR #{scan.pr_number || "Internal"}</span>
                        <span className="w-1 h-1 rounded-full bg-slate-700"></span>
                        <span className="flex items-center gap-1.5 font-mono"><span className="text-lg">🐙</span> {scan.commit_sha?.substring(0, 7)}</span>
                        <span className="w-1 h-1 rounded-full bg-slate-700"></span>
                        <span className="flex items-center gap-1.5"><span className="text-lg">🕒</span> {new Date(scan.created_at).toLocaleDateString()}</span>
                    </div>
                </div>
            </div>

            <div className="hidden lg:flex gap-3">
                {Object.entries(scan.severity_counts).map(([sev, count]) => (
                    count > 0 && (
                        <div key={sev} className={`px-4 py-2.5 rounded-2xl border ${SEVERITY_LABEL[sev]} text-center min-w-[80px]`}>
                            <p className="text-[9px] font-black uppercase tracking-widest opacity-60">{sev}</p>
                            <p className="text-lg font-black leading-none mt-1">{count}</p>
                        </div>
                    )
                ))}
            </div>
        </div>
      </section>

      {/* Findings Content */}
      <main className="max-w-6xl mx-auto px-8 py-12 space-y-12">
        {fileResults.map((file) => (
          <div key={file.file} className="space-y-6">
            <header className="flex items-center justify-between border-b border-slate-900 pb-4">
                <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-slate-900 flex items-center justify-center text-lg">📄</div>
                    <div>
                        <h2 className="text-xl font-bold tracking-tight text-slate-200">{file.file.split('/').pop()}</h2>
                        <code className="text-[10px] text-slate-500 font-mono italic">{file.file}</code>
                    </div>
                </div>
                <div className={`px-4 py-1 rounded-full border text-xs font-black uppercase tracking-widest ${GRADE_COLOR[file.grade]}`}>
                    Grade {file.grade}
                </div>
            </header>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {file.findings.length === 0 ? (
                    <div className="col-span-full py-12 text-center border-2 border-dashed border-slate-900 rounded-3xl space-y-3">
                        <div className="text-4xl">✨</div>
                        <p className="text-xs font-black text-slate-600 uppercase tracking-widest">Zero security risks detected in this asset.</p>
                    </div>
                ) : (
                    file.findings.map((finding, idx) => (
                        <article key={idx} className="group p-6 rounded-3xl border border-slate-800 bg-slate-900/20 hover:border-slate-500/30 transition-all flex flex-col h-full relative overflow-hidden">
                            <div className="flex items-center justify-between mb-4">
                                <span className={`px-2 py-0.5 rounded-full border text-[9px] font-black uppercase tracking-widest ${SEVERITY_LABEL[finding.severity]}`}>
                                    {finding.severity}
                                </span>
                                <span className="text-[10px] font-mono text-slate-600">LN {finding.line}</span>
                            </div>
                            
                            <h3 className="text-lg font-bold text-slate-100 leading-snug mb-3">{finding.message}</h3>
                            <p className="text-xs text-slate-400 leading-relaxed mb-6 flex-grow">{finding.suggestion}</p>

                            <div className="mt-auto space-y-3">
                                <div className="p-3 rounded-xl bg-slate-950 border border-slate-800/50">
                                    <p className="text-[9px] font-black text-slate-600 uppercase tracking-widest mb-1.5">Impacted Resource</p>
                                    <code className="text-[11px] text-pink-400/80 font-mono break-all">{finding.resource || "Cluster Policy"}</code>
                                </div>
                                <div className="p-3 rounded-xl bg-emerald-500/5 border border-emerald-500/10">
                                    <p className="text-[9px] font-black text-emerald-500/60 uppercase tracking-widest mb-1">AI Recommendation</p>
                                    <p className="text-[11px] text-slate-300 font-medium">Mitigate via infrastructure update.</p>
                                </div>
                            </div>
                        </article>
                    ))
                )}
            </div>
          </div>
        ))}
        
        {fileResults.length === 0 && (
             <div className="py-32 text-center space-y-6">
                <div className="text-6xl grayscale opacity-20">📊</div>
                <div className="space-y-2">
                    <h3 className="text-xl font-bold uppercase tracking-tight">Empty Data Stream</h3>
                    <p className="text-slate-500 text-sm max-w-xs mx-auto">This report contains no file breakdown. This usually happens when the PR contains no supported IaC assets.</p>
                </div>
            </div>
        )}
      </main>
    </div>
  );
}
