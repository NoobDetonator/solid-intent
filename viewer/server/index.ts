import { createHash } from "node:crypto";
import { promises as fs } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import express, { type NextFunction, type Request, type Response } from "express";
import { createServer as createViteServer } from "vite";

type JsonObject = Record<string, unknown>;

const serverDirectory = path.dirname(fileURLToPath(import.meta.url));
const viewerRoot = path.resolve(serverDirectory, "..");
const repositoryRoot = path.resolve(viewerRoot, "..");
const projectsRoot = path.join(repositoryRoot, "projects");
const production = process.argv.includes("--production");
const port = Number(process.env.PORT ?? 4173);

async function readJson<T>(filename: string): Promise<T> {
  return JSON.parse(await fs.readFile(filename, "utf8")) as T;
}

function assertProjectId(projectId: string): void {
  if (!/^[a-z0-9_]+$/.test(projectId)) {
    throw new Error("Invalid project identifier.");
  }
}

function resolveInside(root: string, candidate: string): string {
  const resolved = path.resolve(root, candidate);
  if (resolved !== root && !resolved.startsWith(`${root}${path.sep}`)) {
    throw new Error("Resolved path escapes the allowed project workspace.");
  }
  return resolved;
}

function resolveWorkspaceReference(baseDirectory: string, candidate: string): string {
  const resolved = path.resolve(baseDirectory, candidate);
  if (
    resolved !== repositoryRoot &&
    !resolved.startsWith(`${repositoryRoot}${path.sep}`)
  ) {
    throw new Error("Resolved path escapes the allowed project workspace.");
  }
  return resolved;
}

async function hashFile(filename: string): Promise<string> {
  const content = await fs.readFile(filename);
  return createHash("sha256").update(content).digest("hex").toUpperCase();
}

async function fileExists(filename: string): Promise<boolean> {
  try {
    await fs.access(filename);
    return true;
  } catch {
    return false;
  }
}

function resolveParameterDefinition(schema: JsonObject, name: string): JsonObject {
  const properties = schema.properties as Record<string, JsonObject>;
  const property = properties[name];
  const reference = property.$ref;
  if (typeof reference !== "string") return property;

  const definitionName = reference.split("/").at(-1);
  const definitions = schema.$defs as Record<string, JsonObject>;
  const inherited = definitionName ? definitions[definitionName] : undefined;
  if (!inherited) throw new Error(`Unknown parameter definition for ${name}.`);

  return {
    ...inherited,
    ...property,
    "x-ui": {
      ...((inherited["x-ui"] as JsonObject | undefined) ?? {}),
      ...((property["x-ui"] as JsonObject | undefined) ?? {}),
    },
  };
}

function buildParameterCatalog(schema: JsonObject, parameters: Record<string, number>) {
  return Object.entries(parameters)
    .map(([name, value]) => {
      const definition = resolveParameterDefinition(schema, name);
      const ui = (definition["x-ui"] as JsonObject | undefined) ?? {};
      return {
        name,
        label: String(definition.title ?? name),
        value,
        type: String(definition.type ?? "number"),
        unit: String(definition["x-unit"] ?? ""),
        minimum: typeof definition.minimum === "number" ? definition.minimum : null,
        maximum: typeof definition.maximum === "number" ? definition.maximum : null,
        step: typeof definition["x-step"] === "number" ? definition["x-step"] : null,
        userEditable: definition["x-user-editable"] === true,
        semanticChange: definition["x-semantic-change"] === true,
        lockReason:
          typeof definition["x-lock-reason"] === "string"
            ? definition["x-lock-reason"]
            : null,
        group: String(ui.group ?? "Other"),
        order: typeof ui.order === "number" ? ui.order : 9999,
        control: String(ui.control ?? "number"),
        advanced: ui.advanced === true,
        warning: typeof ui.warning === "string" ? ui.warning : null,
      };
    })
    .sort((a, b) => a.order - b.order);
}

