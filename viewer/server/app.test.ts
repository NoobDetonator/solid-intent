import { mkdtempSync, rmSync } from "node:fs";
import { promises as fs } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";

import request from "supertest";
import { afterAll, beforeEach, describe, expect, it } from "vitest";

import { createApiApp, formatParameterValue, type ServerPaths } from "./app";

const PARAMETER_SCHEMA = {
  $schema: "https://json-schema.org/draft/2020-12/schema",
  type: "object",
  additionalProperties: false,
  required: ["wall_thickness", "pcb_length"],
  properties: {
    wall_thickness: {
      $ref: "#/$defs/editable_dimension",
      title: "Wall thickness",
      minimum: 1.2,
      maximum: 5.0,
      "x-step": 0.1,
      "x-ui": { group: "Base", order: 20, control: "slider" },
    },
    pcb_length: {
      $ref: "#/$defs/locked_dimension",
      title: "PCB length",
      minimum: 84.5,
      maximum: 85.5,
      "x-ui": { group: "Reference", order: 10 },
    },
  },
  $defs: {
    editable_dimension: {
      type: "number",
      "x-unit": "mm",
      "x-user-editable": true,
      "x-semantic-change": false,
    },
    locked_dimension: {
      type: "number",
      "x-unit": "mm",
      "x-user-editable": false,
      "x-semantic-change": true,
      "x-lock-reason": "Controlled by reference hardware",
    },
  },
};

async function writeJson(file: string, value: unknown): Promise<void> {
  await fs.mkdir(path.dirname(file), { recursive: true });
  await fs.writeFile(file, `${JSON.stringify(value, null, 2)}\n`, "utf8");
}

let root: string;
let paths: ServerPaths;

async function buildFixture(): Promise<void> {
  const projectDir = path.join(root, "projects", "sample_case");
  await fs.mkdir(projectDir, { recursive: true });
  await fs.writeFile(path.join(projectDir, "model.py"), "def build_model(p):\n    return {}\n");
  await fs.writeFile(path.join(root, "existing_artifact.stl"), "solid demo\nendsolid demo\n");

  await writeJson(path.join(projectDir, "parameter_schema.json"), PARAMETER_SCHEMA);
  await writeJson(path.join(projectDir, "parameters.json"), {
    pcb_length: 85.0,
    wall_thickness: 2.4,
  });
  await writeJson(path.join(projectDir, "references.json"), { references: [] });
  await writeJson(path.join(projectDir, "revisions", "index.json"), {
    revisions: [{ revision: 1, record: "0001.json" }],
  });
  await writeJson(path.join(projectDir, "revisions", "0001.json"), {
    revision: 1,
    status: "accepted",
    parameters_snapshot: { pcb_length: 85.0, wall_thickness: 2.4 },
  });
  await writeJson(path.join(projectDir, "validation.json"), {
    accepted_revision: 1,
    geometry: { base: {} },
    source_hashes_sha256: {},
  });
  await writeJson(path.join(projectDir, "project.json"), {
    schema_version: 1,
    format: "ai_cad_project",
    project_id: "sample_case",
    title: "Sample Case",
    status: "prototype",
    revision: 1,
    units: "mm",
    model: { source: "model.py", entrypoint: "build_model" },
    parameter_values: "parameters.json",
    parameter_schema: "parameter_schema.json",
    references: "references.json",
    validation: "validation.json",
    revision_index: "revisions/index.json",
    named_geometry: { bodies: ["base"], interfaces: [] },
    artifacts: {
      base_stl: "../../existing_artifact.stl",
      lid_stl: "../../missing_artifact.stl",
    },
  });
}

beforeEach(async () => {
  root = mkdtempSync(path.join(tmpdir(), "solidintent-"));
  paths = { repositoryRoot: root, projectsRoot: path.join(root, "projects") };
  await buildFixture();
});

afterAll(() => {
  if (root) rmSync(root, { recursive: true, force: true });
});

describe("formatParameterValue", () => {
  it("keeps a decimal for integers and drops float noise", () => {
    expect(formatParameterValue(85)).toBe("85.0");
    expect(formatParameterValue(1.25)).toBe("1.25");
    expect(formatParameterValue(0.1 + 0.2)).toBe("0.3");
  });
});

describe("project API", () => {
  it("lists projects", async () => {
    const response = await request(createApiApp(paths)).get("/api/projects");
    expect(response.status).toBe(200);
    expect(response.body.projects).toEqual([
      { id: "sample_case", title: "Sample Case", status: "prototype", revision: 1 },
    ]);
  });

  it("loads a project with derived counts and availability", async () => {
    const response = await request(createApiApp(paths)).get("/api/projects/sample_case");
    expect(response.status).toBe(200);
    expect(response.body.parameterCounts).toEqual({ total: 2, editable: 1, locked: 1 });
    expect(response.body.artifactAvailability).toEqual({ base_stl: true, lid_stl: false });
    expect(response.body.status.dirty).toBe(true); // empty accepted hashes
  });

  it("returns 404 for an unknown project", async () => {
    const response = await request(createApiApp(paths)).get("/api/projects/nope");
    expect(response.status).toBe(404);
  });

  it("returns 400 for an invalid project id", async () => {
    const response = await request(createApiApp(paths)).get("/api/projects/Bad-Id");
    expect(response.status).toBe(400);
  });
});

