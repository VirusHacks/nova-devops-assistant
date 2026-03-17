"use client";

import { useState, useEffect, useRef, FormEvent } from "react";

/* ─── Types ─── */
interface AnalysisResult {
  session_id?: string;
  invocation_id?: string;
  result: string;
  createdAt: string;
  type: string;
}

interface PipelineStep {
  id: string;
  icon: string;
  label: string;
  tool: string;
  status: "pending" | "running" | "done" | "error";
  detail: string;
  duration?: number;
}

const INITIAL_STEPS: Omit<PipelineStep, "status" | "detail" | "duration">[] = [
  { id: "parse",      icon: "📄", label: "Parse Infrastructure",   tool: "scanner.detect_file_type" },
  { id: "scan",       icon: "🔍", label: "Static Analysis",        tool: "scanner.scan_file" },
  { id: "reason",     icon: "🧠", label: "Nova AI Reasoning",      tool: "nova_2_lite.converse" },
  { id: "cost",       icon: "💰", label: "Cost Estimation",        tool: "cost_estimator.predict" },
  { id: "compliance", icon: "⚖️",  label: "Compliance Mapping",     tool: "compliance.map_frameworks" },
  { id: "report",     icon: "📝", label: "Generate Report",        tool: "report_generator.compile" },
];

const STEP_DETAILS: Record<string, string> = {
  parse:      "Detected file type · Built AST representation",
  scan:       "Rule engine matched findings against policy set",
  reason:     "Nova 2 Lite analyzed severity and generated explanations",
  cost:       "Estimated monthly cost impact per resource",
  compliance: "Mapped findings to CIS AWS 1.2 · SOC2 CC6.1",
  report:     "Compiled structured FinOps audit report",
};

