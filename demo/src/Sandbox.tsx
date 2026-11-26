// SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0
// Visitor sandbox: runs the ported session loop in a Web Worker. Its output is
// labelled as sandbox output and never mixed with the published results.
// Nothing is stored or sent anywhere; the optional JSON download is built in
// the browser from the run on screen.
import { useEffect, useRef, useState } from "react";
import { DriftCurves, TasteMapSvg } from "./charts";
import { POLICIES, UPDATE_RULES, type Policy, type UpdateRule } from "./engine";
import type { SandboxResult, SandboxSettings, WorkerReply, WorkerRequest } from "./sandbox.worker";

const DEFAULTS: SandboxSettings = { seed: 1, policy: "SIM", updateRule: "consumed", eta: 0.05, epsilon: 0.2 };
const f3 = (v: number) => v.toFixed(3);

export function Sandbox() {
  const worker = useRef<Worker | null>(null);
  const [settings, setSettings] = useState<SandboxSettings>(DEFAULTS);
  const [running, setRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState<SandboxResult | null>(null);
  const [message, setMessage] = useState<string>("");
  const [shown, setShown] = useState(0);

  useEffect(() => {
    const w = new Worker(new URL("./sandbox.worker.ts", import.meta.url), { type: "module" });
    w.onmessage = (ev: MessageEvent<WorkerReply>) => {
      const m = ev.data;
      if (m.type === "progress") setProgress(m.fraction);
      if (m.type === "done") {
        setResult(m.result);
        const [a, b] = m.result.arms;
        const s = m.result.settings;
        setMessage(
          `Sandbox output (seed ${s.seed}, ${a.policy}, ${s.updateRule} rule, eta ${s.eta}${a.policy === "EXPLORE" ? `, epsilon ${s.epsilon}` : ""}): ` +
            `mean drift ${f3(a.driftRad)} rad` +
            (b ? `; RAND with the same seed ${f3(b.driftRad)} rad; difference ${f3(a.driftRad - b.driftRad)} rad.` : ".") +
            " One sandbox seed, no interval: not a research result.",
        );
      }
      if (m.type === "error") setMessage(`Sandbox run stopped with an error: ${m.message}`);
      if (m.type === "cancelled") setMessage("Sandbox run cancelled.");
      if (m.type !== "progress") setRunning(false);
    };
    worker.current = w;
    return () => w.terminate();
  }, []);

  const set = <K extends keyof SandboxSettings>(k: K, v: SandboxSettings[K]) => setSettings((s) => ({ ...s, [k]: v }));
  const run = () => {
    setRunning(true);
    setProgress(0);
    setMessage("");
    worker.current?.postMessage({ type: "run", settings } satisfies WorkerRequest);
  };
  const cancel = () => worker.current?.postMessage({ type: "cancel" } satisfies WorkerRequest);
  const reset = () => {
    if (running) cancel();
    setSettings(DEFAULTS);
    setResult(null);
    setMessage("");
    setProgress(0);
  };
  const download = () => {
    if (!result) return;
    const blob = new Blob([JSON.stringify({ label: "ECHO sandbox output, not a research result", ...result }, null, 1)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `echo-sandbox-seed${result.settings.seed}-${result.settings.policy}.json`;
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  };

  const p = result?.params;
  return (
    <section id="sandbox" aria-labelledby="h-sandbox" className="sandbox">
      <p className="tag tag-sandbox">Sandbox output</p>
      <h2 id="h-sandbox">Sandbox: run the session loop yourself</h2>
      <p>
        This runs a port of the ECHO session loop in your browser. Given the same random inputs, the port reproduces the
        Python research engine's slates and choices exactly and its preferences and metrics within 1e-9 (a test against a
        fixture from the Python engine). It differs from the research runs in two stated ways: a smaller world (300 tracks,
        40 listeners, 60 steps instead of 1000, 200 and 100) and its own random-number generator, so a sandbox seed does
        not reproduce any research seed. The catalogue uses the frozen FMA-fitted cluster weights and Zipf exponent.
      </p>
      <p className="note">
        Sandbox output is produced in your browser from your settings. It is not a research result, carries no interval
        and is not comparable to the published numbers. Nothing you do here is stored or sent anywhere.
      </p>
      <fieldset className="controls" disabled={running}>
        <legend>Settings</legend>
        <label>
          Seed
          <input type="number" min={1} max={1_000_000} step={1} value={settings.seed}
            onChange={(e) => set("seed", Math.min(1_000_000, Math.max(1, Math.round(Number(e.target.value)) || 1)))} />
        </label>
        <label>
          Policy
          <select value={settings.policy} onChange={(e) => set("policy", e.target.value as Policy)}>
            {POLICIES.map((x) => <option key={x} value={x}>{x}</option>)}
          </select>
        </label>
        <label>
          Update rule
          <select value={settings.updateRule} onChange={(e) => set("updateRule", e.target.value as UpdateRule)}>
            {UPDATE_RULES.map((x) => <option key={x} value={x}>{x}</option>)}
          </select>
        </label>
        <label>
          Update rate (eta)
          <select value={settings.eta} onChange={(e) => set("eta", Number(e.target.value))}>
            {[0.01, 0.05, 0.2].map((x) => <option key={x} value={x}>{x}</option>)}
          </select>
        </label>
        <label>
          Exploration (EXPLORE epsilon): {settings.epsilon.toFixed(2)}
          <input type="range" min={0} max={1} step={0.05} value={settings.epsilon}
            onChange={(e) => set("epsilon", Number(e.target.value))} />
        </label>
      </fieldset>
      <div className="buttons">
        <button type="button" className="primary" onClick={run} disabled={running}>Run</button>
        <button type="button" onClick={cancel} disabled={!running}>Cancel</button>
        <button type="button" onClick={reset}>Reset</button>
        <button type="button" onClick={download} disabled={!result || running}>Download this sandbox output (JSON)</button>
      </div>
      {running && <progress max={1} value={progress} aria-label="Sandbox progress" />}
      <p aria-live="polite" className="sandbox-out">{message}</p>
      {!result && !running && <p className="note">No sandbox run yet. Choose settings and press Run.</p>}
      {result && p && (
        <div className="figure-pair sbx-out">
          <figure>
            <div className="map-wrap">
              <TasteMapSvg tracks={result.tracks}
                paths={result.arms.map((a) => ({ policy: a.policy, points: a.paths[shown] }))}
                label={`Sandbox taste map: ${p.nTracks} tracks in a 2-D projection with the preference path of listener ${result.shownListeners[shown]} under ${result.arms.map((a) => a.policy).join(" and ")}.`} />
            </div>
            <figcaption>
              Sandbox taste map. Grey dots are the sandbox's tracks in the first two principal components of their 16-D
              embeddings. Lines are one listener's preference path; the circle is the start, the square the end.
              <label className="inline">
                Listener{" "}
                <select value={shown} onChange={(e) => setShown(Number(e.target.value))}>
                  {result.shownListeners.map((u, i) => <option key={u} value={i}>{u}</option>)}
                </select>
              </label>
            </figcaption>
          </figure>
          <figure>
            <div className="table-scroll" role="region" aria-label="Sandbox drift curves" tabIndex={0}>
              <DriftCurves series={result.arms.map((a) => ({ policy: a.policy, values: a.meanDriftByStep }))}
                label={`Sandbox: mean drift in radians over ${p.nSteps} steps for ${result.arms.map((a) => a.policy).join(" and ")}.`} />
            </div>
            <figcaption>Sandbox mean drift over the {p.nUsers} sandbox listeners, by step (radians).</figcaption>
          </figure>
          <div className="table-scroll" role="region" aria-label="Sandbox metrics" tabIndex={0}>
            <table>
              <caption>Sandbox metrics (one seed, no interval)</caption>
              <thead>
                <tr><th scope="col">Policy</th><th scope="col">Mean drift (rad)</th><th scope="col">Skip rate</th><th scope="col">Exposure Gini</th><th scope="col">Intra-list diversity</th></tr>
              </thead>
              <tbody>
                {result.arms.map((a) => (
                  <tr key={a.policy}><th scope="row">{a.policy}</th><td>{f3(a.driftRad)}</td><td>{f3(a.skipRate)}</td><td>{f3(a.exposureGini)}</td><td>{f3(a.diversityIld)}</td></tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </section>
  );
}
