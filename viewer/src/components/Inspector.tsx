import { useMemo, useState } from "react";
import {
  AlertTriangle,
  Check,
  CheckCircle2,
  ChevronDown,
  Copy,
  Download,
  ExternalLink,
  FileWarning,
  LockKeyhole,
  RotateCcw,
  Save,
  Search,
} from "lucide-react";

import type {
  EvidenceView,
  ParameterDefinition,
  ParameterFilter,
  ProjectData,
} from "../types";

interface InspectorProps {
  project: ProjectData;
  selectedView: EvidenceView;
  draftValues: Record<string, number>;
  saving: boolean;
  onDraftChange: (name: string, value: number) => void;
  onDiscard: () => void;
  onSave: () => void;
  onCopyRebuildPrompt: () => void;
}

interface InspectorHeaderProps {
  title: string;
  description: string;
}

function InspectorHeader({ title, description }: InspectorHeaderProps) {
  return (
    <div className="inspector-heading">
      <div>
        <h1>{title}</h1>
        <p>{description}</p>
      </div>
    </div>
  );
}

function ParameterRow({
  definition,
  project,
  draftValue,
  onChange,
}: {
  definition: ParameterDefinition;
  project: ProjectData;
  draftValue: number | undefined;
  onChange: (name: string, value: number) => void;
}) {
  const currentValue = draftValue ?? definition.value;
  const acceptedValue = project.acceptedParameters[definition.name];
  const differsFromAccepted = currentValue !== acceptedValue;
  const inputId = `parameter-${definition.name}`;
  const useSlider =
    definition.userEditable &&
    definition.control === "slider" &&
    definition.minimum !== null &&
    definition.maximum !== null;

  function handleValue(value: number) {
    if (Number.isFinite(value)) onChange(definition.name, value);
  }

  return (
    <div className={`parameter-row ${draftValue !== undefined ? "parameter-row--changed" : ""}`}>
      <div className="parameter-label-block">
        <label htmlFor={inputId}>{definition.label}</label>
        <span className="parameter-name">{definition.name}</span>
        {definition.warning ? <span className="parameter-warning">{definition.warning}</span> : null}
      </div>

      <div className="parameter-control-block">
        {useSlider ? (
          <input
            className="parameter-slider"
            type="range"
            value={currentValue}
            min={definition.minimum ?? undefined}
            max={definition.maximum ?? undefined}
            step={definition.step ?? "any"}
            aria-label={`${definition.label} slider`}
            onChange={(event) => handleValue(event.currentTarget.valueAsNumber)}
          />
        ) : null}
        <div className="number-control">
          <input
            id={inputId}
            type="number"
            value={currentValue}
            min={definition.minimum ?? undefined}
            max={definition.maximum ?? undefined}
            step={definition.step ?? "any"}
            disabled={!definition.userEditable}
            aria-describedby={`${inputId}-meta`}
            onChange={(event) => handleValue(event.currentTarget.valueAsNumber)}
          />
          <span>{definition.unit}</span>
        </div>
        <div className="parameter-meta" id={`${inputId}-meta`}>
          {!definition.userEditable ? (
            <span className="locked-note">
              <LockKeyhole aria-hidden="true" />
              {definition.lockReason}
            </span>
          ) : differsFromAccepted ? (
            <span className="accepted-note">
              Accepted <span>{acceptedValue.toFixed(2)} {definition.unit}</span>
              <button
                type="button"
                className="param-reset"
                title={`Reset ${definition.label} to the accepted value`}
                aria-label={`Reset ${definition.label} to the accepted value`}
                onClick={() => handleValue(acceptedValue)}
              >
                <RotateCcw aria-hidden="true" />
              </button>
            </span>
          ) : definition.advanced ? (
            <span>Advanced control</span>
          ) : (
            <span>Accepted value</span>
          )}
        </div>
      </div>
    </div>
  );
}

