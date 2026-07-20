import { Suspense, useEffect, useMemo, useRef, useState } from "react";
import { Canvas, useLoader, useThree } from "@react-three/fiber";
import {
  Bounds,
  ContactShadows,
  Edges,
  GizmoHelper,
  GizmoViewport,
  Html,
  OrbitControls,
} from "@react-three/drei";
import { Box, Focus, Layers3, ScanLine } from "lucide-react";
import type { OrbitControls as OrbitControlsImpl } from "three-stdlib";
import { STLLoader } from "three/examples/jsm/loaders/STLLoader.js";

import type { ProjectData } from "../types";
import type { BodyVisibility } from "./ContextRail";

interface ModelViewerProps {
  project: ProjectData;
  bodyVisibility: BodyVisibility;
}

interface ModelBodyProps {
  url: string;
  color: string;
  positionY: number;
  opacity: number;
}

function ModelBody({ url, color, positionY, opacity }: ModelBodyProps) {
  const sourceGeometry = useLoader(STLLoader, url);
  const geometry = useMemo(() => {
    const copy = sourceGeometry.clone();
    copy.computeVertexNormals();
    copy.center();
    return copy;
  }, [sourceGeometry]);

  return (
    <mesh geometry={geometry} rotation={[-Math.PI / 2, 0, 0]} position={[0, positionY, 0]} castShadow receiveShadow>
      <meshStandardMaterial
        color={color}
        roughness={0.64}
        metalness={0.08}
        transparent={opacity < 1}
        opacity={opacity}
      />
      <Edges threshold={24} color="#adb8b3" />
    </mesh>
  );
}

function CanvasLoading() {
  return (
    <Html center>
      <div className="canvas-loading" role="status">
        <span />
        Loading generated geometry
      </div>
    </Html>
  );
}

function CameraRig({ fitNonce }: { fitNonce: number }) {
  const { camera } = useThree();
  const controls = useRef<OrbitControlsImpl>(null);

  useEffect(() => {
    camera.position.set(126, 94, 126);
    camera.zoom = 1;
    camera.updateProjectionMatrix();
    controls.current?.target.set(0, 7, 0);
    controls.current?.update();
  }, [camera, fitNonce]);

  return (
    <OrbitControls
      ref={controls}
      makeDefault
      enableDamping
      dampingFactor={0.08}
      minDistance={70}
      maxDistance={280}
      target={[0, 7, 0]}
    />
  );
}

export function ModelViewer({ project, bodyVisibility }: ModelViewerProps) {
  const [exploded, setExploded] = useState(true);
  const [transparent, setTransparent] = useState(false);
  const [fitNonce, setFitNonce] = useState(0);
  const baseAvailable = project.artifactAvailability.base_stl;
  const lidAvailable = project.artifactAvailability.lid_stl;
  const available = baseAvailable || lidAvailable;

  return (
    <section className="model-stage" aria-label="Generated model viewer">
      <div className="stage-meta">
        <span>Base + Lid</span>
        <span aria-hidden="true">·</span>
        <span>2 validated solids</span>
        <span aria-hidden="true">·</span>
        <span className="stage-meta-mono">mm</span>
      </div>

      {available ? (
        <Canvas
          className="model-canvas"
          camera={{ position: [126, 94, 126], fov: 34, near: 0.1, far: 1000 }}
          dpr={[1, 1.75]}
          shadows
          gl={{ antialias: true, alpha: false }}
          fallback={<div className="canvas-error">WebGL is not available in this browser.</div>}
        >
          <color attach="background" args={["#171a19"]} />
          <ambientLight intensity={1.4} />
          <directionalLight position={[80, 130, 70]} intensity={2.6} castShadow />
          <directionalLight position={[-90, 45, -70]} intensity={0.9} />
          <Suspense fallback={<CanvasLoading />}>
            <Bounds fit clip observe margin={1.22}>
              {baseAvailable && bodyVisibility.base ? (
                <ModelBody
                  url={`/api/projects/${project.manifest.project_id}/artifacts/base_stl`}
                  color="#3d4541"
                  positionY={-5}
                  opacity={transparent ? 0.46 : 1}
                />
              ) : null}
              {lidAvailable && bodyVisibility.lid ? (
                <ModelBody
                  url={`/api/projects/${project.manifest.project_id}/artifacts/lid_stl`}
                  color="#555e5a"
                  positionY={exploded ? 42 : 15}
                  opacity={transparent ? 0.38 : 1}
                />
              ) : null}
            </Bounds>
            <ContactShadows position={[0, -18, 0]} opacity={0.45} scale={170} blur={2.2} far={80} />
          </Suspense>
          <CameraRig fitNonce={fitNonce} />
          <GizmoHelper alignment="bottom-left" margin={[82, 82]}>
            <GizmoViewport axisColors={["#ff645f", "#58c98e", "#2f77ff"]} labelColor="#f1f5f3" />
          </GizmoHelper>
        </Canvas>
      ) : (
        <div className="canvas-empty">
          <Box aria-hidden="true" />
          <h2>No local mesh artifacts</h2>
          <p>Generate the project STL files through build123d-mcp to enable the interactive view.</p>
        </div>
      )}

      {available && !bodyVisibility.base && !bodyVisibility.lid ? (
        <div className="bodies-hidden-state" role="status">
          Both generated bodies are hidden. Use the Bodies list to show one.
        </div>
      ) : null}

      <div className="canvas-controls" aria-label="Model view controls">
        <button type="button" onClick={() => setFitNonce((value) => value + 1)}>
          <Focus aria-hidden="true" />
          Fit view
        </button>
        <button
          className={exploded ? "is-active" : ""}
          type="button"
          aria-pressed={exploded}
          onClick={() => setExploded((value) => !value)}
        >
          <Layers3 aria-hidden="true" />
          Exploded
        </button>
        <button
          className={transparent ? "is-active" : ""}
          type="button"
          aria-pressed={transparent}
          onClick={() => setTransparent((value) => !value)}
        >
          <ScanLine aria-hidden="true" />
          Transparency
        </button>
      </div>
    </section>
  );
}
