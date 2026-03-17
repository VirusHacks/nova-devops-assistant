"use client";

import Link from "next/link";

const AGENTS = [
  {
    role: "Planner",
    icon: "🗺️",
    color: "bg-[#FFD600]",
    desc: "Receives webhook events, identifies infra files, and orchestrates the full scan pipeline.",
    tools: ["github_api.get_pr_files", "scanner.detect_file_type"],
  },
  {
    role: "Scanner",
    icon: "🔍",
    color: "bg-[#00C2FF]",
    desc: "Multi-engine static analysis across Terraform, K8s YAML, Dockerfiles, and GitHub Actions.",
    tools: ["scanner.scan_file", "scanner.run_rules"],
  },
  {
    role: "Evaluator",
    icon: "🧠",
    color: "bg-[#FF5252]",
    desc: "Amazon Nova 2 Lite reasons about each finding — explains the risk, writes a code fix, and estimates impact.",
    tools: ["nova_2_lite.converse", "cost_estimator.predict", "compliance.map"],
  },
  {
    role: "Reporter",
    icon: "📝",
    color: "bg-[#2ECC71]",
    desc: "Compiles the structured report, posts inline PR review comments, and sets the commit status.",
    tools: [
      "github_api.post_review",
      "github_api.set_commit_status",
      "db.save_scan",
    ],
  },
];

const TOOLS = [
  {
    name: "scanner.scan_file",
    type: "Static Analysis",
    desc: "Pattern-match rules against infrastructure AST",
    color: "bg-[#00C2FF]",
  },
  {
    name: "nova_2_lite.converse",
    type: "AI Reasoning",
    desc: "AWS Bedrock Converse API with extended thinking",
    color: "bg-[#FFD600]",
  },
  {
    name: "github_api.*",
    type: "GitHub Integration",
    desc: "PR files, reviews, commit status, inline comments",
    color: "bg-[#f0f0f0]",
  },
  {
    name: "cost_estimator.predict",
    type: "FinOps",
    desc: "Estimate monthly cost impact per resource",
    color: "bg-[#2ECC71]",
  },
  {
    name: "compliance.map",
    type: "Compliance",
    desc: "Map findings to CIS AWS 1.2, SOC2, FinOps frameworks",
    color: "bg-[#00C2FF]",
  },
  {
    name: "db.save_scan",
    type: "Persistence",
    desc: "SQLite storage for scan history and dashboard",
    color: "bg-[#f0f0f0]",
  },
];

const PIPELINE = [
  {
    step: "1",
    label: "Webhook Received",
    desc: "GitHub sends a PR event to the Guardian webhook server.",
    icon: "🔗",
    color: "bg-[#FFD600]",
  },
  {
    step: "2",
    label: "File Discovery",
    desc: "The Planner agent fetches changed files and filters to supported infra types.",
    icon: "📄",
    color: "bg-[#FFD600]",
  },
  {
    step: "3",
    label: "Static Scan",
    desc: "The Scanner agent runs rule engines across all detected file types in parallel.",
    icon: "🔍",
    color: "bg-[#00C2FF]",
  },
  {
    step: "4",
    label: "Nova Reasoning",
    desc: "Each finding is sent to Nova 2 Lite for severity analysis, explanation, and code fix generation.",
    icon: "🧠",
    color: "bg-[#FF5252]",
  },
  {
    step: "5",
    label: "Cost & Compliance",
    desc: "Financial impact is estimated and findings are mapped to compliance frameworks.",
    icon: "💰",
    color: "bg-[#2ECC71]",
  },
  {
    step: "6",
    label: "PR Review",
    desc: "The Reporter posts inline comments with fixes and sets the commit status (pass/fail).",
    icon: "📝",
    color: "bg-[#2ECC71]",
  },
];

