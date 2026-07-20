export type EvidenceView = "parameters" | "validation" | "references" | "revisions";
export type ParameterFilter = "editable" | "locked";

export interface ProjectSummary {
  id: string;
  title: string;
  status: string;
  revision: number;
}

export interface ParameterDefinition {
  name: string;
  label: string;
  value: number;
  type: string;
  unit: string;
  minimum: number | null;
  maximum: number | null;
  step: number | null;
  userEditable: boolean;
  semanticChange: boolean;
  lockReason: string | null;
  group: string;
  order: number;
  control: string;
  advanced: boolean;
  warning: string | null;
}

export interface GeometryValidation {
  validate: string;
  single_solid: boolean;
  watertight_manifold: boolean;
  brep_valid: boolean;
  volume_mm3: number;
  bbox_mm: [number, number, number];
  topology: { faces: number; edges: number; vertices: number };
}

export interface ValidationRecord {
  accepted_revision: number;
  validated_at: string;
  executor: string;
  runtime: Record<string, string>;
  parameter_contract: Record<string, string | number>;
  geometry: Record<string, GeometryValidation>;
  interfaces: Record<
    string,
    { status: string; clearance_mm: number; intersection_volume_mm3: number }
  >;
  printability: Record<string, Record<string, string | number>>;
  residual_risks: string[];
}

export interface ReferenceRecord {
  id: string;
  kind: string;
  trust_class: string;
  author?: string;
  source_url?: string;
  license_status: string;
  redistributed: boolean;
  use?: string[];
  limitations?: string[];
}

export interface RevisionRecord {
  revision: number;
  status: string;
  created_at: string;
  authoring_agent: string;
  summary: string;
  changes: string[];
}

export interface ProjectData {
  manifest: {
    project_id: string;
    title: string;
    description: string;
    status: string;
    revision: number;
    units: string;
    named_geometry: { bodies: string[]; interfaces: string[] };
  };
  parameters: Record<string, number>;
  acceptedParameters: Record<string, number>;
  parameterCatalog: ParameterDefinition[];
  validation: ValidationRecord;
  references: { references: ReferenceRecord[] };
  revisions: RevisionRecord[];
  status: {
    dirty: boolean;
    changedSources: string[];
    currentHashes: Record<string, string>;
    acceptedHashes: Record<string, string>;
  };
  artifactAvailability: Record<string, boolean>;
  parameterCounts: { total: number; editable: number; locked: number };
}
