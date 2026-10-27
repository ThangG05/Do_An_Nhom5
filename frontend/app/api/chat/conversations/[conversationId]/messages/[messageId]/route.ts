const API_BASE_URL = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1").replace(/\/+$/, "");

export async function POST(
  request: Request,
  { params }: { params: Promise<{ conversationId: string; messageId: string }> },
) {
  const { conversationId, messageId } = await params;
  const authorization = request.headers.get("authorization");

  try {
    const upstream = await fetch(
      `${API_BASE_URL}/chat/conversations/${encodeURIComponent(conversationId)}/messages/${encodeURIComponent(messageId)}`,
      {
        method: "POST",
        headers: authorization ? { authorization } : undefined,
        cache: "no-store",
      },
    );
    return new Response(upstream.body, {
      status: upstream.status,
      headers: {
        "content-type": upstream.headers.get("content-type") || "application/json",
        "cache-control": "no-store",
      },
    });
  } catch (error) {
    console.error("Chat recall proxy could not reach backend", error);
    return Response.json({ detail: "Máy chủ ứng dụng không kết nối được backend để thu hồi tin nhắn." }, { status: 502 });
  }
}
