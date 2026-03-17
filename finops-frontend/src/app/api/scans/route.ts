import { NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8000";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const repo = searchParams.get("repo");
  const limit = searchParams.get("limit") || "50";

  const url = new URL(`${BACKEND_URL}/api/scans`);
  if (repo) url.searchParams.set("repo", repo);
  url.searchParams.set("limit", limit);

  try {
    const res = await fetch(url.toString(), { next: { revalidate: 0 } });
    const data = await res.json();
    return NextResponse.json(data);
  } catch (err: unknown) {
    const errorMessage = err instanceof Error ? err.message : "Internal Server Error";
    return NextResponse.json({ error: errorMessage }, { status: 502 });
  }
}
