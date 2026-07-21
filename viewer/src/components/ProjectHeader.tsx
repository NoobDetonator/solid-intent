import { Bot, CheckCircle2, ChevronDown, Copy, RefreshCw, TriangleAlert } from "lucide-react";

import type { ProjectData, ProjectSummary } from "../types";
import logoUrl from "../assets/solidintent_logo.png";

interface ProjectHeaderProps {
  project: ProjectData;
  projects: ProjectSummary[];
  unsavedCount: number;
  rebuilding: boolean;
  onSelectProject: (projectId: string) => void;
  onCopyRebuildPrompt: () => void;
  onRebuild: () => void;
}

export function ProjectHeader({
  project,
  projects,
  unsavedCount,
  rebuilding,
  onSelectProject,
  onCopyRebuildPrompt,
  onRebuild,
}: ProjectHeaderProps) {
  const dirty = project.status.dirty;
  const state = unsavedCount > 0 ? "unsaved" : dirty ? "dirty" : "validated";
  const multipleProjects = projects.length > 1;

  return (
    <header className="project-header">
      <div className="brand-lockup" aria-label="SolidIntent home">
        <img className="brand-logo" src={logoUrl} alt="SolidIntent" height={22} />
      </div>

      <div className="project-identity">
        {multipleProjects ? (
          <div className="project-select">
            <select
              aria-label="Active project"
              value={project.manifest.project_id}
              onChange={(event) => onSelectProject(event.currentTarget.value)}
            >
              {projects.map((summary) => (
                <option key={summary.id} value={summary.id}>
                  {summary.title}
                </option>
              ))}
            </select>
            <ChevronDown aria-hidden="true" />
          </div>
        ) : (
          <span className="project-title">{project.manifest.title}</span>
        )}
        <span className="header-separator" aria-hidden="true">/</span>
        <span className="revision-label">Revision {project.manifest.revision}</span>
      </div>

      <div className="header-actions">
        <span className={`status-label status-label--${state}`} role="status">
          {state === "validated" ? <CheckCircle2 aria-hidden="true" /> : <TriangleAlert aria-hidden="true" />}
          {state === "unsaved"
            ? `${unsavedCount} unsaved ${unsavedCount === 1 ? "change" : "changes"}`
            : state === "dirty"
              ? "Rebuild required"
              : "Validated"}
        </span>
        {dirty && unsavedCount === 0 ? (
          <>
            <button
              className="header-button"
              type="button"
              disabled={rebuilding}
              onClick={onCopyRebuildPrompt}
            >
              <Copy aria-hidden="true" />
              Copy rebuild prompt
            </button>
            <button
              className="header-button header-button--primary"
              type="button"
              disabled={rebuilding}
              aria-busy={rebuilding}
              onClick={onRebuild}
            >
              {rebuilding ? (
                <span className="button-progress" aria-hidden="true" />
              ) : (
                <RefreshCw aria-hidden="true" />
              )}
              {rebuilding ? "Rebuilding…" : "Rebuild & accept"}
            </button>
          </>
        ) : (
          <span className="agent-indicator" title="CAD operations are performed by the AI through MCP">
            <Bot aria-hidden="true" />
            AI-operated CAD
          </span>
        )}
      </div>
    </header>
  );
}