describe("parameter updates", () => {
  it("rejects locked parameters", async () => {
    const response = await request(createApiApp(paths))
      .put("/api/projects/sample_case/parameters")
      .send({ changes: { pcb_length: 85.2 } });
    expect(response.status).toBe(400);
    expect(response.body.error).toMatch(/reference hardware/);
  });

  it("rejects out-of-range values", async () => {
    const response = await request(createApiApp(paths))
      .put("/api/projects/sample_case/parameters")
      .send({ changes: { wall_thickness: 99 } });
    expect(response.status).toBe(400);
  });

  it("rejects unknown parameters and malformed bodies", async () => {
    const app = createApiApp(paths);
    expect(
      (await request(app).put("/api/projects/sample_case/parameters").send({ changes: { x: 1 } }))
        .status,
    ).toBe(400);
    expect(
      (await request(app).put("/api/projects/sample_case/parameters").send({})).status,
    ).toBe(400);
  });

  it("persists a valid edit with clean serialization", async () => {
    const response = await request(createApiApp(paths))
      .put("/api/projects/sample_case/parameters")
      .send({ changes: { wall_thickness: 3 } });
    expect(response.status).toBe(200);
    const file = await fs.readFile(
      path.join(paths.projectsRoot, "sample_case", "parameters.json"),
      "utf8",
    );
    expect(file).toContain('"wall_thickness": 3.0');
  });
});

describe("artifacts", () => {
  it("serves an existing artifact", async () => {
    const response = await request(createApiApp(paths)).get(
      "/api/projects/sample_case/artifacts/base_stl",
    );
    expect(response.status).toBe(200);
    expect(response.text).toContain("solid demo");
  });

  it("returns 404 for a missing artifact file", async () => {
    const response = await request(createApiApp(paths)).get(
      "/api/projects/sample_case/artifacts/lid_stl",
    );
    expect(response.status).toBe(404);
  });

  it("returns 404 for an unknown artifact key", async () => {
    const response = await request(createApiApp(paths)).get(
      "/api/projects/sample_case/artifacts/nope",
    );
    expect(response.status).toBe(404);
  });
});

describe("rebuild route", () => {
  it("returns 400 for an invalid project id", async () => {
    const response = await request(
      createApiApp(paths, {
        rebuildRunner: async () => ({ code: 0, stdout: "ok", stderr: "" }),
      }),
    )
      .post("/api/projects/Bad-Id/rebuild")
      .send({ accept: true });
    expect(response.status).toBe(400);
  });

  it("returns 404 for an unknown project", async () => {
    const response = await request(
      createApiApp(paths, {
        rebuildRunner: async () => ({ code: 0, stdout: "ok", stderr: "" }),
      }),
    )
      .post("/api/projects/missing_case/rebuild")
      .send({ accept: true });
    expect(response.status).toBe(404);
  });

  it("returns 409 when the project is clean and accept is omitted", async () => {
    const { createHash } = await import("node:crypto");
    const projectDir = path.join(paths.projectsRoot, "sample_case");
    const hashFile = async (filename: string) => {
      const content = await fs.readFile(filename);
      return createHash("sha256").update(content).digest("hex").toUpperCase();
    };
    await writeJson(path.join(projectDir, "validation.json"), {
      accepted_revision: 1,
      geometry: { base: {} },
      source_hashes_sha256: {
        model: await hashFile(path.join(projectDir, "model.py")),
        parameters: await hashFile(path.join(projectDir, "parameters.json")),
        parameter_schema: await hashFile(path.join(projectDir, "parameter_schema.json")),
      },
    });

    let called = false;
    const response = await request(
      createApiApp(paths, {
        rebuildRunner: async () => {
          called = true;
          return { code: 0, stdout: "ok", stderr: "" };
        },
      }),
    )
      .post("/api/projects/sample_case/rebuild")
      .send({});
    expect(response.status).toBe(409);
    expect(called).toBe(false);
  });

  it("returns 422 when the rebuild runner fails", async () => {
    const response = await request(
      createApiApp(paths, {
        rebuildRunner: async () => ({
          code: 2,
          stdout: "gate failed",
          stderr: "volume delta",
        }),
      }),
    )
      .post("/api/projects/sample_case/rebuild")
      .send({ accept: true });
    expect(response.status).toBe(422);
    expect(response.body.error).toMatch(/gates failed/i);
  });

  it("returns the project payload when rebuild succeeds", async () => {
    const response = await request(
      createApiApp(paths, {
        rebuildRunner: async (_root, projectId, options) => {
          expect(projectId).toBe("sample_case");
          expect(options.accept).toBe(true);
          expect(options.exportArtifacts).toBe(true);
          return { code: 0, stdout: "accepted revision 2", stderr: "" };
        },
      }),
    )
      .post("/api/projects/sample_case/rebuild")
      .send({ accept: true });
    expect(response.status).toBe(200);
    expect(response.body.ok).toBe(true);
    expect(response.body.project.manifest.project_id).toBe("sample_case");
  });
});
