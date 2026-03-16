"use client";

import Link from "next/link";

export default function DocsPage() {
  return (
    <div className="min-h-screen p-8 max-w-4xl mx-auto space-y-12">
      <header className="space-y-4">
        <h1 className="text-5xl font-black tracking-tight">
          System <span className="gradient-text">Architecture</span>
        </h1>
        <p className="text-slate-400 text-lg leading-relaxed">
          Nova-Devops-Automate leverages custom AWS Bedrock models (Nova Micro/Pro) 
          and specialized static analysis engines to protect your cloud infrastructure.
        </p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <section className="p-6 rounded-2xl border border-slate-800 bg-slate-900/50 space-y-4">
          <div className="w-12 h-12 rounded-xl bg-emerald-500/10 flex items-center justify-center text-2xl">🔍</div>
          <h2 className="text-xl font-bold">Static Analysis Engine</h2>
          <p className="text-sm text-slate-400">
            Our multi-engine core scans across Terraform, Kubernetes YAML, and Dockerfiles. 
            It identifies patterns like "privileged: true" or "expensive instance types" 
            in milliseconds.
          </p>
        </section>

        <section className="p-6 rounded-2xl border border-slate-800 bg-slate-900/50 space-y-4">
          <div className="w-12 h-12 rounded-xl bg-purple-500/10 flex items-center justify-center text-2xl">🧠</div>
          <h2 className="text-xl font-bold">AWS Nova Logic</h2>
          <p className="text-sm text-slate-400">
            Plain errors are boring. Nova analyzes the findings, determines the 
            financial impact, and writes the specific fix for your PR. 
            It's like having a Senior SRE reviewing every commit.
          </p>
        </section>
      </div>

      <section className="space-y-6">
        <h2 className="text-3xl font-bold">The Guardian Flow</h2>
        <div className="space-y-4 border-l-2 border-emerald-500/20 pl-8 ml-4">
          <div className="relative">
            <div className="absolute -left-[41px] top-1 w-4 h-4 rounded-full bg-emerald-500 border-4 border-slate-950"></div>
            <h3 className="font-bold text-slate-100">Webhook Registered</h3>
            <p className="text-sm text-slate-400">GitHub sends a notification when infrastructure files change.</p>
          </div>
          <div className="relative">
            <div className="absolute -left-[41px] top-1 w-4 h-4 rounded-full bg-emerald-500 border-4 border-slate-950"></div>
            <h3 className="font-bold text-slate-100">Deep Scan</h3>
            <p className="text-sm text-slate-400">Terraform and K8s configuration is validated against security and cost policies.</p>
          </div>
          <div className="relative">
            <div className="absolute -left-[41px] top-1 w-4 h-4 rounded-full bg-emerald-500 border-4 border-slate-950"></div>
            <h3 className="font-bold text-slate-100">PR Annotation</h3>
            <p className="text-sm text-slate-400">Nova posts line-by-line feedback with automated fix suggestions.</p>
          </div>
        </div>
      </section>

      <footer className="pt-12 border-t border-slate-800 flex justify-between items-center text-sm text-slate-500">
        <p>Built for the AWS Nova Hackathon 2026</p>
        <Link href="/" className="text-emerald-500 hover:underline">Run manual scan →</Link>
      </footer>
    </div>
  );
}
