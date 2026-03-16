"use client";

import { useState, FormEvent } from "react";

interface AnalysisResult {
  session_id?: string;
  invocation_id?: string;
  result: string;
  createdAt: string;
  type: string;
}

interface AnalysisRequestPayload {
  request?: string;
  terraform_file_name?: string;
  terraform_content: string;
}

export default function HomePage() {
  const [content, setContent] = useState("");
  const [fileType, setFileType] = useState("terraform");
  const [focus, setFocus] = useState("General Security & Cost Optimization");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<AnalysisResult[]>([]);

  const handleAnalyze = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!content.trim()) {
      setError("Please provide infrastructure code to audit.");
      return;
    }

    const payload: AnalysisRequestPayload = {
      request: `Audit this ${fileType} for: ${focus}`,
      terraform_file_name: fileType === "terraform" ? "main.tf" : (fileType === "docker" ? "Dockerfile" : "k8s.yaml"),
      terraform_content: content,
    };

    setLoading(true);
    try {
      const res = await fetch("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        throw new Error(`Cloud Analysis Error: ${res.status}`);
      }

      const data = await res.json();
      const item: AnalysisResult = {
        session_id: data.session_id,
        invocation_id: data.invocation_id,
        result: data.result ?? data.report ?? "Scan completed with no issues found.",
        createdAt: new Date().toISOString(),
        type: fileType,
      };
      setResults((prev) => [item, ...prev]);
    } catch (err: any) {
      setError(err.message ?? "Unexpected connectivity error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-12 animate-in slide-in-from-bottom-4 duration-700">
      <header className="space-y-2">
        <h1 className="text-4xl font-black tracking-tight tracking-tighter uppercase leading-none">
          Manual <span className="gradient-text">Cloud Audit</span>
        </h1>
        <p className="text-slate-500 font-medium">Instantly analyze IaC clusters using the Nova Guardian engine.</p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-start">
        {/* Input Form */}
        <section className="lg:col-span-7 space-y-8">
          <form onSubmit={handleAnalyze} className="space-y-6">
             <div className="grid grid-cols-2 gap-4">
               <div className="space-y-2">
                  <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Asset Type</label>
                  <select 
                    className="w-full rounded-xl border border-slate-800 bg-slate-900/50 px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-emerald-500/40 appearance-none bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iOCIgdmlld0JveD0iMCAwIDEyIDgiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHBhdGggZD0iTTEgMUw2IDZMMTIgMSIgc3Ryb2tlPSIjNDc1NTY5IiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPjwvc3ZnPg==')] bg-[length:12px_8px] bg-[right_1rem_center] bg-no-repeat"
                    value={fileType}
                    onChange={(e) => setFileType(e.target.value)}
                  >
                    <option value="terraform">Terraform (HCL)</option>
                    <option value="k8s">Kubernetes (YAML)</option>
                    <option value="docker">Dockerfile</option>
                  </select>
               </div>
               <div className="space-y-2">
                  <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Scan Profile</label>
                  <select 
                    className="w-full rounded-xl border border-slate-800 bg-slate-900/50 px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-emerald-500/40 appearance-none bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iOCIgdmlld0JveD0iMCAwIDEyIDgiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHBhdGggZD0iTTEgMUw2IDZMMTIgMSIgc3Ryb2tlPSIjNDc1NTY5IiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPjwvc3ZnPg==')] bg-[length:12px_8px] bg-[right_1rem_center] bg-no-repeat"
                    value={focus}
                    onChange={(e) => setFocus(e.target.value)}
                  >
                    <option value="General Security">Security First</option>
                    <option value="Cost Optimization">FinOps / Cost</option>
                    <option value="Compliance (CIS)">Compliance (CIS)</option>
                  </select>
               </div>
             </div>

            <div className="space-y-2">
              <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest">
                Source Code
              </label>
              <div className="relative group">
                <div className="absolute -inset-0.5 rounded-2xl bg-gradient-to-br from-emerald-500/20 to-transparent opacity-0 group-focus-within:opacity-100 transition-opacity blur"></div>
                <textarea
                  className="relative w-full h-80 rounded-2xl border border-slate-800 bg-slate-950 px-5 py-4 text-sm font-mono outline-none focus:border-emerald-500/50 transition-all resize-none"
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  placeholder={`project { \n  name = "production-cluster"\n  region = "us-east-1"\n}`}
                />
              </div>
            </div>

            {error && (
              <div className="p-4 rounded-xl border border-red-500/20 bg-red-500/5 flex items-center gap-3">
                <span className="text-red-500 text-lg">⚠️</span>
                <p className="text-xs text-red-400 font-bold uppercase tracking-tight">{error}</p>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full relative group overflow-hidden rounded-2xl bg-emerald-500 py-4 text-sm font-black text-slate-950 transition-all hover:scale-[1.01] active:scale-[0.98] disabled:opacity-50"
            >
              <div className="absolute inset-0 bg-white/20 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700 ease-in-out skew-x-[-20deg]"></div>
              <span className="relative flex items-center justify-center gap-2">
                {loading ? (
                    <>
                        <div className="w-4 h-4 border-2 border-slate-950/30 border-t-slate-950 rounded-full animate-spin"></div>
                        DISPATCHING NOVA AGENT...
                    </>
                ) : (
                    <>
                        🛡️ INITIATE SECURITY AUDIT
                    </>
                )}
              </span>
            </button>
          </form>
        </section>

        {/* Results Stream */}
        <section className="lg:col-span-5 space-y-6">
          <div className="flex items-center justify-between px-2">
              <h3 className="text-xs font-black text-slate-500 uppercase tracking-[0.2em]">Audit Results</h3>
              {results.length > 0 && (
                  <button onClick={() => setResults([])} className="text-[10px] font-bold text-slate-600 hover:text-red-500 uppercase transition-colors">Clear All</button>
              )}
          </div>

          <div className="space-y-4 max-h-[80vh] overflow-y-auto pr-2 custom-scrollbar">
            {results.length === 0 ? (
              <div className="rounded-3xl border border-dashed border-slate-800 py-20 flex flex-col items-center justify-center text-center space-y-4">
                <div className="w-16 h-16 rounded-full bg-slate-900 flex items-center justify-center text-2xl grayscale opacity-50">📂</div>
                <p className="text-xs text-slate-500 font-bold uppercase tracking-widest max-w-[180px]">Results will appear here in real-time</p>
              </div>
            ) : (
              results.map((item, idx) => (
                <article
                  key={idx}
                  className="rounded-2xl border border-slate-800 bg-slate-900/30 p-6 space-y-4 animate-in slide-in-from-right-4 duration-500"
                >
                  <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                    <div className="flex items-center gap-2">
                        <span className="px-2 py-0.5 rounded bg-slate-800 text-[10px] font-bold text-slate-300 uppercase tracking-wider">{item.type}</span>
                        <span className="text-[10px] font-medium text-slate-600">ID: {item.session_id?.slice(0, 8)}</span>
                    </div>
                    <span className="text-[10px] font-bold text-slate-500">{new Date(item.createdAt).toLocaleTimeString()}</span>
                  </div>
                  <div className="text-sm leading-relaxed text-slate-300 prose prose-invert max-w-none">
                    <div dangerouslySetInnerHTML={{ 
                        __html: item.result
                            .replace(/\n/g, '<br/>')
                            .replace(/\*\*(.*?)\*\*/g, '<strong class="text-emerald-400">$1</strong>')
                            .replace(/` (.*?)`/g, '<code class="bg-slate-800 px-1 rounded">$1</code>')
                    }} />
                  </div>
                </article>
              ))
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
