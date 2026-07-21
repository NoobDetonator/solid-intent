import { Suspense, useEffect, useMemo, useRef, useState } from "react";
import { Canvas, useLoader, useThree } from "@react-three/fiber";
import { ContactShadows, Edges, GizmoHelper, GizmoViewport, Html, OrbitControls } from "@react-three/drei";
import { Box, Focus, Layers3, ScanLine } from "lucide-react";
import { Vector3, type BufferGeometry } from "three";
import type { OrbitControls as OrbitControlsImpl } from "three-stdlib";
import { STLLoader } from "three/examples/jsm/loaders/STLLoader.js";

import type { ProjectData } from "../types";
import { bodyColor, bodyLabel, renderableBodies, validatedSolidCount } from "../bodies";
import type { BodyVisibility } from "./ContextRail";

interface ModelViewerProps {
  project: ProjectData;
  bodyVisibility: BodyVisibility;
}

const EXPLODED_GAP_MM = 20;

interface PlacedBody {
  name: string;
  geometry: BufferGeometry;
  positionY: number;
}

interface BodiesGroupProps {
  urls: string[];
  names: string[];
  bodyVisibility: BodyVisibility;
  exploded: boolean;
  transparent: boolean;
}

function BodiesGroup({ urls, names, bodyVisibility, exploded, transparent }: BodiesGroupProps) {
  const geometries = useLoader(STLLoader, urls);

  const placed = useMemo<PlacedBody[]>(() => {
    const measured = names.map((name, index) => {
      const geometry = geometries[index].clone();
      geometry.computeVertexNormals();
      geometry.center();
      geometry.computeBoundingBox();
      const size = new Vector3();
      geometry.boundingBox?.getSize(size);
      // The model is rotated -90° about X, so the model Z extent is the world
      // vertical height of the body.
      return { name, geometry, height: size.z };
    });

    const totalHeight =
      measured.reduce((sum, item) => sum + item.height, 0) +
      (exploded ? EXPLODED_GAP_MM * Math.max(0, measured.length - 1) : 0);

    let bottom = 0;
    return measured.map((item, index) => {
      const gap = exploded ? EXPLODED_GAP_MM * index : 0;
      const centerY = bottom + gap + item.height / 2;
      bottom += item.height;
      return { name: item.name, geometry: item.geometry, positionY: centerY - totalHeight / 2 };
    });
  }, [geometries, names, exploded]);

  return (
    <>
      {placed.map((body, index) => (
        <mesh
          key={body.name}
          geometry={body.geometry}
          rotation={[-Math.PI / 2, 0, 0]}
          position={[0, body.positionY, 0]}
          visible={bodyVisibility[body.name] !== false}
          castShadow
          receiveShadow
        >
          <meshStandardMaterial
            color={bodyColor(index)}
            roughness={0.64}
            metalness={0.08}
            transparent={transparent}
            opacity={transparent ? 0.42 : 1}
          />
          <Edges threshold={24} color="#adb8b3" />
        </mesh>
      ))}
      <ContactShadows position={[0, -26, 0]} opacity={0.45} scale={190} blur={2.2} far={90} />
    </>
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
    controls.current?.target.set(0, 0, 0);
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
      target={[0, 0, 0]}
    />
  );
}

export function ModelViewer({ project, bodyVisibility }: ModelViewerProps) {
  const [exploded, setExploded] = useState(true);
  const [transparent, setTransparent] = useState(false);
  const [fitNonce, setFitNonce] = useState(0);

  const bodyNames = useMemo(() => renderableBodies(project), [project]);
  const urls = useMemo(
    () =>
      bodyNames.map(
        (name) => `/api/projects/${project.manifest.project_id}/artifacts/${name}_stl`,
      ),
    [bodyNames, project.manifest.project_id],
  );
  const available = bodyNames.length > 0;
  const allHidden = available && bodyNames.every((name) => bodyVisibility[name] === false);

  const solidCount = validatedSolidCount(project);
  const bodyLabels = bodyNames.map(bodyLabel).join(" + ") || "No local bodies";

  return (
    <section className="model-stage" aria-label="Generated model viewer">
      <div className="stage-meta">
        <span>{bodyLabels}</span>
        <span aria-hidden="true">·</span>
        <span>
          {solidCount} validated {solidCount === 1 ? "solid" : "solids"}
        </span>
        <span aria-hidden="true">·</span>
        <span className="stage-meta-mono">{project.manifest.units}</span>
      </div>

      {available ? (
        <Canvas
          key={project.manifest.project_id}
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
            <BodiesGroup
              urls={urls}
              names={bodyNames}
              bodyVisibility={bodyVisibility}
              exploded={exploded}
              transparent={transparent}
            />
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

      {allHidden ? (
        <div className="bodies-hidden-state" role="status">
          All generated bodies are hidden. Use the Bodies list to show one.
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
