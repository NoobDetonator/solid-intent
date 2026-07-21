import type { ProjectData } from "./types";

const BODY_COLORS = ["#3d4541", "#555e5a", "#6c7772", "#828d88"];

/**
 * Bodies declared by the manifest that also have a locally generated STL mesh.
 * Print-orientation duplicates and interface proxies without a mesh artifact
 * are intentionally excluded from the interactive scene.
 */
export function renderableBodies(project: ProjectData): string[] {
  return project.manifest.named_geometry.bodies.filter(
    (body) => project.artifactAvailability[`${body}_stl`] === true,
  );
}

export function unavailableBodies(project: ProjectData): string[] {
  return project.manifest.named_geometry.bodies.filter(
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
