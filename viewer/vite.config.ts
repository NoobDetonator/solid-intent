import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: "dist",
    sourcemap: true,
    // The 3D viewer (three.js + react-three) is already isolated in its own
    // lazily-loaded chunk, so a larger size here is expected and acceptable.
    chunkSizeWarningLimit: 1100,
  },
});
