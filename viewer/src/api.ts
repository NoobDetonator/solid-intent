import type { ProjectData, ProjectSummary } from "./types";

async function requestJson<T>(input: RequestInfo | URL, init?: RequestInit): Promise<T> {
  const response = await fetch(input, init);
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.error ?? `Request failed with status ${response.status}.`);
  }
  return payload as T;
}

export async function listProjects(): Promise<ProjectSummary[]> {
  const payload = await requestJson<{ projects: ProjectSummary[] }>("/api/projects");
  return payload.projects;
}

export function loadProject(projectId: string): Promise<ProjectData> {
  return requestJson<ProjectData>(`/api/projects/${projectId}`);
}

export function saveParameters(
  projectId: string,
  changes: Record<string, number>,
): Promise<ProjectData> {
  return requestJson<ProjectData>(`/api/projects/${projectId}/parameters`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ changes }),
  });
}

export function rebuildProject(
  projectId: string,
  options: { accept?: boolean; export?: boolean } = {},
): Promise<{ ok: boolean; project: ProjectData; log?: string }> {
  return requestJson<{ ok: boolean; project: ProjectData; log?: string }>(
    `/api/projects/${projectId}/rebuild`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        accept: options.accept ?? true,
        export: options.export ?? true,
      }),
    },
  );
}
