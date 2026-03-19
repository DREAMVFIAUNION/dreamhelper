import { NextRequest, NextResponse } from "next/server";
import { brainCoreFetch } from '@/lib/brain-core-url';

export async function POST(req: NextRequest) {
  try {
    const formData = await req.formData();
    const resp = await brainCoreFetch('/api/v1/multimodal/vision/analyze', {
      method: "POST",
      body: formData,
    });
    const data = await resp.json();
    return NextResponse.json(data);
  } catch {
    return NextResponse.json(
      { error: "Vision analysis failed" },
      { status: 502 }
    );
  }
}
