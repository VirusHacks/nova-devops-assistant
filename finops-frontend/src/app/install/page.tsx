"use client";

import { useState } from "react";
import Link from "next/link";

export default function InstallPage() {
  const [installed, setInstalled] = useState(false);

  const APP_NAME = process.env.NEXT_PUBLIC_GITHUB_APP_NAME || "nova-devops-automate";
  const installUrl = `https://github.com/apps/${APP_NAME}/installations/new`;

  return (
    <div className="p-8 max-w-4xl mx-auto space-y-12 animate-in fade-in duration-700">
      <header className="space-y-2">
        <h1 className="text-4xl font-black tracking-tight tracking-tighter uppercase leading-none">
          GitHub <span className="gradient-text">Integration</span>
        </h1>
        <p className="text-slate-500 font-medium">Protect your production repositories with the Nova Guardian.</p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
        {/* Left Side: Steps */}
        <section className="space-y-8">
           <div className="space-y-6">
                {[
                    { step: "01", title: "App Installation", desc: "Instantiate the Nova Devops Automate app on your GitHub account or organization." },
                    { step: "02", title: "Repository Access", desc: "Select the specific repositories containing your Terraform, K8s, or Docker source code." },
                    { step: "03", title: "Automated Checks", desc: "Nova will automatically review every Pull Request and provide line-by-line feedback." }
                ].map((s) => (
                    <div key={s.step} className="relative pl-12">
                        <div className="absolute left-0 top-0 w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-[10px] font-black text-emerald-500 tracking-tighter">
                            {s.step}
                        </div>
                        <h3 className="font-bold text-slate-100">{s.title}</h3>
                        <p className="text-xs text-slate-500 mt-1 leading-relaxed">{s.desc}</p>
                    </div>
                ))}
           </div>

           <div className="p-6 rounded-2xl border border-slate-800 bg-slate-900/30 space-y-4">
                <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Capabilities</p>
                <div className="grid grid-cols-2 gap-3">
                    {["Terraform HCL", "Dockerfiles", "K8s YAML", "Cloud Scores", "Auto-Fixes"].map(cap => (
                        <div key={cap} className="flex items-center gap-2 text-[10px] font-bold text-slate-300">
                            <span className="text-emerald-500">✔</span>
                            {cap}
                        </div>
                    ))}
                </div>
           </div>
        </section>

        {/* Right Side: CTA */}
        <section className="flex flex-col justify-center gap-6">
            {!installed ? (
                <div className="rounded-3xl border border-slate-800 bg-slate-950 p-8 space-y-6 text-center relative overflow-hidden group">
                    <div className="absolute top-0 right-0 p-4 grayscale opacity-10 group-hover:grayscale-0 group-hover:opacity-100 transition-all text-4xl">🐙</div>
                    <div className="space-y-2">
                        <h2 className="text-xl font-bold">Connect your GitHub</h2>
                        <p className="text-xs text-slate-500">Zero configuration required. Nova works out of the box with default security policies.</p>
                    </div>
                    
                    <a
                        href={installUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="block w-full rounded-2xl bg-emerald-500 py-5 text-sm font-black text-slate-950 hover:bg-emerald-400 transition-all shadow-[0_0_20px_rgba(16,185,129,0.2)] active:scale-95"
                    >
                        INSTALL NOVA GUARDIAN
                    </a>
                    
                    <p className="text-[10px] text-slate-600 font-medium">Free for Public & Private Repositories</p>
                </div>
            ) : (
                <div className="rounded-3xl border border-emerald-500/20 bg-emerald-500/5 p-8 text-center space-y-4 animate-in zoom-in-95 duration-500">
                    <div className="w-16 h-16 rounded-full bg-emerald-500/20 flex items-center justify-center mx-auto text-3xl">🛡️</div>
                    <div className="space-y-2">
                        <h2 className="text-xl font-bold text-emerald-400">Connection Active</h2>
                        <p className="text-xs text-slate-400 max-w-[240px] mx-auto">Nova is now protecting your repositories. Open a PR to see the AI in action.</p>
                    </div>
                </div>
            )}
            
            <Link href="/dashboard" className="text-center text-xs font-bold text-slate-600 hover:text-slate-300 uppercase tracking-widest transition-colors">
                Return to Command Center →
            </Link>
        </section>
      </div>
    </div>
  );
}
