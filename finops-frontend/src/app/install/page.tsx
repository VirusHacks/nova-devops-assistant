"use client";

import { useState } from "react";
import Link from "next/link";

export default function InstallPage() {
  const [installed] = useState(false);

  const APP_NAME =
    process.env.NEXT_PUBLIC_GITHUB_APP_NAME || "nova-devops-automate";
  const installUrl = `https://github.com/apps/${APP_NAME}/installations/new`;

  return (
    <div className="space-y-[32px]">
      {/* ── Header ── */}
      <div className="page-header">
        <h1>
          GitHub{" "}
          <span className="bg-white px-[8px] py-[2px] border-[2px] border-[#111] rounded-[8px] inline-block">
            Integration
          </span>
        </h1>
        <p>Protect your production repositories with the Nova Guardian.</p>
      </div>

      {/* ── Two Column ── */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-[24px]">
        {/* LEFT (5 cols) */}
        <div className="md:col-span-5 space-y-[24px]">
          <div className="brutal-card-static space-y-[24px]">
            <h2 className="text-[20px] font-bold uppercase border-b-[2px] border-[#111] pb-4 mb-[16px]">
              Installation Flow
            </h2>
            {[
              {
                step: "01",
                title: "App Installation",
                desc: "Instantiate the Nova Devops Automate app on your GitHub account or organization.",
              },
              {
                step: "02",
                title: "Repository Access",
                desc: "Select the specific repositories containing your Terraform, K8s, or Docker source code.",
              },
              {
                step: "03",
                title: "Automated Checks",
                desc: "Nova will automatically review every Pull Request and provide line-by-line feedback.",
              },
            ].map((s) => (
              <div key={s.step} className="flex gap-[16px] pt-4">
                <div className="w-[36px] h-[36px] shrink-0 bg-[#FFD600] border-[2px] border-[#111] rounded-[8px] shadow-[4px_4px_0px_#000] flex items-center justify-center text-[12px] font-black">
                  {s.step}
                </div>
                <div>
                  <h3 className="text-[16px] font-bold uppercase">{s.title}</h3>
                  <p className="text-[14px] text-[#444] font-medium mt-[4px] leading-relaxed">
                    {s.desc}
                  </p>
                </div>
              </div>
            ))}
          </div>

          <div className="brutal-card-static bg-[#00C2FF]">
            <p className="text-[12px] font-bold uppercase tracking-[0.1em] mb-[12px]">
              Capabilities
            </p>
            <div className="grid grid-cols-2 gap-[8px]">
              {[
                "Terraform HCL",
                "Dockerfiles",
                "K8s YAML",
                "Cloud Scores",
                "Auto-Fixes",
              ].map((cap) => (
                <div
                  key={cap}
                  className="flex items-center gap-[8px] text-[13px] font-bold uppercase"
                >
                  <span className="w-[20px] h-[20px] border-[2px] border-[#111] rounded-[4px] bg-[#FFD600] flex items-center justify-center text-[10px] shadow-[2px_2px_0px_#000]">
                    ✔
                  </span>
                  {cap}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* RIGHT (7 cols) */}
        <div className="md:col-span-7 space-y-[24px]">
          {!installed ? (
            <div className="brutal-card-static bg-[#FFD600] text-center relative overflow-hidden">
              <div className="absolute top-[16px] right-[16px] opacity-20 text-[48px] pointer-events-none">
                🐙
              </div>
              <div className="py-[16px] space-y-[16px]">
                <h2 className="text-[28px] font-bold uppercase">
                  Connect your GitHub
                </h2>
                <p className="text-[16px] font-medium max-w-[360px] mx-auto">
                  Zero configuration required. Nova works out of the box with
                  default security policies.
                </p>

                <a
                  href={installUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="brutal-btn-ghost w-full text-[16px] py-[16px] justify-center"
                >
                  Install Nova Guardian
                </a>

                <p className="text-[12px] font-bold uppercase tracking-[0.1em] text-[#111] opacity-60 mt-[8px]">
                  Free for Public &amp; Private Repositories
                </p>
              </div>
            </div>
          ) : (
            <div className="brutal-card-static bg-[#2ECC71] text-center space-y-[16px] py-[48px]">
              <div className="w-[56px] h-[56px] border-[2px] border-[#111] rounded-[10px] bg-white flex items-center justify-center mx-auto text-[28px] shadow-[4px_4px_0px_#000]">
                🛡️
              </div>
              <h2 className="text-[24px] font-bold uppercase">
                Connection Active
              </h2>
              <p className="text-[16px] font-medium max-w-[300px] mx-auto">
                Nova is now protecting your repositories. Open a PR to see the
                AI in action.
              </p>
            </div>
          )}

          <Link
            href="/dashboard"
            className="brutal-btn-ghost w-full justify-center text-[14px]"
          >
            Return to Command Center →
          </Link>
        </div>
      </div>
    </div>
  );
}