export default function DocsPage() {
  return (
    <div className="space-y-[32px]">
      {/* ── Header ── */}
      <div className="page-header">
        <h1>
          Agentic{" "}
          <span className="bg-white px-[8px] py-[2px] border-[2px] border-[#111] rounded-[8px] inline-block">
            Architecture
          </span>
        </h1>
        <p className="max-w-[600px]">
          Nova Guardian uses a multi-agent pipeline powered by Amazon Nova 2
          Lite to scan, reason about, and auto-fix infrastructure security
          issues.
        </p>
      </div>

      {/* ── Agent Roles (4 cards) ── */}
      <section className="space-y-[16px]">
        <h2 className="text-[22px] font-bold uppercase tracking-tight">
          Agent Roles
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-[16px]">
          {AGENTS.map((agent) => (
            <div key={agent.role} className="brutal-card flex flex-col">
              <div className="flex items-center gap-[12px] mb-[12px]">
                <div
                  className={`w-[40px] h-[40px] border-[2px] border-[#111] rounded-[8px] ${agent.color} flex items-center justify-center text-[20px] shadow-[4px_4px_0px_#000] shrink-0`}
                >
                  {agent.icon}
                </div>
                <h3 className="text-[16px] font-bold uppercase">
                  {agent.role}
                </h3>
              </div>
              <p className="text-[13px] text-[#444] leading-relaxed flex-grow">
                {agent.desc}
              </p>
              <div className="border-t-[2px] border-[#111] mt-[12px] pt-[12px]">
                <p className="text-[10px] font-bold uppercase tracking-[0.1em] text-[#888] mb-[6px]">
                  Tools Used
                </p>
                <div className="flex flex-wrap gap-[4px]">
                  {agent.tools.map((t) => (
                    <code
                      key={t}
                      className="text-[10px] font-mono bg-[#f0f0f0] border border-[#ddd] px-[6px] py-[2px] rounded-[4px]"
                    >
                      {t}
                    </code>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ── Tool Registry ── */}
      <section className="space-y-[16px]">
        <h2 className="text-[22px] font-bold uppercase tracking-tight">
          Tool Registry
        </h2>
        <div className="brutal-card-static overflow-hidden !p-0">
          <div className="grid grid-cols-[1fr_120px_1fr] text-[11px] font-bold uppercase tracking-[0.1em] text-[#444] bg-[#f0f0f0] border-b-[2px] border-[#111] px-[16px] py-[10px]">
            <span>Tool</span>
            <span>Type</span>
            <span>Description</span>
          </div>
          {TOOLS.map((tool, i) => (
            <div
              key={tool.name}
              className={`grid grid-cols-[1fr_120px_1fr] items-center px-[16px] py-[10px] ${
                i < TOOLS.length - 1 ? "border-b border-[#ddd]" : ""
              }`}
            >
              <code className="text-[12px] font-mono font-bold">
                {tool.name}
              </code>
              <span
                className={`brutal-badge ${tool.color} text-[10px] !py-[2px] w-fit`}
              >
                {tool.type}
              </span>
              <span className="text-[12px] text-[#444]">{tool.desc}</span>
            </div>
          ))}
        </div>
      </section>

      {/* ── Execution Pipeline ── */}
      <section className="space-y-[16px]">
        <h2 className="text-[22px] font-bold uppercase tracking-tight">
          Execution Pipeline
        </h2>
        <div className="brutal-card-static bg-[#111] text-black space-y-[0px]">
          <div className="flex items-center gap-[12px] mb-[20px]">
            <div className="w-[32px] h-[32px] border-[2px] border-white/20 rounded-[8px] bg-[#FFD600] flex items-center justify-center text-[14px]">
              🤖
            </div>
            <div>
              <p className="text-[14px] font-bold uppercase tracking-[0.1em]">
                PR Scan Pipeline
              </p>
              <p className="text-[10px] font-mono text-black">
                Webhook → Planner → Scanner → Evaluator → Reporter
              </p>
            </div>
          </div>

          <div className="space-y-[2px] relative">
            {/* Vertical connector */}
            <div className="absolute left-[23px] top-[24px] bottom-[24px] w-[2px] bg-white/10" />

            {PIPELINE.map((step) => (
              <div
                key={step.step}
                className="flex items-center gap-[16px] px-[8px] py-[10px] rounded-[8px] relative"
                style={{ background: "rgba(255,255,255,0.03)" }}
              >
                <div
                  className={`w-[32px] h-[32px] border-[2px] border-white/20 rounded-full ${step.color} flex items-center justify-center text-[14px] shrink-0 z-10`}
                >
                  {step.icon}
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-[8px]">
                    <span className="text-[10px] font-bold text-black uppercase">
                      Step {step.step}
                    </span>
                    <span className="text-[14px] font-bold uppercase">
                      {step.label}
                    </span>
                  </div>
                  <p className="text-[12px] text-black mt-[2px]">{step.desc}</p>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-[16px] pt-[16px] border-t border-white/10 flex items-center justify-between px-[8px]">
            <span className="text-[10px] font-bold text-black uppercase">
              End-to-end: ~3.4 seconds average
            </span>
            <span className="text-[10px] font-bold text-black uppercase">
              Powered by Amazon Nova 2 Lite
            </span>
          </div>
        </div>
      </section>

      {/* ── Tech Stack ── */}
      <section className="space-y-[16px]">
        <h2 className="text-[22px] font-bold uppercase tracking-tight">
          Technology Stack
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-[16px]">
          {[
            {
              title: "AI Engine",
              items: [
                "Amazon Nova 2 Lite (Bedrock)",
                "Converse API + Extended Thinking",
                "Prompt-chained reasoning",
              ],
              color: "bg-[#FFD600]",
            },
            {
              title: "Infrastructure",
              items: [
                "AWS Lambda + Step Functions",
                "SQLite persistence",
                "GitHub App (webhooks)",
              ],
              color: "bg-[#00C2FF]",
            },
            {
              title: "Frontend",
              items: [
                "Next.js 15 (App Router)",
                "Neo-Brutalism design system",
                "Real-time pipeline visualization",
              ],
              color: "bg-[#2ECC71]",
            },
          ].map((stack) => (
            <div
              key={stack.title}
              className={`brutal-card-static ${stack.color}`}
            >
              <h3 className="text-[16px] font-bold uppercase mb-[12px]">
                {stack.title}
              </h3>
              <ul className="space-y-[6px]">
                {stack.items.map((item) => (
                  <li
                    key={item}
                    className="flex items-start gap-[8px] text-[13px] font-medium"
                  >
                    <span className="text-[10px] mt-[4px]">▸</span>
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </section>

      {/* ── Footer ── */}
      <div className="flex items-center justify-between pt-[16px] border-t-[2px] border-[#111]">
        <p className="text-[12px] font-bold uppercase tracking-[0.1em] text-[#888]">
          Built for the Amazon Nova AI Hackathon 2026
        </p>
        <Link href="/" className="brutal-btn text-[14px]">
          Run Manual Scan →
        </Link>
      </div>
    </div>
  );
}
