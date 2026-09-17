import { NextResponse } from "next/server";

export async function GET() {
  return NextResponse.json({
    status: "ok",
    service: "recourse-web",
    environment: process.env.NEXT_PUBLIC_ENVIRONMENT || "development",
  });
}
