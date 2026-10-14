import { supabase } from "@/lib/supabase";

export const API_URL = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/+$/, "");

/** status 0 = the request never got a response (server down, CORS, offline). */
export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

type ApiOptions = Omit<RequestInit, "body"> & {
  json?: unknown;
  /** Pass explicitly from auth callbacks; otherwise read from the current Supabase session. */
  token?: string;
};

/**
 * Calls the NeetiAi backend with the Supabase access token attached.
 * Resolves with the parsed JSON body; throws ApiError for network failures
 * and non-2xx responses (message = FastAPI's `detail` when present).
 */
export async function api<T = unknown>(path: string, { json, token, headers, ...init }: ApiOptions = {}): Promise<T> {
  const accessToken = token ?? (await supabase.auth.getSession()).data.session?.access_token;

  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}`, {
      ...init,
      headers: {
        ...(json !== undefined ? { "Content-Type": "application/json" } : {}),
        ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
        ...headers,
      },
      body: json !== undefined ? JSON.stringify(json) : undefined,
    });
  } catch {
    throw new ApiError("Can't reach the NeetiAi server.", 0);
  }

  const data = await res.json().catch(() => null);
  if (!res.ok) {
    const detail = data?.detail;
    const message = typeof detail === "string" ? detail : `Request failed (${res.status})`;
    throw new ApiError(message, res.status);
  }
  return data as T;
}
