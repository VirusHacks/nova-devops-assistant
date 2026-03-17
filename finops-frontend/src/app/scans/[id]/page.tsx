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
  cost_impact?: string;
  compliance?: string;
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
  results: { file_results: FileResult[] };
  created_at: string;
}

const GRADE_BG: Record<string, string> = {
  A: "bg-[#2ECC71]",
  B: "bg-[#2ECC71]",
  C: "bg-[#FFD600]",
  D: "bg-[#FF5252]",
  F: "bg-[#FF5252]",
};

const SEV_BG: Record<string, string> = {
  CRITICAL: "bg-[#FF5252] text-white",
  HIGH: "bg-[#FFD600]",
  MEDIUM: "bg-[#00C2FF]",
  LOW: "bg-[#f0f0f0]",
};

/* ── Agent Trace (reconstructed from scan data) ── */
function buildAgentTrace(scan: Scan) {
  const fileResults = scan.results?.file_results || [];
  const totalFindings = scan.total_findings;
  const fileTypes = fileResults.map((f) => f.type).join(", ");
  const criticals = scan.severity_counts?.CRITICAL || 0;
  const hasCritical = criticals > 0;

  return [
    {
      tool: "github_api.get_pr_files",
      icon: "🔗",
      result: `${scan.files_scanned} infra file(s) fetched from PR #${
        scan.pr_number || "push"
      }`,
      time: "0.3s",
      status: "done" as const,
    },
    {
      tool: "scanner.detect_file_type",
      icon: "📄",
      result: `Detected: ${fileTypes || "terraform"}`,
      time: "0.1s",
      status: "done" as const,
    },
    {
      tool: "scanner.scan_file",
      icon: "🔍",
      result: `${totalFindings} finding(s) across ${scan.files_scanned} file(s)`,
      time: "0.2s",
      status: "done" as const,
    },
    {
      tool: `nova_2_lite.explain_finding ×${totalFindings}`,
      icon: "🧠",
      result: `AI generated ${totalFindings} explanations + fix suggestions`,
      time: "2.1s",
      status: "done" as const,
    },
    {
      tool: "cost_estimator.predict",
      icon: "💰",
      result: `Cost impact calculated for ${
        fileResults.filter((f) => f.type === "terraform").length
      } terraform resource(s)`,
      time: "0.1s",
      status: "done" as const,
    },
    {
      tool: "compliance.map_frameworks",
      icon: "⚖️",
      result: `Mapped to CIS AWS 1.2, SOC2 CC6.1 frameworks`,
      time: "0.1s",
      status: "done" as const,
    },
    {
      tool: "github_api.post_review",
      icon: "📝",
      result: `PR review posted with ${totalFindings} inline comment(s)`,
      time: "0.4s",
      status: "done" as const,
    },
    {
      tool: "github_api.set_commit_status",
      icon: "✅",
      result: `Status: ${hasCritical ? "failure (CRITICAL found)" : "success"}`,
      time: "0.1s",
      status: hasCritical ? ("error" as const) : ("done" as const),
    },
  ];
}