function ParametersView({
  project,
  draftValues,
  saving,
  onDraftChange,
  onDiscard,
  onSave,
  onCopyRebuildPrompt,
}: Omit<InspectorProps, "selectedView">) {
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<ParameterFilter>("editable");
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [openGroups, setOpenGroups] = useState<Set<string>>(new Set(["Base", "Lid"]));
  const unsavedCount = Object.keys(draftValues).length;

  const advancedCount = useMemo(
    () => project.parameterCatalog.filter((item) => item.userEditable && item.advanced).length,
    [project.parameterCatalog],
  );

  const groups = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    const filtered = project.parameterCatalog.filter((definition) => {
      if (filter === "editable" && !definition.userEditable) return false;
      if (filter === "locked" && definition.userEditable) return false;
      // Advanced editable controls stay hidden until explicitly revealed,
      // unless a search query is active (search always spans everything).
      if (filter === "editable" && definition.advanced && !showAdvanced && !normalizedQuery) {
        return false;
      }
      if (!normalizedQuery) return true;
      return (
        definition.label.toLowerCase().includes(normalizedQuery) ||
        definition.name.toLowerCase().includes(normalizedQuery) ||
        definition.group.toLowerCase().includes(normalizedQuery)
      );
    });

    return filtered.reduce<Record<string, ParameterDefinition[]>>((result, definition) => {
      (result[definition.group] ??= []).push(definition);
      return result;
    }, {});
  }, [filter, project.parameterCatalog, query, showAdvanced]);

  function toggleGroup(group: string) {
    setOpenGroups((current) => {
      const next = new Set(current);
      if (next.has(group)) next.delete(group);
      else next.add(group);
      return next;
    });
  }

  return (
    <>
      <div className="inspector-sticky-top">
        <InspectorHeader
          title="Parameters"
          description={`${project.parameterCounts.total} named dimensions · ${project.parameterCounts.editable} user editable`}
        />
        <label className="search-field">
          <Search aria-hidden="true" />
          <span className="sr-only">Search parameters</span>
          <input
            type="search"
            value={query}
            placeholder="Search parameters"
            onChange={(event) => setQuery(event.currentTarget.value)}
          />
        </label>
        <div className="segmented-control" aria-label="Parameter access filter">
          <button
            type="button"
            className={filter === "editable" ? "is-selected" : ""}
            aria-pressed={filter === "editable"}
            onClick={() => setFilter("editable")}
          >
            Editable <span>{project.parameterCounts.editable}</span>
          </button>
          <button
            type="button"
            className={filter === "locked" ? "is-selected" : ""}
            aria-pressed={filter === "locked"}
            onClick={() => setFilter("locked")}
          >
            Locked <span>{project.parameterCounts.locked}</span>
          </button>
        </div>
        {filter === "editable" && advancedCount > 0 ? (
          <label className="advanced-toggle">
            <input
              type="checkbox"
              checked={showAdvanced}
              onChange={(event) => setShowAdvanced(event.currentTarget.checked)}
            />
            <span>Show advanced controls</span>
            <span className="advanced-toggle-count">{advancedCount}</span>
          </label>
        ) : null}
      </div>

      <div className="parameter-groups">
        {Object.entries(groups).length ? (
          Object.entries(groups).map(([group, definitions]) => {
            const expanded = query.length > 0 || openGroups.has(group);
            return (
              <section className="parameter-group" key={group}>
                <button
                  className="parameter-group-toggle"
                  type="button"
                  aria-expanded={expanded}
                  onClick={() => toggleGroup(group)}
                >
                  <span>{group}</span>
                  <span>{definitions.length}</span>
                  <ChevronDown aria-hidden="true" />
                </button>
                {expanded ? (
                  <div className="parameter-list">
                    {definitions.map((definition) => (
                      <ParameterRow
                        key={definition.name}
                        definition={definition}
                        project={project}
                        draftValue={draftValues[definition.name]}
                        onChange={onDraftChange}
                      />
                    ))}
                  </div>
                ) : null}
              </section>
            );
          })
        ) : (
          <div className="inspector-empty">
            <Search aria-hidden="true" />
            <strong>No matching parameters</strong>
            <span>Try a parameter name, group, or change the access filter.</span>
          </div>
        )}
      </div>

      <div className="inspector-actions">
        {unsavedCount > 0 ? (
          <div className="change-state change-state--unsaved" role="status">
            <FileWarning aria-hidden="true" />
            <div>
              <strong>{unsavedCount} unsaved {unsavedCount === 1 ? "change" : "changes"}</strong>
              <span>Save the parameter set before asking the AI to rebuild.</span>
            </div>
          </div>
        ) : project.status.dirty ? (
          <div className="change-state change-state--dirty" role="status">
            <AlertTriangle aria-hidden="true" />
            <div>
              <strong>Rebuild required</strong>
              <span>Saved parameters no longer match the accepted geometry.</span>
            </div>
          </div>
        ) : (
          <div className="change-state change-state--clean" role="status">
            <CheckCircle2 aria-hidden="true" />
            <div>
              <strong>Project is validated</strong>
              <span>Parameters and generated geometry match revision {project.manifest.revision}.</span>
            </div>
          </div>
        )}

        <div className="action-row">
          {project.status.dirty && unsavedCount === 0 ? (
            <button className="button button--secondary" type="button" onClick={onCopyRebuildPrompt}>
              <Copy aria-hidden="true" />
              Copy AI prompt
            </button>
          ) : (
            <button
              className="button button--secondary"
              type="button"
              disabled={unsavedCount === 0 || saving}
              onClick={onDiscard}
            >
              <RotateCcw aria-hidden="true" />
              Discard
            </button>
          )}
          <button
            className="button button--primary"
            type="button"
            disabled={unsavedCount === 0 || saving}
            aria-busy={saving}
            onClick={onSave}
          >
            {saving ? <span className="button-progress" aria-hidden="true" /> : <Save aria-hidden="true" />}
            {saving ? "Saving" : "Save parameters"}
          </button>
        </div>
      </div>
    </>
  );
}

