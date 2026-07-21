import path from "node:path";
import { fileURLToPath } from "node:url";

import express from "express";
import { createServer as createViteServer } from "vite";

import { errorHandler, registerApiRoutes, type ServerPaths } from "./app.js";

const serverDirectory = path.dirname(fileURLToPath(import.meta.url));
const viewerRoot = path.resolve(serverDirectory, "..");
const repositoryRoot = path.resolve(viewerRoot, "..");
const paths: ServerPaths = {
  repositoryRoot,
  projectsRoot: path.join(repositoryRoot, "projects"),
};
const production = process.argv.includes("--production");
const port = Number(process.env.PORT ?? 4173);

const app = express();
app.disable("x-powered-by");
app.use(express.json({ limit: "32kb" }));
registerApiRoutes(app, paths);

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

app.use(errorHandler);

app.listen(port, "127.0.0.1", () => {
  console.log(`SolidIntent viewer running at http://127.0.0.1:${port}`);
});
