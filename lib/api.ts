const DEFAULT_BASE_URL = "http://localhost:8000";

function normalizeBaseUrl(raw: string | undefined): string {
  if (!raw) {
    return DEFAULT_BASE_URL;
  }
  let normalized = raw.trim();
  if (!normalized) {
    return DEFAULT_BASE_URL;
  }

  normalized = normalized.replace(/\/+$/, "");
  if (normalized.toLowerCase().endsWith("/api")) {
    normalized = normalized.slice(0, -4);
  }

  return normalized || DEFAULT_BASE_URL;
}

const API_BASE_URL = normalizeBaseUrl(process.env.NEXT_PUBLIC_API_URL);

function resolveApiPath(path: string): string {
  const normalized = path.startsWith("/") ? path : `/${path}`;
  if (/^\/api\/v\d+\//i.test(normalized)) {
    return normalized;
  }
  if (normalized.startsWith("/api/")) {
    return normalized.replace(/^\/api\//i, "/api/v1/");
  }
  return normalized;
}

export interface ApiError {
  code: string | null;
  message: string | null;
}

export interface ApiResponse<T> {
  data: T | null;
  error: ApiError | null;
  meta: (Record<string, unknown> & { timestamp?: string; pagination?: unknown }) | null;
}

function assertResponseShape<T>(payload: unknown): asserts payload is ApiResponse<T> {
  if (typeof payload !== "object" || payload === null) {
    throw new Error("响应结构无效");
  }

  const cast = payload as Record<string, unknown>;
  if (!cast.hasOwnProperty("data") || !cast.hasOwnProperty("error") || !cast.hasOwnProperty("meta")) {
    throw new Error("响应缺少必要字段");
  }

  const error = cast.error;
  if (error !== null) {
    if (typeof error !== "object" || error === null) {
      throw new Error("错误结构无效");
    }
    if (!("code" in error) || !("message" in error)) {
      throw new Error("错误缺少必要字段");
    }
  }
}

function fallbackError(message: string, code: string): ApiError {
  return { code, message };
}

export async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<ApiResponse<T>> {
  const resolvedPath = resolveApiPath(path);
  const url = `${API_BASE_URL}${resolvedPath}`;

  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  let payload: unknown = null;
  try {
    payload = await response.json();
  } catch {
    return {
      data: null,
      error: fallbackError("响应解析失败", `HTTP_${response.status}`),
      meta: {
        timestamp: new Date().toISOString(),
        pagination: null,
      },
    };
  }

  try {
    assertResponseShape<T>(payload);
    return payload;
  } catch (validationError) {
    return {
      data: null,
      error: fallbackError(
        validationError instanceof Error ? validationError.message : "响应结构无效",
        `HTTP_${response.status}`,
      ),
      meta: {
        timestamp: new Date().toISOString(),
        pagination: null,
      },
    };
  }
}