function DrawingsView({ project }: { project: ProjectData }) {
  const previewKeys = ["assembled_preview", "exploded_preview", "dimensioned_drawing"] as const;
  const sheets = previewKeys
    .filter((key) => project.manifest.artifacts[key] && project.artifactAvailability[key])
    .map((key) => ({
      key,
      label: key.replaceAll("_", " "),
      href: `/api/projects/${project.manifest.project_id}/artifacts/${key}`,
    }));
  const downloads = Object.entries(project.manifest.artifacts ?? {})
    .filter(([key]) => project.artifactAvailability[key])
    .filter(([key]) => /\.(svg|dxf|png)$/i.test(project.manifest.artifacts[key]))
    .map(([key, relativePath]) => ({
      key,
      label: key.replaceAll("_", " "),
      extension: (relativePath.split(".").pop() ?? "").toUpperCase(),
      href: `/api/projects/${project.manifest.project_id}/artifacts/${key}`,
    }));

  return (
    <>
      <InspectorHeader
        title="Drawings"
        description="Technical SVG previews and the dimensioned sheet. Visuals are review aids, not geometric proof."
      />
      <div className="evidence-content">
        {sheets.length ? (
          sheets.map((sheet) => (
            <section className="evidence-section drawing-sheet" key={sheet.key}>
              <div className="evidence-section-heading">
                <h2>{sheet.label}</h2>
                <a className="source-link" href={sheet.href} target="_blank" rel="noreferrer">
                  Open <ExternalLink aria-hidden="true" />
                </a>
              </div>
              <div className="drawing-frame">
                <img src={sheet.href} alt={sheet.label} loading="lazy" />
              </div>
            </section>
          ))
        ) : (
          <div className="inspector-empty">
            <FileWarning aria-hidden="true" />
            <strong>No local drawing artifacts</strong>
            <span>
              Run <code>scripts/export_artifacts.py {project.manifest.project_id}</code> to
              regenerate SVG previews and drawings.
            </span>
          </div>
        )}

        {downloads.length ? (
          <section className="evidence-section evidence-section--exports">
            <div className="evidence-section-heading"><h2>Drawing files</h2></div>
            <ul className="download-list">
              {downloads.map((download) => (
                <li key={download.key}>
                  <a href={download.href} download>
                    <Download aria-hidden="true" />
                    <span className="download-label">{download.label}</span>
                    <span className="download-ext">{download.extension}</span>
                  </a>
                </li>
              ))}
            </ul>
          </section>
        ) : null}
      </div>
    </>
  );
}

