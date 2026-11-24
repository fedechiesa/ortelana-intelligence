export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
  }
}
let token = sessionStorage.getItem("ortelana-token") || "";
export function setToken(value: string) {
  token = value;
  if (value) sessionStorage.setItem("ortelana-token", value);
  else sessionStorage.removeItem("ortelana-token");
}
export function hasToken() {
  return !!token;
}
export async function api<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`/api${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
        ...options.headers,
      },
      signal: options.signal || AbortSignal.timeout(60000),
    });
  } catch {
    throw new ApiError(
      "The service could not be reached. Check the connection and retry with the same request.",
      0,
    );
  }
  const body = await response.json();
  if (!response.ok)
    throw new ApiError(
      typeof body.detail === "string" ? body.detail : "Request failed",
      response.status,
    );
  return body as T;
}
export function queryString(values: object) {
  const p = new URLSearchParams();
  Object.entries(values).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== "") p.set(k, String(v));
  });
  return p.toString();
}