function serializeParameters(parameters: Record<string, number>): string {
  const lines = Object.entries(parameters).map(([name, value]) => {
    const serializedValue = Number.isInteger(value) ? value.toFixed(1) : String(value);
    return `  ${JSON.stringify(name)}: ${serializedValue}`;
  });
  return `{\n${lines.join(",\n")}\n}\n`;
}

async function loadProject(projectId: string) {
  assertProjectId(projectId);
  const projectDirectory = resolveInside(projectsRoot, projectId);
  const manifestPath = path.join(projectDirectory, "project.json");
  const manifest = await readJson<JsonObject>(manifestPath);

  const parameterPath = resolveInside(projectDirectory, String(manifest.parameter_values));
  const schemaPath = resolveInside(projectDirectory, String(manifest.parameter_schema));
  const validationPath = resolveInside(projectDirectory, String(manifest.validation));
  const referencesPath = resolveInside(projectDirectory, String(manifest.references));
  const revisionIndexPath = resolveInside(projectDirectory, String(manifest.revision_index));
  const model = manifest.model as JsonObject;
  const modelPath = resolveWorkspaceReference(projectDirectory, String(model.source));

  const [parameters, schema, validation, references, revisionIndex] = await Promise.all([
    readJson<Record<string, number>>(parameterPath),
    readJson<JsonObject>(schemaPath),
    readJson<JsonObject>(validationPath),
    readJson<JsonObject>(referencesPath),
    readJson<JsonObject>(revisionIndexPath),
  ]);

  const revisionDirectory = path.dirname(revisionIndexPath);
  const revisionEntries = revisionIndex.revisions as Array<JsonObject>;
  const revisions = await Promise.all(
    revisionEntries.map((entry) =>
      readJson<JsonObject>(resolveInside(revisionDirectory, String(entry.record))),
    ),
  );
  const acceptedRevision = revisions.find(
    (revision) => revision.revision === validation.accepted_revision,
  );
  const acceptedParameters =
    (acceptedRevision?.parameters_snapshot as Record<string, number> | undefined) ?? parameters;

  const currentHashes = {
    model: await hashFile(modelPath),
    parameters: await hashFile(parameterPath),
    parameter_schema: await hashFile(schemaPath),
  };
  const acceptedHashes = validation.source_hashes_sha256 as Record<string, string>;
  const changedSources = Object.entries(currentHashes)
    .filter(([key, value]) => acceptedHashes[key] !== value)
    .map(([key]) => key);

  const artifacts = manifest.artifacts as Record<string, string>;
  const artifactAvailability = Object.fromEntries(
    await Promise.all(
      Object.entries(artifacts).map(async ([key, relativePath]) => [
        key,
        await fileExists(resolveWorkspaceReference(projectDirectory, relativePath)),
      ]),
    ),
  );

  const parameterCatalog = buildParameterCatalog(schema, parameters);

  return {
    manifest,
    parameters,
    acceptedParameters,
    parameterCatalog,
    validation,
    references,
    revisions,
    status: {
      dirty: changedSources.length > 0,
      changedSources,
      currentHashes,
      acceptedHashes,
    },
    artifactAvailability,
    parameterCounts: {
      total: parameterCatalog.length,
      editable: parameterCatalog.filter((item) => item.userEditable).length,
      locked: parameterCatalog.filter((item) => !item.userEditable).length,
    },
  };
}

