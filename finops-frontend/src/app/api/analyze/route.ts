import { NextRequest, NextResponse } from "next/server";

// Prefer local backend (stays running); else use API Gateway (AWS).
const BACKEND_URL =
  process.env.BACKEND_URL || process.env.NEXT_PUBLIC_API_BASE_URL;

export async function POST(request: NextRequest) {
  if (!BACKEND_URL) {
    return NextResponse.json(
      {
        error:
          "No backend configured. Set BACKEND_URL (e.g. http://127.0.0.1:5000) or NEXT_PUBLIC_API_BASE_URL.",
      },
      { status: 500 }
    );
  }

  try {
    const body = await request.json();
    const url = BACKEND_URL.replace(/\/$/, "") + "/analyze";
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    const text = await res.text();
    let data: Record<string, unknown> = {};
    try {
      if (text) data = JSON.parse(text) as Record<string, unknown>;
    } catch {
      data = {};
    }
    if (!res.ok) {
      return NextResponse.json(
        (data as { error?: string }).error ? data : { error: text || `Backend ${res.status}` },
        { status: res.status }
      );
    }
    return NextResponse.json(data);
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : "Proxy request failed";
    return NextResponse.json({ error: message }, { status: 502 });
  }
}
