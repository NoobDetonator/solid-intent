import { Bot, CheckCircle2, Copy, TriangleAlert } from "lucide-react";

import type { ProjectData } from "../types";

interface ProjectHeaderProps {
  project: ProjectData;
  unsavedCount: number;
  onCopyRebuildPrompt: () => void;
}

export function ProjectHeader({
  project,
  unsavedCount,
  onCopyRebuildPrompt,
}: ProjectHeaderProps) {
  const dirty = project.status.dirty;
  const state = unsavedCount > 0 ? "unsaved" : dirty ? "dirty" : "validated";

  return (
    <header className="project-header">
      <div className="brand-lockup" aria-label="SolidIntent home">
        <span className="brand-mark" aria-hidden="true">
          <span />
          <span />
          <span />
        </span>
        <span className="brand-name">SolidIntent</span>
      </div>

      <div className="project-identity">
        <span className="project-title">{project.manifest.title}</span>
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
          <button className="header-button" type="button" onClick={onCopyRebuildPrompt}>
            <Copy aria-hidden="true" />
            Copy rebuild prompt
          </button>
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
