import type { ProjectData } from "./types";

const BODY_COLORS = ["#3d4541", "#555e5a", "#6c7772", "#828d88"];

export type SceneMode = "assembled" | "print";

function bodiesForMode(project: ProjectData, mode: SceneMode): string[] {
  return project.manifest.named_geometry.bodies.filter((body) =>
    mode === "print" ? body !== "lid" : body !== "lid_print",
  );
}

/**
 * Bodies declared by the manifest that also have a locally generated STL mesh.
 * Print-orientation mode swaps assembled ``lid`` for ``lid_print`` when present.
 */
export function renderableBodies(project: ProjectData, mode: SceneMode = "assembled"): string[] {
  return bodiesForMode(project, mode).filter(
    (body) => project.artifactAvailability[`${body}_stl`] === true,
  );
}

export function unavailableBodies(project: ProjectData, mode: SceneMode = "assembled"): string[] {
  return bodiesForMode(project, mode).filter(
    (body) => project.artifactAvailability[`${body}_stl`] !== true,
  );
}

export function bodyColor(index: number): string {
  return BODY_COLORS[index % BODY_COLORS.length];
}

export function bodyLabel(name: string): string {
  return name.replaceAll("_", " ").replace(/\b\w/g, (character) => character.toUpperCase());
}

export function validatedSolidCount(project: ProjectData): number {
  return Object.keys(project.validation.geometry ?? {}).length;
}
