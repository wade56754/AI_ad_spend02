const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || "http://localhost:8000";

export interface ApiResponse<T> {
  data: T | null;
  error: string | null;
  meta: Record<string, unknown> | null;
}

function assertResponseShape<T>(payload: unknown): asserts payload is ApiResponse<T> {
  if (typeof payload !== "object" || payload === null) {
    throw new Error("响应结构无效");
  }

  const cast = payload as Record<string, unknown>;
  if (!cast.hasOwnProperty("data") || !cast.hasOwnProperty("error") || !cast.hasOwnProperty("meta")) {
    throw new Error("响应缺少必要字段");
  }
}

export async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<ApiResponse<T>> {
  const url = `${API_BASE_URL}${path.startsWith("/") ? path : `/${path}`}`;

  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  let payload: unknown;
  try {
    payload = await response.json();
  } catch {
    throw new Error("响应解析失败");
  }

  assertResponseShape<T>(payload);
  return payload;
}

