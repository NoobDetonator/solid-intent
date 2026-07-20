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
} from "lucide-react";

import type { EvidenceView, ProjectData } from "../types";

export interface BodyVisibility {
  base: boolean;
  lid: boolean;
}

interface ContextRailProps {
  project: ProjectData;
  selectedView: EvidenceView;
  bodyVisibility: BodyVisibility;
  onSelectView: (view: EvidenceView) => void;
  onToggleBody: (body: keyof BodyVisibility) => void;
}

const evidenceItems: Array<{
  id: EvidenceView;
  label: string;
  icon: typeof SlidersHorizontal;
}> = [
  { id: "parameters", label: "Parameters", icon: SlidersHorizontal },
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
        <button
          className={`rail-row ${bodyVisibility.base ? "rail-row--selected" : ""}`}
          type="button"
          aria-label={`${bodyVisibility.base ? "Hide" : "Show"} base body`}
          aria-pressed={bodyVisibility.base}
          onClick={() => onToggleBody("base")}
        >
          <Box aria-hidden="true" />
          <span>Base</span>
          {bodyVisibility.base ? <Eye aria-hidden="true" /> : <EyeOff aria-hidden="true" />}
        </button>
        <button
          className={`rail-row ${bodyVisibility.lid ? "rail-row--selected" : ""}`}
          type="button"
          aria-label={`${bodyVisibility.lid ? "Hide" : "Show"} lid body`}
          aria-pressed={bodyVisibility.lid}
          onClick={() => onToggleBody("lid")}
        >
          <Box aria-hidden="true" />
          <span>Lid</span>
          {bodyVisibility.lid ? <Eye aria-hidden="true" /> : <EyeOff aria-hidden="true" />}
        </button>
        <button
          className="rail-row"
          type="button"
          aria-label="PCB proxy unavailable"
          disabled
          title="No PCB proxy mesh has been exported"
        >
          <LockKeyhole aria-hidden="true" />
          <span>PCB proxy</span>
          <span className="rail-unavailable">Unavailable</span>
        </button>
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