function ValidationView({ project }: { project: ProjectData }) {
  const validation = project.validation;
  return (
    <>
      <InspectorHeader
        title="Validation"
        description={`Accepted revision ${validation.accepted_revision} · ${validation.executor}`}
      />
      <div className="evidence-content">
        <div className="evidence-summary evidence-summary--pass">
          <CheckCircle2 aria-hidden="true" />
          <div>
            <strong>Exact geometry gates passed</strong>
            <span>Validated {validation.validated_at}; visual preview is not used as proof.</span>
          </div>
        </div>

        {Object.entries(validation.geometry).map(([name, geometry]) => (
          <section className="evidence-section" key={name}>
            <div className="evidence-section-heading">
              <h2>{name}</h2>
              <span className="mini-status mini-status--pass">
                <Check aria-hidden="true" /> {geometry.validate}
              </span>
            </div>
            <dl className="metric-list">
              <div><dt>Envelope</dt><dd>{geometry.bbox_mm.join(" × ")} mm</dd></div>
              <div><dt>Volume</dt><dd>{geometry.volume_mm3.toLocaleString(undefined, { maximumFractionDigits: 3 })} mm³</dd></div>
              <div><dt>Topology</dt><dd>{geometry.topology.faces} F · {geometry.topology.edges} E · {geometry.topology.vertices} V</dd></div>
              <div><dt>Solid</dt><dd>{geometry.single_solid ? "Single" : "Multiple"}</dd></div>
              <div><dt>Watertight</dt><dd>{geometry.watertight_manifold ? "Yes" : "No"}</dd></div>
            </dl>
          </section>
        ))}

        <section className="evidence-section">
          <div className="evidence-section-heading"><h2>Interfaces</h2></div>
          <dl className="metric-list">
            {Object.entries(validation.interfaces).map(([name, fit]) => (
              <div key={name}>
                <dt>{name.replaceAll("_", " ")}</dt>
                <dd>{fit.status} · {fit.intersection_volume_mm3} mm³ overlap</dd>
              </div>
            ))}
          </dl>
        </section>

        <section className="evidence-section evidence-section--risks">
          <div className="evidence-section-heading">
            <h2>Physical verification</h2>
            <span className="mini-status mini-status--warning"><AlertTriangle aria-hidden="true" /> Required</span>
          </div>
          <ul>
            {validation.residual_risks.map((risk) => <li key={risk}>{risk}</li>)}
          </ul>
        </section>

        <ExportsSection project={project} />
      </div>
    </>
  );
}

function ExportsSection({ project }: { project: ProjectData }) {
  const downloads = Object.entries(project.manifest.artifacts ?? {})
    .filter(([key]) => project.artifactAvailability[key])
    .map(([key, relativePath]) => ({
      key,
      label: key.replaceAll("_", " "),
      extension: (relativePath.split(".").pop() ?? "").toUpperCase(),
      href: `/api/projects/${project.manifest.project_id}/artifacts/${key}`,
    }));

  return (
    <section className="evidence-section evidence-section--exports">
      <div className="evidence-section-heading"><h2>Exports</h2></div>
      {downloads.length ? (
        <ul className="download-list">
          {downloads.map((download) => (
            <li key={download.key}>
              <a href={download.href} download>
                <Download aria-hidden="true" />
                <span className="download-label">{download.label}</span>
                <span className="download-ext">{download.extension}</span>
              </a>
            </li>
          ))}
        </ul>
      ) : (
        <p className="exports-empty">
          No neutral CAD artifacts are available locally. Regenerate them with
          <code>scripts/export_artifacts.py</code> or build123d-mcp.
        </p>
      )}
    </section>
  );
}

function ReferencesView({ project }: { project: ProjectData }) {
  return (
    <>
      <InspectorHeader
        title="References"
        description="Evidence is ranked by provenance and never silently transferred between board generations."
      />
      <div className="evidence-content">
        {project.references.references.map((reference) => (
          <article className="reference-item" key={reference.id}>
            <div className="reference-heading">
              <div>
                <h2>{reference.id.replaceAll("_", " ")}</h2>
                <span>{reference.kind.replaceAll("_", " ")}</span>
              </div>
              <span className="reference-license">{reference.license_status}</span>
            </div>
            <dl className="metric-list">
              <div><dt>Trust class</dt><dd>{reference.trust_class.replaceAll("_", " ")}</dd></div>
              <div><dt>Author</dt><dd>{reference.author ?? "Not recorded"}</dd></div>
              <div><dt>Redistributed</dt><dd>{reference.redistributed ? "Yes" : "No"}</dd></div>
            </dl>
            {reference.source_url ? (
              <a className="source-link" href={reference.source_url} target="_blank" rel="noreferrer">
                Open source record <ExternalLink aria-hidden="true" />
              </a>
            ) : null}
          </article>
        ))}
      </div>
    </>
  );
}

