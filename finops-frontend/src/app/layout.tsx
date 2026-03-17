import type { Metadata } from "next";
import { Space_Grotesk } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const spaceGrotesk = Space_Grotesk({
  variable: "--font-brutal",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Nova-Devops-Automate | Infrastructure Guardian",
  description: "AI-Powered FinOps and Security for Infrastructure-as-Code",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${spaceGrotesk.variable} antialiased flex h-screen overflow-hidden bg-white text-[#111]`}>
        {/* ──── Sidebar ──── */}
        <aside className="w-[260px] border-r-[2px] border-[#111] bg-white flex flex-col shrink-0 z-10">
          {/* Logo */}
          <div className="px-[24px] py-[20px] border-b-[2px] border-[#111] bg-[#FFD600] flex items-center gap-[12px]">
            <div className="w-[36px] h-[36px] border-[2px] border-[#111] rounded-[8px] bg-white flex items-center justify-center shadow-[4px_4px_0px_#000]">
              <span className="text-[18px]">🛡️</span>
            </div>
            <div>
              <p className="text-[15px] font-bold tracking-tight uppercase leading-none">NOVA DEVOPS</p>
              <p className="text-[11px] font-semibold uppercase tracking-[0.15em] mt-[2px] opacity-70">Guardian v1</p>
            </div>
          </div>

          {/* Nav */}
          <nav className="flex-1 px-[16px] py-[16px] space-y-[4px] overflow-y-auto">
            {[
              { href: "/dashboard", icon: "📊", label: "Dashboard" },
              { href: "/", icon: "⚡", label: "Manual Audit" },
              { href: "/install", icon: "🔗", label: "Integrations" },
            ].map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="flex items-center gap-[12px] px-[16px] py-[10px] rounded-[8px] text-[14px] font-semibold text-[#111] border-[2px] border-transparent hover:border-[#111] hover:bg-[#FAFAFA] hover:shadow-[4px_4px_0px_#000] transition-all"
              >
                <span className="text-[18px] w-[20px] text-center">{item.icon}</span>
                {item.label}
              </Link>
            ))}

            <div className="pt-[24px] pb-[8px] px-[16px]">
              <span className="text-[11px] font-bold text-[#888] uppercase tracking-[0.15em]">Resources</span>
            </div>

            {[
              { href: "/docs", icon: "📖", label: "Documentation" },
              { href: "/settings", icon: "⚙️", label: "Settings" },
            ].map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="flex items-center gap-[12px] px-[16px] py-[10px] rounded-[8px] text-[14px] font-semibold text-[#111] border-[2px] border-transparent hover:border-[#111] hover:bg-[#FAFAFA] hover:shadow-[4px_4px_0px_#000] transition-all"
              >
                <span className="text-[18px] w-[20px] text-center">{item.icon}</span>
                {item.label}
              </Link>
            ))}
          </nav>

          {/* Status */}
          <div className="px-[16px] py-[16px] border-t-[2px] border-[#111]">
            <div className="border-[2px] border-[#111] rounded-[8px] px-[16px] py-[10px] shadow-[4px_4px_0px_#000] bg-white flex items-center justify-between">
              <span className="text-[12px] font-bold uppercase tracking-[0.1em]">Cloud Status</span>
              <div className="flex items-center gap-[6px]">
                <div className="w-[10px] h-[10px] border-[2px] border-[#111] rounded-full bg-[#2ECC71]"></div>
                <span className="text-[12px] font-bold">Online</span>
              </div>
            </div>
          </div>
        </aside>

        {/* ──── Main ──── */}
        <div className="flex-1 flex flex-col min-w-0 bg-[#FAFAFA]">
          <main className="flex-1 overflow-y-auto">
            <div className="content-container">
              {children}
            </div>
          </main>
        </div>
      </body>
    </html>
  );
}
