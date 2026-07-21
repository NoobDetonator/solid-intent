import {
  Box,
  ChevronRight,
  Eye,
  EyeOff,
  FileSearch,
  History,
  Link2,
  LockKeyhole,
  ShieldCheck,
  SlidersHorizontal,
  SquarePen,
} from "lucide-react";

import type { EvidenceView, ProjectData } from "../types";
import { bodyLabel, renderableBodies, unavailableBodies } from "../bodies";

export type BodyVisibility = Record<string, boolean>;

interface ContextRailProps {
  project: ProjectData;
  selectedView: EvidenceView;
  bodyVisibility: BodyVisibility;
  onSelectView: (view: EvidenceView) => void;
  onToggleBody: (body: string) => void;
}

const evidenceItems: Array<{
  id: EvidenceView;
  label: string;
  icon: typeof SlidersHorizontal;
}> = [
  { id: "parameters", label: "Parameters", icon: SlidersHorizontal },
  { id: "drawings", label: "Drawings", icon: SquarePen },
  { id: "validation", label: "Validation", icon: ShieldCheck },
  { id: "references", label: "References", icon: Link2 },
  { id: "revisions", label: "Revisions", icon: History },
];

export function ContextRail({
  project,
  selectedView,
  bodyVisibility,
  onSelectView,
  onToggleBody,
}: ContextRailProps) {
  const bodies = renderableBodies(project);
  const missingBodies = unavailableBodies(project);

  return (
    <nav className="context-rail" aria-label="Project workspace">
      <div className="rail-project">
        <span className="rail-heading">Project</span>
        <div className="rail-project-row">
          <FileSearch aria-hidden="true" />
          <span>{project.manifest.title}</span>
          <ChevronRight aria-hidden="true" />
        </div>
      </div>

      <div className="rail-section">
        <span className="rail-heading">Bodies</span>
        {bodies.map((body) => {
          const visible = bodyVisibility[body] !== false;
          return (
            <button
              className={`rail-row ${visible ? "rail-row--selected" : ""}`}
              type="button"
              key={body}
              aria-label={`${visible ? "Hide" : "Show"} ${bodyLabel(body)} body`}
              aria-pressed={visible}
              onClick={() => onToggleBody(body)}
            >
              <Box aria-hidden="true" />
              <span>{bodyLabel(body)}</span>
              {visible ? <Eye aria-hidden="true" /> : <EyeOff aria-hidden="true" />}
            </button>
          );
        })}
        {missingBodies.map((body) => (
          <button
            className="rail-row"
            type="button"
            key={body}
            aria-label={`${bodyLabel(body)} body unavailable`}
            disabled
            title="No local mesh has been exported for this body"
          >
            <LockKeyhole aria-hidden="true" />
            <span>{bodyLabel(body)}</span>
            <span className="rail-unavailable">Unavailable</span>
          </button>
        ))}
      </div>

      <div className="rail-section rail-section--evidence">
        <span className="rail-heading">Evidence</span>
        {evidenceItems.map((item) => {
          const Icon = item.icon;
          return (
            <button
              className={`rail-row ${selectedView === item.id ? "rail-row--active" : ""}`}
              type="button"
              aria-label={`Open ${item.label}`}
              aria-current={selectedView === item.id ? "page" : undefined}
              onClick={() => onSelectView(item.id)}
              key={item.id}
            >
              <Icon aria-hidden="true" />
              <span>{item.label}</span>
              {item.id === "parameters" ? (
                <span className="rail-count">{project.parameterCounts.total}</span>
              ) : null}
            </button>
          );
        })}
      </div>
    </nav>
  );
}