function WorkingChangesSection({ project }: { project: ProjectData }) {
  const meta = new Map(project.parameterCatalog.map((item) => [item.name, item]));
  const parameterDiffs = Object.entries(project.parameters)
    .filter(([name, value]) => project.acceptedParameters[name] !== value)
    .map(([name, value]) => ({
      name,
      label: meta.get(name)?.label ?? name,
      unit: meta.get(name)?.unit ?? "",
      accepted: project.acceptedParameters[name],
      current: value,
    }));
  const changedSources = project.status.changedSources;

  if (!project.status.dirty) {
    return (
      <section className="evidence-section working-changes">
        <div className="evidence-summary evidence-summary--pass">
          <CheckCircle2 aria-hidden="true" />
          <div>
            <strong>Matches accepted revision {project.manifest.revision}</strong>
            <span>The working sources are identical to the accepted geometry.</span>
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className="evidence-section working-changes">
      <div className="evidence-section-heading">
        <h2>Changes since revision {project.manifest.revision}</h2>
        <span className="mini-status mini-status--warning">
          <AlertTriangle aria-hidden="true" /> Rebuild
        </span>
      </div>
      <dl className="metric-list">
        <div>
          <dt>Changed sources</dt>
          <dd>{changedSources.map((source) => source.replaceAll("_", " ")).join(", ")}</dd>
        </div>
      </dl>
      {parameterDiffs.length ? (
        <table className="diff-table">
          <thead>
            <tr>
              <th>Parameter</th>
              <th>Accepted</th>
              <th>Current</th>
            </tr>
          </thead>
          <tbody>
            {parameterDiffs.map((diff) => (
              <tr key={diff.name}>
                <td>{diff.label}</td>
                <td>{diff.accepted?.toFixed(2)} {diff.unit}</td>
                <td className="diff-current">{diff.current.toFixed(2)} {diff.unit}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <p className="diff-note">
          No parameter values differ; only the model source or schema changed.
        </p>
      )}
    </section>
  );
}

function RevisionsView({ project }: { project: ProjectData }) {
  return (
    <>
      <InspectorHeader
        title="Revisions"
        description="Accepted project states retain parameters, source hashes, and validation evidence."
      />
      <div className="evidence-content">
        <WorkingChangesSection project={project} />
        {project.revisions
          .slice()
          .sort((a, b) => b.revision - a.revision)
          .map((revision) => (
            <article className="revision-item" key={revision.revision}>
              <div className="revision-marker" aria-hidden="true">{revision.revision}</div>
              <div>
                <div className="revision-heading">
                  <h2>Revision {revision.revision}</h2>
                  <span className="mini-status mini-status--pass">{revision.status}</span>
                </div>
                <p>{revision.summary}</p>
                <span className="revision-meta">{revision.created_at} · {revision.authoring_agent}</span>
                <details>
                  <summary>View change record</summary>
                  <ul>{revision.changes.map((change) => <li key={change}>{change}</li>)}</ul>
                </details>
              </div>
            </article>
          ))}
      </div>
    </>
  );
}

export function Inspector(props: InspectorProps) {
  return (
    <aside className="inspector" aria-label={`${props.selectedView} inspector`}>
      {props.selectedView === "parameters" ? <ParametersView {...props} /> : null}
      {props.selectedView === "drawings" ? <DrawingsView project={props.project} /> : null}
      {props.selectedView === "validation" ? <ValidationView project={props.project} /> : null}
      {props.selectedView === "references" ? <ReferencesView project={props.project} /> : null}
      {props.selectedView === "revisions" ? <RevisionsView project={props.project} /> : null}
    </aside>
  );
}
