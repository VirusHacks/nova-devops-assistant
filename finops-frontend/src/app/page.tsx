 "use client";

import { useState, FormEvent } from "react";

interface AnalysisResult {
  session_id?: string;
  invocation_id?: string;
  result: string;
  createdAt: string;
}

// Use Next.js API route (proxy) to avoid CORS; proxy forwards to API Gateway
const API_BASE_URL = "";

export default function HomePage() {
  const [terraform, setTerraform] = useState("");
  const [request, setRequest] = useState(
    "Analyze this Terraform for Financial Tech Debt and cost risks."
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<AnalysisResult[]>([]);

  const handleAnalyze = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!terraform.trim()) {
      setError("Please paste your Terraform content.");
      return;
    }
    setLoading(true);
    try {
      const res = await fetch("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          request,
          terraform_content: terraform,
          terraform_file_name: "infra.tf",
        }),
      });

      if (!res.ok) {
        const text = await res.text();
        throw new Error(`Backend error: ${res.status} ${text}`);
      }

      const data = await res.json();
      const item: AnalysisResult = {
        session_id: data.session_id,
        invocation_id: data.invocation_id,
        result: data.result ?? data.report ?? JSON.stringify(data, null, 2),
        createdAt: new Date().toISOString(),
      };
      setResults((prev) => [item, ...prev]);
    } catch (err: any) {
      setError(err.message ?? "Unexpected error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-50 flex flex-col">
      <header className="border-b border-slate-800 px-6 py-4 flex items-center justify-between">
        <h1 className="text-xl font-semibold tracking-tight">
          FinOps FAME Dashboard
        </h1>
        <span className="text-xs text-slate-400">
          Planner → Actor → Evaluator • AWS Step Functions
        </span>
      </header>

      <main className="flex-1 grid gap-6 px-6 py-6 md:grid-cols-2">
        <section className="space-y-4">
          <h2 className="text-lg font-semibold">Run new analysis</h2>
          <form onSubmit={handleAnalyze} className="space-y-4">
            <div>
              <label className="block text-sm mb-1 font-medium">
                Request / question
              </label>
              <input
                className="w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-emerald-500/60"
                value={request}
                onChange={(e) => setRequest(e.target.value)}
              />
            </div>

            <div>
              <label className="block text-sm mb-1 font-medium">
                Terraform content
              </label>
              <textarea
                className="w-full h-64 rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm font-mono outline-none focus:ring-2 focus:ring-emerald-500/60"
                value={terraform}
                onChange={(e) => setTerraform(e.target.value)}
                placeholder='resource "aws_instance" "example" { ... }'
              />
            </div>

            {error && (
              <p className="text-sm text-red-400">
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="inline-flex items-center rounded-md bg-emerald-500 px-4 py-2 text-sm font-semibold text-slate-950 shadow-sm hover:bg-emerald-400 disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {loading ? "Analyzing..." : "Run FinOps analysis"}
            </button>
          </form>
        </section>

        <section className="space-y-4">
          <h2 className="text-lg font-semibold">Recent results</h2>
          {results.length === 0 && (
            <p className="text-sm text-slate-400">
              No analyses yet. Run your first scan on the left.
            </p>
          )}
          <div className="space-y-3 max-h-[70vh] overflow-y-auto pr-1">
            {results.map((item, idx) => (
              <article
                key={idx}
                className="rounded-lg border border-slate-800 bg-slate-900/50 p-3"
              >
                <div className="mb-2 flex items-center justify-between text-xs text-slate-400">
                  <span>Session: {item.session_id ?? "n/a"}</span>
                  <span>
                    {new Date(item.createdAt).toLocaleString()}
                  </span>
                </div>
                <pre className="whitespace-pre-wrap text-sm leading-relaxed">
                  {item.result}
                </pre>
              </article>
            ))}
          </div>
        </section>
      </main>
    </div>
  );
}