async function updateParameters(projectId: string, changes: Record<string, unknown>) {
  assertProjectId(projectId);
  const projectDirectory = resolveInside(projectsRoot, projectId);
  const manifest = await readJson<JsonObject>(path.join(projectDirectory, "project.json"));
  const parameterPath = resolveInside(projectDirectory, String(manifest.parameter_values));
  const schemaPath = resolveInside(projectDirectory, String(manifest.parameter_schema));
  const parameters = await readJson<Record<string, number>>(parameterPath);
  const schema = await readJson<JsonObject>(schemaPath);

  for (const [name, rawValue] of Object.entries(changes)) {
    if (!(name in parameters)) throw new Error(`Unknown parameter: ${name}`);
    const definition = resolveParameterDefinition(schema, name);
    if (definition["x-user-editable"] !== true) {
      throw new Error(`${name} is controlled by reference hardware and cannot be edited here.`);
    }
    if (typeof rawValue !== "number" || !Number.isFinite(rawValue)) {
      throw new Error(`${name} must be a finite number.`);
    }
    if (typeof definition.minimum === "number" && rawValue < definition.minimum) {
      throw new Error(`${name} must be at least ${definition.minimum}.`);
    }
    if (typeof definition.maximum === "number" && rawValue > definition.maximum) {
      throw new Error(`${name} must be at most ${definition.maximum}.`);
    }
    parameters[name] = rawValue;
  }

  const temporaryPath = `${parameterPath}.viewer-${process.pid}-${Date.now()}.tmp`;
  await fs.writeFile(temporaryPath, serializeParameters(parameters), "utf8");
  await fs.rename(temporaryPath, parameterPath);
  return loadProject(projectId);
}

const app = express();
app.disable("x-powered-by");
app.use(express.json({ limit: "32kb" }));

app.get("/api/projects", async (_request, response, next) => {
  try {
    const entries = await fs.readdir(projectsRoot, { withFileTypes: true });
    const projects = [];
    for (const entry of entries) {
      if (!entry.isDirectory()) continue;
      const manifestPath = path.join(projectsRoot, entry.name, "project.json");
      if (!await fileExists(manifestPath)) continue;
      const manifest = await readJson<JsonObject>(manifestPath);
      projects.push({
        id: String(manifest.project_id),
        title: String(manifest.title),
        status: String(manifest.status),
        revision: Number(manifest.revision),
      });
    }
    response.json({ projects });
  } catch (error) {
    next(error);
  }
});

app.get("/api/projects/:projectId", async (request, response, next) => {
  try {
    response.json(await loadProject(request.params.projectId));
  } catch (error) {
    next(error);
  }
});

app.put("/api/projects/:projectId/parameters", async (request, response, next) => {
  try {
    const changes = request.body?.changes;
    if (!changes || typeof changes !== "object" || Array.isArray(changes)) {
      response.status(400).json({ error: "Request body must contain a changes object." });
      return;
    }
    response.json(await updateParameters(request.params.projectId, changes));
  } catch (error) {
    next(error);
  }
});

app.get("/api/projects/:projectId/artifacts/:artifactKey", async (request, response, next) => {
  try {
    assertProjectId(request.params.projectId);
    const projectDirectory = resolveInside(projectsRoot, request.params.projectId);
    const manifest = await readJson<JsonObject>(path.join(projectDirectory, "project.json"));
    const artifacts = manifest.artifacts as Record<string, string>;
    const relativePath = artifacts[request.params.artifactKey];
    if (!relativePath) {
      response.status(404).json({ error: "Unknown artifact." });
      return;
    }
    const filename = resolveWorkspaceReference(projectDirectory, relativePath);
    if (!await fileExists(filename)) {
      response.status(404).json({ error: "Artifact has not been generated locally." });
      return;
    }
    response.sendFile(filename);
  } catch (error) {
    next(error);
  }
});

if (production) {
  const distributionDirectory = path.join(viewerRoot, "dist");
  app.use(express.static(distributionDirectory));
  app.use((_request, response) => response.sendFile(path.join(distributionDirectory, "index.html")));
} else {
  const vite = await createViteServer({
    root: viewerRoot,
    server: { middlewareMode: true },
    appType: "spa",
  });
  app.use(vite.middlewares);
}

app.use((error: unknown, _request: Request, response: Response, _next: NextFunction) => {
  const message = error instanceof Error ? error.message : "Unexpected server error.";
  console.error(error);
  response.status(400).json({ error: message });
});

app.listen(port, "127.0.0.1", () => {
  console.log(`SolidIntent viewer running at http://127.0.0.1:${port}`);
});