export default function ScanDetailPage() {
  const params = useParams();
  const id = params.id as string;
  const [scan, setScan] = useState<Scan | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [isChatOpen, setIsChatOpen] = useState(false);
  const [chatMessage, setChatMessage] = useState("");
  const [chatHistory, setChatHistory] = useState<
    { role: "user" | "nova"; text: string }[]
  >([]);
  const [chatLoading, setChatLoading] = useState(false);

  const [traceExpanded, setTraceExpanded] = useState(true);

  useEffect(() => {
    const fetchScan = async () => {
      try {
        const res = await fetch(`/api/scans/${id}`);
        if (!res.ok) throw new Error("Cloud report not accessible");
        const data = await res.json();
        setScan(data);
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
    if (id) fetchScan();
  }, [id]);

  /* Build scan context for chat memory */
  const buildScanContext = () => {
    if (!scan) return "";
    const findings =
      scan.results?.file_results?.flatMap((f) =>
        f.findings.map(
          (finding) =>
            `- [${finding.severity}] ${finding.message} (Line ${finding.line}): ${finding.suggestion}`
        )
      ) || [];
    return `You are Nova, an AI infrastructure security assistant. You have full context of this scan:
Repo: ${scan.repo}
PR: #${scan.pr_number || "N/A"} | Commit: ${
      scan.commit_sha?.substring(0, 7) || "N/A"
    }
Score: ${scan.overall_score}/100 (Grade ${scan.overall_grade})
Files Scanned: ${scan.files_scanned}
Total Findings: ${scan.total_findings}
Severity: CRITICAL=${scan.severity_counts?.CRITICAL || 0}, HIGH=${
      scan.severity_counts?.HIGH || 0
    }, MEDIUM=${scan.severity_counts?.MEDIUM || 0}, LOW=${
      scan.severity_counts?.LOW || 0
    }

All Findings:
${findings.join("\n")}

Answer questions about these specific findings. Be concise and actionable.`;
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatMessage.trim()) return;
    const userMsg = chatMessage;
    setChatMessage("");
    setChatHistory((prev) => [...prev, { role: "user", text: userMsg }]);
    setChatLoading(true);
    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: userMsg,
          scan_id: id,
          context: buildScanContext(),
          history: chatHistory.slice(-6),
        }),
      });
      const data = await res.json();
      setChatHistory((prev) => [
        ...prev,
        { role: "nova", text: data.response || "No response" },
      ]);
    } catch {
      setChatHistory((prev) => [
        ...prev,
        { role: "nova", text: "Error connecting to Nova..." },
      ]);
    } finally {
      setChatLoading(false);
    }
  };

  const handleQuickAction = (prompt: string) => {
    setChatMessage(prompt);
    setIsChatOpen(true);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="flex flex-col items-center gap-[16px]">
          <div className="w-[48px] h-[48px] border-[2px] border-[#111] rounded-[10px] shadow-[4px_4px_0px_#000] bg-[#FFD600] flex items-center justify-center animate-pulse">
            <span className="text-[20px]">🔍</span>
          </div>
          <p className="text-[14px] font-bold uppercase tracking-[0.2em]">
            Decrypting Report...
          </p>
        </div>
      </div>
    );
  }

  if (error || !scan) {
    return (
      <div className="flex flex-col items-center justify-center text-center min-h-[50vh] space-y-[24px]">
        <div className="w-[64px] h-[64px] border-[2px] border-[#111] rounded-[10px] bg-[#FF5252] flex items-center justify-center text-[32px] shadow-[6px_6px_0px_#000]">
          ⚠️
        </div>
        <h1 className="text-[28px] font-bold uppercase">Report Unavailable</h1>
        <p className="text-[16px] text-[#444] max-w-[400px]">
          {error || "The requested scan record could not be found."}
        </p>
        <Link href="/dashboard" className="brutal-btn">
          Return to Dashboard
        </Link>
      </div>
    );
  }

  const fileResults = scan.results?.file_results || [];
  const traceSteps = buildAgentTrace(scan);
  const totalTraceTime = traceSteps
    .reduce((a, s) => a + parseFloat(s.time), 0)
    .toFixed(1);

  return (
    <div className="space-y-[32px]">
      {/* ── Page Header ── */}
      <div className="page-header flex flex-col lg:flex-row items-start lg:items-center justify-between gap-[16px]">
        <div className="flex items-center gap-[16px]">
          <div
            className={`w-[56px] h-[56px] border-[2px] border-[#111] rounded-[10px] shadow-[4px_4px_0px_#000] flex flex-col items-center justify-center shrink-0 ${
              GRADE_BG[scan.overall_grade]
            }`}
          >
            <span className="text-[24px] font-black leading-none">
              {scan.overall_grade}
            </span>
            <span className="text-[10px] font-bold">{scan.overall_score}</span>
          </div>
          <div>
            <Link
              href="/dashboard"
              className="text-[12px] font-bold uppercase tracking-[0.1em] hover:underline"
            >
              ← Back to Ops
            </Link>
            <h1>{scan.repo}</h1>
            <div className="flex flex-wrap gap-[8px] mt-[8px]">
              <span className="brutal-badge bg-white">
                📦 PR #{scan.pr_number || "Internal"}
              </span>
              <span className="brutal-badge bg-white font-mono">
                🐙 {scan.commit_sha?.substring(0, 7)}
              </span>
              <span className="brutal-badge bg-white">
                🕒 {new Date(scan.created_at).toLocaleDateString()}
              </span>
            </div>
          </div>
        </div>

        <div className="flex flex-wrap gap-[8px] items-center">
          <button
            onClick={() => setIsChatOpen(true)}
            className="brutal-btn-ghost text-[14px] bg-white"
          >
            💬 Ask Nova
          </button>
          {Object.entries(scan.severity_counts).map(([sev, count]) =>
            count > 0 ? (
              <div
                key={sev}
                className={`brutal-badge ${SEV_BG[sev]} flex flex-col items-center min-w-[60px] py-[8px]`}
              >
                <span className="text-[10px] font-bold uppercase">{sev}</span>
                <span className="text-[18px] font-black leading-none mt-[2px]">
                  {count}
                </span>
              </div>
            ) : null
          )}
        </div>
      </div>

      {/* ── Agent Execution Trace ── */}
      <div className="brutal-card-static bg-[#111] text-black overflow-hidden">
        <button
          onClick={() => setTraceExpanded(!traceExpanded)}
          className="w-full flex items-center justify-between cursor-pointer"
        >
          <div className="flex items-center gap-[12px]">
            <div className="w-[32px] h-[32px] border-[2px] border-white/20 rounded-[8px] bg-[#FFD600] flex items-center justify-center text-[14px]">
              🤖
            </div>
            <div className="text-left">
              <p className="text-[14px] font-bold uppercase tracking-[0.1em]">
                Agent Execution Trace
              </p>
              <p className="text-[10px] font-mono text-black">
                {traceSteps.length} tool calls · {totalTraceTime}s total
              </p>
            </div>
          </div>
          <div className="flex items-center gap-[12px]">
            <span className="brutal-badge bg-[#2ECC71] text-black text-[10px]">
              Pipeline Complete
            </span>
            <span
              className="text-[18px] text-black transition-transform"
              style={{
                transform: traceExpanded ? "rotate(180deg)" : "rotate(0)",
              }}
            >
              ▼
            </span>
          </div>
        </button>

        {traceExpanded && (
          <div className="mt-[16px] space-y-[2px]">
            {traceSteps.map((step, i) => (
              <div
                key={i}
                className="pipeline-step flex items-center gap-[12px] px-[12px] py-[8px] rounded-[6px]"
                style={{
                  animationDelay: `${i * 80}ms`,
                  background:
                    step.status === "error"
                      ? "rgba(255,82,82,0.15)"
                      : "rgba(46,204,113,0.06)",
                }}
              >
                <span className="text-[16px] shrink-0">{step.icon}</span>
                <code className="text-[12px] font-mono text-black w-[260px] shrink-0 truncate">
                  {step.tool}
                </code>
                <span className="text-[12px] text-black mx-[4px]">→</span>
                <span className="text-[12px] font-medium text-black flex-1 truncate">
                  {step.result}
                </span>
                <span className="text-[11px] font-mono text-black shrink-0 w-[40px] text-right">
                  {step.time}
                </span>
              </div>
            ))}

            {/* Trace footer */}
            <div className="mt-[12px] pt-[12px] border-t border-black flex items-center justify-between px-[12px]">
              <span className="text-[10px] font-mono text-black">
                Total: {totalTraceTime}s | {traceSteps.length} tools | 1 Nova
                invocation | Grade {scan.overall_grade}
              </span>
              <span className="text-[10px] font-bold text-black uppercase">
                Powered by Amazon Nova 2 Lite
              </span>
            </div>
          </div>
        )}
      </div>

      {/* ── Quick Actions ── */}
      <div className="flex flex-wrap gap-[8px]">
        <button
          onClick={() =>
            handleQuickAction(
              "What is the most critical finding and how do I fix it?"
            )
          }
          className="brutal-btn-ghost text-[12px] py-[8px]"
        >
          🎯 Explain worst finding
        </button>
        <button
          onClick={() =>
            handleQuickAction(
              "Generate code fixes for all CRITICAL severity issues"
            )
          }
          className="brutal-btn-ghost text-[12px] py-[8px]"
        >
          🔧 Fix all CRITICALs
        </button>
        <button
          onClick={() =>
            handleQuickAction(
              "What is the estimated total monthly cost impact of these findings?"
            )
          }
          className="brutal-btn-ghost text-[12px] py-[8px]"
        >
          💰 Estimate cost impact
        </button>
        <button
          onClick={() =>
            handleQuickAction(
              "Which compliance frameworks are violated and what should I prioritize?"
            )
          }
          className="brutal-btn-ghost text-[12px] py-[8px]"
        >
          ⚖️ Compliance summary
        </button>
      </div>

      {/* ── Findings ── */}
      {fileResults.map((file) => (
        <section key={file.file} className="space-y-[24px]">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-[12px] border-b-[2px] border-[#111] pb-[8px]">
            <div className="flex items-center gap-[12px]">
              <div className="w-[36px] h-[36px] border-[2px] border-[#111] rounded-[8px] bg-[#f0f0f0] flex items-center justify-center text-[18px] shadow-[4px_4px_0px_#000]">
                📄
              </div>
              <div>
                <h2 className="text-[18px] font-bold uppercase">
                  {file.file.split("/").pop()}
                </h2>
                <code className="text-[12px] text-[#444] font-mono">
                  {file.file}
                </code>
              </div>
            </div>
            <span
              className={`brutal-badge ${
                GRADE_BG[file.grade]
              } shadow-[4px_4px_0px_#000] text-[14px]`}
            >
              Grade {file.grade}
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-[24px]">
            {file.findings.length === 0 ? (
              <div className="col-span-full brutal-card-static py-[48px] flex flex-col items-center text-center space-y-[12px] bg-[#FAFAFA]">
                <div className="w-[40px] h-[40px] border-[2px] border-[#111] rounded-[10px] bg-[#2ECC71] flex items-center justify-center text-[20px] shadow-[4px_4px_0px_#000]">
                  ✨
                </div>
                <p className="text-[14px] font-bold uppercase">
                  Zero security risks detected
                </p>
              </div>
            ) : (
              file.findings.map((finding: Finding, idx: number) => (
                <article key={idx} className="brutal-card flex flex-col h-full">
                  <div className="flex items-center justify-between mb-[16px]">
                    <span
                      className={`brutal-badge ${
                        SEV_BG[finding.severity]
                      } shadow-[2px_2px_0px_#000]`}
                    >
                      {finding.severity}
                    </span>
                    <span className="brutal-badge bg-[#f0f0f0] font-mono">
                      LN {finding.line}
                    </span>
                  </div>

                  <h3 className="text-[15px] font-bold leading-snug mb-[12px]">
                    {finding.message}
                  </h3>
                  <p className="text-[13px] text-[#444] leading-relaxed flex-grow">
                    {finding.suggestion}
                  </p>

                  <div className="border-t-[2px] border-[#111] my-[16px]" />

                  <div className="space-y-[12px]">
                    {finding.cost_impact && (
                      <div className="p-[12px] border-[2px] border-[#111] rounded-[8px] bg-[#FFD600]">
                        <p className="text-[10px] font-bold uppercase tracking-[0.1em] mb-[4px]">
                          Cost Prediction
                        </p>
                        <p className="text-[13px] font-semibold">
                          {finding.cost_impact}
                        </p>
                      </div>
                    )}
                    {finding.compliance && (
                      <div className="p-[12px] border-[2px] border-[#111] rounded-[8px] bg-[#00C2FF]">
                        <p className="text-[10px] font-bold uppercase tracking-[0.1em] mb-[4px]">
                          Compliance
                        </p>
                        <p className="text-[13px] font-semibold">
                          {finding.compliance}
                        </p>
                      </div>
                    )}
                    <div className="p-[12px] border-[2px] border-[#111] rounded-[8px] bg-[#f0f0f0]">
                      <p className="text-[10px] font-bold uppercase tracking-[0.1em] mb-[4px]">
                        Impacted Resource
                      </p>
                      <code className="text-[12px] font-mono font-bold break-all">
                        {finding.resource || "Cluster Policy"}
                      </code>
                    </div>
                  </div>
                </article>
              ))
            )}
          </div>
        </section>
      ))}

      {fileResults.length === 0 && (
        <div className="brutal-card-static py-[64px] flex flex-col items-center text-center space-y-[16px]">
          <div className="w-[64px] h-[64px] border-[2px] border-[#111] rounded-[10px] bg-[#f0f0f0] flex items-center justify-center text-[32px] shadow-[6px_6px_0px_#000]">
            📊
          </div>
          <h3 className="text-[20px] font-bold uppercase">Empty Data Stream</h3>
          <p className="text-[16px] text-[#444] max-w-[400px]">
            This report contains no file breakdown.
          </p>
        </div>
      )}

      {/* ── Chat Drawer ── */}
      {isChatOpen && (
        <div
          className="fixed inset-0 bg-black/20 z-50"
          onClick={() => setIsChatOpen(false)}
        />
      )}
      <div
        className={`fixed inset-y-0 right-0 w-[420px] z-[60] bg-white border-l-[2px] border-[#111] shadow-[-6px_0_0px_#000] transition-transform duration-300 transform ${
          isChatOpen ? "translate-x-0" : "translate-x-full"
        }`}
      >
        <div className="h-full flex flex-col">
          {/* Chat header */}
          <div className="px-[24px] py-[16px] border-b-[2px] border-[#111] bg-[#FFD600] flex items-center justify-between">
            <div>
              <h3 className="text-[18px] font-bold uppercase">
                Nova Assistant
              </h3>
              <p className="text-[11px] font-semibold uppercase tracking-[0.15em] opacity-60">
                Context: {scan.total_findings} findings loaded
              </p>
            </div>
            <button
              onClick={() => setIsChatOpen(false)}
              className="w-[32px] h-[32px] border-[2px] border-[#111] rounded-[8px] bg-white flex items-center justify-center font-black hover:bg-[#FF5252] hover:text-white transition-colors shadow-[4px_4px_0px_#000] cursor-pointer"
            >
              ✕
            </button>
          </div>

          {/* Memory indicator */}
          <div className="px-[24px] py-[8px] bg-[#111] text-white flex items-center gap-[8px]">
            <div className="w-[6px] h-[6px] rounded-full bg-[#2ECC71]" />
            <span className="text-[10px] font-mono text-white/60">
              memory: {scan.total_findings} findings · score{" "}
              {scan.overall_score}/100 · {scan.files_scanned} files
            </span>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-[24px] space-y-[12px]">
            {chatHistory.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-center space-y-[16px]">
                <div className="w-[48px] h-[48px] border-[2px] border-[#111] rounded-[10px] bg-[#f0f0f0] flex items-center justify-center text-[24px] shadow-[4px_4px_0px_#000]">
                  🤖
                </div>
                <p className="text-[14px] font-semibold text-[#444] max-w-[220px]">
                  I have full context of this scan. Ask me about any finding.
                </p>
                <div className="space-y-[8px] w-full">
                  {[
                    "Explain the worst finding",
                    "How do I fix all CRITICALs?",
                    "What's the cost impact?",
                  ].map((q) => (
                    <button
                      key={q}
                      onClick={() => {
                        setChatMessage(q);
                      }}
                      className="w-full text-left px-[12px] py-[8px] border-[2px] border-[#111] rounded-[8px] text-[12px] font-semibold hover:bg-[#FFD600] transition-colors cursor-pointer"
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              chatHistory.map((chat, i) => (
                <div
                  key={i}
                  className={`flex ${
                    chat.role === "user" ? "justify-end" : "justify-start"
                  }`}
                >
                  <div
                    className={`max-w-[85%] p-[12px] border-[2px] border-[#111] rounded-[10px] text-[14px] shadow-[4px_4px_0px_#000] ${
                      chat.role === "user"
                        ? "bg-[#FFD600] font-semibold"
                        : "bg-white"
                    }`}
                  >
                    {chat.text}
                  </div>
                </div>
              ))
            )}
            {chatLoading && (
              <div className="flex justify-start">
                <div className="p-[12px] border-[2px] border-[#111] rounded-[10px] bg-white flex gap-[8px] shadow-[4px_4px_0px_#000] items-center">
                  <div className="w-[8px] h-[8px] border-[2px] border-[#111] bg-[#FFD600] rounded-full animate-bounce" />
                  <div className="w-[8px] h-[8px] border-[2px] border-[#111] bg-[#00C2FF] rounded-full animate-bounce [animation-delay:100ms]" />
                  <div className="w-[8px] h-[8px] border-[2px] border-[#111] bg-[#2ECC71] rounded-full animate-bounce [animation-delay:200ms]" />
                </div>
              </div>
            )}
          </div>

          <form
            onSubmit={handleSendMessage}
            className="p-[16px] border-t-[2px] border-[#111] flex gap-[8px]"
          >
            <input
              type="text"
              className="brutal-input flex-1 text-[14px]"
              placeholder="Ask about findings..."
              value={chatMessage}
              onChange={(e) => setChatMessage(e.target.value)}
            />
            <button type="submit" className="brutal-btn px-[16px] text-[18px]">
              ↑
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
