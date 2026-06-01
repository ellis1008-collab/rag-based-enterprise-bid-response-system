export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

type RequestOptions = Omit<RequestInit, "body"> & {
  body?: unknown;
};

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { body, ...requestOptions } = options;
  const headers = new Headers(options.headers);
  const init: RequestInit = {
    ...requestOptions,
    headers,
  };

  if (body !== undefined) {
    headers.set("Content-Type", "application/json");
    init.body = JSON.stringify(body);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, init);
  if (!response.ok) {
    throw new Error(await getErrorMessage(response));
  }
  return response.json() as Promise<T>;
}

export async function uploadFile<T>(path: string, file: File): Promise<T> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    body: formData,
  });
  if (!response.ok) {
    throw new Error(await getErrorMessage(response));
  }
  return response.json() as Promise<T>;
}

async function getErrorMessage(response: Response): Promise<string> {
  try {
    const data = (await response.json()) as { detail?: string };
    return data.detail ?? `${response.status} ${response.statusText}`;
  } catch {
    return `${response.status} ${response.statusText}`;
  }
}