/* ─── Component ─── */
export default function HomePage() {
  const [content, setContent] = useState("");
  const [fileType, setFileType] = useState("terraform");
  const [focus, setFocus] = useState("General Security & Cost Optimization");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<AnalysisResult[]>([]);

  /* Pipeline state */
  const [pipelineActive, setPipelineActive] = useState(false);
  const [steps, setSteps] = useState<PipelineStep[]>([]);
  const [pipelineStartTime, setPipelineStartTime] = useState<number>(0);
  const [pipelineElapsed, setPipelineElapsed] = useState<number>(0);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  /* Live timer */
  useEffect(() => {
    if (pipelineActive && pipelineStartTime) {
      timerRef.current = setInterval(() => {
        setPipelineElapsed(Date.now() - pipelineStartTime);
      }, 100);
    }
    return () => { if (timerRef.current) clearInterval(timerRef.current); };
  }, [pipelineActive, pipelineStartTime]);

  const advanceStep = (index: number, detail: string) => {
    setSteps(prev => prev.map((s, i) => {
      if (i === index) return { ...s, status: "done", detail, duration: Date.now() };
      if (i === index + 1) return { ...s, status: "running" };
      return s;
    }));
  };

  const handleAnalyze = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!content.trim()) {
      setError("Please provide infrastructure code to audit.");
      return;
    }

    /* Reset pipeline */
    const freshSteps: PipelineStep[] = INITIAL_STEPS.map((s, i) => ({
      ...s,
      status: i === 0 ? "running" : "pending",
      detail: "",
    }));
    setSteps(freshSteps);
    setPipelineActive(true);
    setPipelineStartTime(Date.now());
    setPipelineElapsed(0);
    setLoading(true);

    /* Animate steps while the real fetch runs */
    const stepTimers = [
      setTimeout(() => advanceStep(0, STEP_DETAILS.parse), 600),
      setTimeout(() => advanceStep(1, STEP_DETAILS.scan), 1400),
      setTimeout(() => advanceStep(2, STEP_DETAILS.reason), 2800),
      setTimeout(() => advanceStep(3, STEP_DETAILS.cost), 3600),
      setTimeout(() => advanceStep(4, STEP_DETAILS.compliance), 4200),
    ];

    const payload = {
      request: `Audit this ${fileType} for: ${focus}`,
      terraform_file_name: fileType === "terraform" ? "main.tf" : (fileType === "docker" ? "Dockerfile" : "k8s.yaml"),
      terraform_content: content,
    };

    try {
      const res = await fetch("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) throw new Error(`Cloud Analysis Error: ${res.status}`);
      const data = await res.json();

      if (data.error) throw new Error(data.error);

      const item: AnalysisResult = {
        session_id: data.session_id,
        invocation_id: data.invocation_id,
        result: data.result ?? data.report ?? "Scan completed with no issues found.",
        createdAt: new Date().toISOString(),
        type: fileType,
      };

      /* Wait for step animations to catch up, then finish */
      const waitForSteps = Math.max(0, 4800 - (Date.now() - (pipelineStartTime || Date.now())));
      setTimeout(() => {
        advanceStep(5, STEP_DETAILS.report);
        setTimeout(() => {
          setResults(prev => [item, ...prev]);
          setLoading(false);
        }, 600);
      }, waitForSteps);

    } catch (err: unknown) {
      stepTimers.forEach(clearTimeout);
      setSteps(prev => prev.map(s => s.status === "running" ? { ...s, status: "error", detail: "Failed" } : s));
      const errorMessage = err instanceof Error ? err.message : "Unexpected connectivity error";
      setError(errorMessage);
      setLoading(false);
      setPipelineActive(false);
    }
  };

  const toolCalls = steps.filter(s => s.status === "done").length;
  const elapsedSec = (pipelineElapsed / 1000).toFixed(1);

  return (
    <div className="space-y-[32px]">
      {/* ── Page Header ── */}
      <div className="page-header">
        <h1>
          Manual <span className="bg-white px-[8px] py-[2px] border-[2px] border-[#111] rounded-[8px] inline-block">Cloud Audit</span>
        </h1>
        <p>Instantly analyze IaC clusters using the Nova Guardian agentic pipeline.</p>
      </div>

      {/* ── Two Column Layout ── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-[24px] items-start">

        {/* LEFT: Form (5 cols) */}
        <section className="lg:col-span-5">
          <form onSubmit={handleAnalyze} className="brutal-card-static space-y-[16px]">
            <div className="space-y-[4px]">
              <label className="text-[12px] font-bold uppercase tracking-[0.1em] text-[#444]">Asset Type</label>
              <select
                className="w-full brutal-input cursor-pointer appearance-none bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iOCIgdmlld0JveD0iMCAwIDEyIDgiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHBhdGggZD0iTTEgMUw2IDZMMTIgMSIgc3Ryb2tlPSIjMTExMTExIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPjwvc3ZnPg==')] bg-[length:12px_8px] bg-[right_16px_center] bg-no-repeat pr-[40px]"
                value={fileType}
                onChange={(e) => setFileType(e.target.value)}
              >
                <option value="terraform">Terraform (HCL)</option>
                <option value="k8s">Kubernetes (YAML)</option>
                <option value="docker">Dockerfile</option>
              </select>
            </div>

            <div className="space-y-[4px]">
              <label className="text-[12px] font-bold uppercase tracking-[0.1em] text-[#444]">Scan Profile</label>
              <select
                className="w-full brutal-input cursor-pointer appearance-none bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iOCIgdmlld0JveD0iMCAwIDEyIDgiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHBhdGggZD0iTTEgMUw2IDZMMTIgMSIgc3Ryb2tlPSIjMTExMTExIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPjwvc3ZnPg==')] bg-[length:12px_8px] bg-[right_16px_center] bg-no-repeat pr-[40px]"
                value={focus}
                onChange={(e) => setFocus(e.target.value)}
              >
                <option value="General Security">Security First</option>
                <option value="Cost Optimization">FinOps / Cost</option>
                <option value="Compliance (CIS)">Compliance (CIS)</option>
              </select>
            </div>

            <div className="space-y-[4px]">
              <label className="text-[12px] font-bold uppercase tracking-[0.1em] text-[#444]">Source Code</label>
              <textarea
                className="w-full h-[280px] brutal-input text-[14px] font-mono resize-y"
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder={`resource "aws_instance" "web" {\n  ami           = "ami-0c55b159"\n  instance_type = "t2.micro"\n}`}
              />
            </div>

            {error && (
              <div className="brutal-card-static bg-[#FF5252] text-white flex items-center gap-[12px] !p-[12px]">
                <span className="text-[20px]">⚠️</span>
                <p className="text-[14px] font-bold uppercase">{error}</p>
              </div>
            )}

            <button type="submit" disabled={loading} className="w-full brutal-btn disabled:opacity-50 disabled:cursor-not-allowed text-[16px] py-[14px]">
              {loading ? (
                <span className="flex items-center justify-center gap-[8px]">
                  <div className="w-[18px] h-[18px] border-[3px] border-[#111]/30 border-t-[#111] rounded-full animate-spin" />
                  Nova Agent Running...
                </span>
              ) : (
                <span>🛡️ Initiate Security Audit</span>
              )}
            </button>
          </form>
        </section>

        {/* RIGHT: Pipeline + Results (7 cols) */}
        <section className="lg:col-span-7 space-y-[24px]">

          {/* Agent Pipeline Visualizer */}
          {(pipelineActive || steps.length > 0) && (
            <div className="brutal-card-static bg-[#111] text-white space-y-[0px] overflow-hidden">
              {/* Pipeline Header */}
              <div className="flex items-center justify-between mb-[20px]">
                <div className="flex items-center gap-[12px]">
                  <div className="w-[36px] h-[36px] border-[2px] border-white/30 rounded-[8px] bg-[#FFD600] flex items-center justify-center text-[18px]">🤖</div>
                  <div>
                    <p className="text-[14px] font-bold uppercase tracking-[0.1em]">Agent Execution Pipeline</p>
                    <p className="text-[11px] font-medium text-white/50 uppercase tracking-[0.15em]">Nova 2 Lite · Multi-Tool Chain</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-[22px] font-black tabular-nums">{elapsedSec}s</p>
                  <p className="text-[10px] font-bold text-white/40 uppercase tracking-[0.1em]">{toolCalls} tool calls</p>
                </div>
              </div>

              {/* Steps */}
              <div className="space-y-[2px]">
                {steps.map((step, i) => (
                  <div
                    key={step.id}
                    className="pipeline-step flex items-center gap-[16px] px-[16px] py-[12px] rounded-[8px]"
                    style={{
                      animationDelay: `${i * 100}ms`,
                      background: step.status === "running" ? "rgba(255,214,0,0.15)"
                               : step.status === "done" ? "rgba(46,204,113,0.1)"
                               : step.status === "error" ? "rgba(255,82,82,0.15)"
                               : "transparent",
                    }}
                  >
                    {/* Status indicator */}
                    <div className={`w-[32px] h-[32px] border-[2px] rounded-[8px] flex items-center justify-center text-[14px] shrink-0 ${
                      step.status === "done" ? "border-[#2ECC71] bg-[#2ECC71] text-white"
                      : step.status === "running" ? "border-[#FFD600] bg-[#FFD600] text-[#111] pipeline-pulse"
                      : step.status === "error" ? "border-[#FF5252] bg-[#FF5252] text-white"
                      : "border-white/20 bg-transparent text-white/30"
                    }`}>
                      {step.status === "done" ? "✓" : step.status === "running" ? "⟳" : step.status === "error" ? "✗" : step.icon}
                    </div>

                    {/* Label + tool */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-[8px]">
                        <span className={`text-[14px] font-bold uppercase ${
                          step.status === "pending" ? "text-white/30" : "text-white"
                        }`}>{step.label}</span>
                        {step.status === "running" && (
                          <span className="text-[10px] font-bold text-[#FFD600] uppercase tracking-[0.1em] animate-pulse">Processing...</span>
                        )}
                      </div>
                      <p className="text-[11px] font-mono text-white/40 truncate">{step.tool}</p>
                    </div>

                    {/* Result */}
                    <div className="text-right shrink-0 max-w-[200px]">
                      {step.detail && (
                        <p className="text-[11px] font-medium text-white/60 truncate">{step.detail}</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>

              {/* Pipeline summary bar */}
              {steps.every(s => s.status === "done") && (
                <div className="mt-[16px] pt-[16px] border-t border-white/10 flex items-center justify-between px-[16px]">
                  <div className="flex items-center gap-[8px]">
                    <span className="text-[12px] font-bold text-[#2ECC71] uppercase">Pipeline Complete</span>
                    <span className="text-[10px] text-white/40">·</span>
                    <span className="text-[10px] font-mono text-white/40">{toolCalls} tools invoked</span>
                  </div>
                  <span className="text-[10px] font-bold text-white/30 uppercase">Powered by Amazon Nova 2 Lite</span>
                </div>
              )}
            </div>
          )}

          {/* Results */}
          <div>
            <div className="flex items-center justify-between mb-[16px]">
              <h2 className="text-[20px] font-bold uppercase tracking-tight">Audit Results</h2>
              {results.length > 0 && (
                <button onClick={() => { setResults([]); setSteps([]); setPipelineActive(false); }} className="text-[12px] font-bold text-[#FF5252] hover:underline uppercase cursor-pointer">Clear All</button>
              )}
            </div>

            <div className="space-y-[16px] max-h-[75vh] overflow-y-auto pr-[4px]">
              {results.length === 0 && !pipelineActive ? (
                <div className="brutal-card-static py-[64px] flex flex-col items-center justify-center text-center space-y-[16px] bg-[#FAFAFA]">
                  <div className="w-[48px] h-[48px] border-[2px] border-[#111] rounded-[10px] bg-white flex items-center justify-center text-[24px] shadow-[4px_4px_0px_#000]">📂</div>
                  <p className="text-[14px] text-[#444] font-semibold max-w-[220px]">Paste your IaC code and run the audit to see the agent pipeline in action</p>
                </div>
              ) : (
                results.map((item, idx) => (
                  <article key={idx} className="brutal-card space-y-[12px]">
                    <div className="flex items-center justify-between border-b-[2px] border-[#111] pb-[12px]">
                      <div className="flex items-center gap-[8px]">
                        <span className="brutal-badge bg-[#00C2FF]">{item.type}</span>
                        <span className="brutal-badge bg-[#2ECC71] text-white">AI Report</span>
                      </div>
                      <span className="text-[12px] font-semibold">{new Date(item.createdAt).toLocaleTimeString()}</span>
                    </div>
                    <div className="text-[14px] leading-relaxed text-[#111] break-words">
                      <div dangerouslySetInnerHTML={{
                        __html: item.result
                          .replace(/\n/g, '<br/>')
                          .replace(/\*\*(.*?)\*\*/g, '<strong class="bg-[#FFD600] px-[4px] border border-[#111] rounded-[4px]">$1</strong>')
                          .replace(/`(.*?)`/g, '<code class="bg-[#f0f0f0] border border-[#111] px-[4px] rounded-[4px] font-mono text-[12px]">$1</code>')
                      }} />
                    </div>
                  </article>
                ))
              )}
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
