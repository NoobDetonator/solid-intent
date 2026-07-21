import { lazy, Suspense, useEffect, useMemo, useState } from "react";
import { AlertTriangle, Box, RefreshCw } from "lucide-react";

import { listProjects, loadProject, saveParameters } from "./api";
import { renderableBodies } from "./bodies";
import { ContextRail, type BodyVisibility } from "./components/ContextRail";
import { Inspector } from "./components/Inspector";
import { ProjectHeader } from "./components/ProjectHeader";
import type { EvidenceView, ProjectData, ProjectSummary } from "./types";

const ModelViewer = lazy(() =>
  import("./components/ModelViewer").then((module) => ({ default: module.ModelViewer })),
);

type ToastState = { kind: "success" | "error"; message: string } | null;

function LoadingShell() {
  return (
    <div className="app-loading" role="status" aria-label="Loading SolidIntent project">
      <div className="loading-header" />
      <div className="loading-rail" />
      <div className="loading-canvas">
        <Box aria-hidden="true" />
        <span>Opening parametric project</span>
      </div>
      <div className="loading-inspector" />
    </div>
  );
}

function ErrorShell({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <main className="fatal-state">
      <AlertTriangle aria-hidden="true" />
      <h1>Project could not be opened</h1>
      <p>{message}</p>
      <button className="button button--primary" type="button" onClick={onRetry}>
        <RefreshCw aria-hidden="true" />
        Retry
      </button>
    </main>
  );
}

function ModelLoadingStage() {
  return (
    <section className="model-stage model-stage--module-loading" aria-label="Loading 3D viewer">
      <div className="canvas-loading" role="status">
        <span />
        Loading interactive viewer
      </div>
    </section>
  );
}

export default function App() {
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [project, setProject] = useState<ProjectData | null>(null);
  const [selectedView, setSelectedView] = useState<EvidenceView>("parameters");
  const [bodyVisibility, setBodyVisibility] = useState<BodyVisibility>({});
  const [draftValues, setDraftValues] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [toast, setToast] = useState<ToastState>(null);

  const unsavedCount = Object.keys(draftValues).length;

  async function openFirstProject() {
    setLoading(true);
    setError(null);
    try {
      const available = await listProjects();
      if (!available.length) throw new Error("No project manifest was found in the workspace.");
      setProjects(available);
      setProject(await loadProject(available[0].id));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unexpected project loading error.");
    } finally {
      setLoading(false);
    }
  }

  async function selectProject(projectId: string) {
    if (projectId === project?.manifest.project_id) return;
    setLoading(true);
    setError(null);
    try {
      setDraftValues({});
      setProject(await loadProject(projectId));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unexpected project loading error.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void openFirstProject();
  }, []);

  const activeProjectId = project?.manifest.project_id;
  useEffect(() => {
    if (!project) return;
    const bodies = renderableBodies(project);
    setBodyVisibility(Object.fromEntries(bodies.map((body) => [body, true])));
    // Reset body visibility only when the active project changes, not on every save.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeProjectId]);

  useEffect(() => {
    if (!toast) return;
    const timeout = window.setTimeout(() => setToast(null), 3600);
    return () => window.clearTimeout(timeout);
  }, [toast]);

  function updateDraft(name: string, value: number) {
    if (!project) return;
    setDraftValues((current) => {
      const next = { ...current };
      if (value === project.parameters[name]) delete next[name];
      else next[name] = value;
      return next;
    });
  }

  async function persistDraft() {
    if (!project || !unsavedCount) return;
    setSaving(true);
    try {
      const updated = await saveParameters(project.manifest.project_id, draftValues);
      setProject(updated);
      setDraftValues({});
      setToast({
        kind: "success",
        message: "Parameters saved. The project now requires an AI/MCP rebuild.",
      });
    } catch (caught) {
      setToast({
        kind: "error",
        message: caught instanceof Error ? caught.message : "Parameters could not be saved.",
      });
    } finally {
      setSaving(false);
    }
  }

  const rebuildPrompt = useMemo(() => {
    if (!project) return "";
    const changed = project.status.changedSources.join(", ") || "parameters";
    return [
      `Open the SolidIntent project '${project.manifest.project_id}'.`,
      `The saved ${changed} differ from accepted revision ${project.manifest.revision}.`,
      "Rebuild through build123d-mcp, compare against the accepted revision, validate every solid,",
      "run fit and FDM printability checks, regenerate STEP/STL and previews, then record a new revision.",
    ].join(" ");
  }, [project]);

  async function copyRebuildPrompt() {
    try {
      await navigator.clipboard.writeText(rebuildPrompt);
      setToast({ kind: "success", message: "AI rebuild prompt copied to the clipboard." });
    } catch {
      setToast({ kind: "error", message: "The browser could not access the clipboard." });
    }
  }

  if (loading) return <LoadingShell />;
  if (error) return <ErrorShell message={error} onRetry={() => void openFirstProject()} />;
  if (!project) return null;

  return (
    <div className="app-shell">
      <ProjectHeader
        project={project}
        projects={projects}
        unsavedCount={unsavedCount}
        onSelectProject={(id) => void selectProject(id)}
        onCopyRebuildPrompt={() => void copyRebuildPrompt()}
      />
      <main className="workspace" id="main-content">
        <ContextRail
          project={project}
          selectedView={selectedView}
          bodyVisibility={bodyVisibility}
          onSelectView={setSelectedView}
          onToggleBody={(body) =>
            setBodyVisibility((current) => ({ ...current, [body]: current[body] === false }))
          }
        />
        <Suspense fallback={<ModelLoadingStage />}>
          <ModelViewer project={project} bodyVisibility={bodyVisibility} />
        </Suspense>
        <Inspector
          project={project}
          selectedView={selectedView}
          draftValues={draftValues}
          saving={saving}
          onDraftChange={updateDraft}
          onDiscard={() => setDraftValues({})}
          onSave={() => void persistDraft()}
          onCopyRebuildPrompt={() => void copyRebuildPrompt()}
        />
      </main>
      {toast ? (
        <div className={`toast toast--${toast.kind}`} role={toast.kind === "error" ? "alert" : "status"}>
          {toast.message}
        </div>
      ) : null}
    </div>
  );
}
