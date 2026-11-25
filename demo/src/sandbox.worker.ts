// SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0
// Bounded, cancellable sandbox: the ported ECHO session loop (engine.ts) at a
// reduced scale, run in a Web Worker. Its output is sandbox output, never a
// research result, and it is never mixed with the published numbers.
import { pca2, project, sandboxRandom, sandboxWorld, session, type Arm, type Params, type Policy, type UpdateRule } from "./engine";

export interface SandboxSettings {
  seed: number;
  policy: Policy;
  updateRule: UpdateRule;
  eta: number;
  epsilon: number;
}

export interface SandboxArmOut {
  policy: Policy;
  meanDriftByStep: number[];
  paths: [number, number][][]; // per shown listener, T + 1 points
  driftRad: number;
  skipRate: number;
  exposureGini: number;
  diversityIld: number;
}

export interface SandboxResult {
  settings: SandboxSettings;
  params: Params;
  tracks: [number, number, number][];
  shownListeners: number[];
  arms: SandboxArmOut[]; // the chosen policy, then RAND with the same seed (unless RAND was chosen)
}

export type WorkerRequest = { type: "run"; settings: SandboxSettings } | { type: "cancel" };
export type WorkerReply =
  | { type: "progress"; fraction: number }
  | { type: "done"; result: SandboxResult }
  | { type: "cancelled" }
  | { type: "error"; message: string };

/** Reduced scale (research runs use N = 1000, U = 200, T = 100). */
export const SANDBOX_PARAMS: Params = {
  nTracks: 300,
  dim: 16,
  nClusters: 16,
  nUsers: 40,
  nSteps: 60,
  slateSize: 10,
  tau: 0.1,
  warmupSteps: 5,
  mmrLambda: 0.5,
  exploreEpsilon: 0.2,
  boundedThreshold: 0.5,
  skipUtility: 0,
};
const SHOWN = [0, 1, 2];
let cancelled = false;

function checkSettings(s: SandboxSettings): void {
  if (!Number.isInteger(s.seed) || s.seed < 1 || s.seed > 1_000_000) throw new Error("seed must be an integer from 1 to 1000000");
  if (![0.01, 0.05, 0.2].includes(s.eta)) throw new Error("eta must be 0.01, 0.05 or 0.2");
  if (!(s.epsilon >= 0 && s.epsilon <= 1)) throw new Error("epsilon must lie in [0, 1]");
}

async function simulate(s: SandboxSettings): Promise<SandboxResult | null> {
  checkSettings(s);
  const p: Params = { ...SANDBOX_PARAMS, exploreEpsilon: s.epsilon };
  const world = sandboxWorld(s.seed, p);
  const d = p.dim;
  const pc = pca2(world.catalogue.emb, p.nTracks, d);
  const tracks: [number, number, number][] = [];
  for (let i = 0; i < p.nTracks; i++) {
    const [x, y] = project(world.catalogue.emb, i * d, d, pc);
    tracks.push([x, y, world.catalogue.cluster[i]]);
  }
  const policies: Policy[] = s.policy === "RAND" ? ["RAND"] : [s.policy, "RAND"];
  const arms: SandboxArmOut[] = [];
  for (const [ai, policy] of policies.entries()) {
    const arm: Arm = { policy, preferenceModel: "adaptive", updateRule: s.updateRule, eta: s.eta, profile: "estimated" };
    const it = session(p, arm, world.catalogue, world.initial, sandboxRandom(s.seed, p), true);
    let r = it.next();
    while (!r.done) {
      if (r.value % 5 === 0) {
        await new Promise((res) => setTimeout(res, 0)); // let a cancel message in
        if (cancelled) return null;
        postMessage({ type: "progress", fraction: (ai + r.value / p.nSteps) / policies.length } satisfies WorkerReply);
      }
      r = it.next();
    }
    const out = r.value;
    const path = out.path!;
    const meanDriftByStep = path.map((P) => {
      let sum = 0;
      for (let u = 0; u < p.nUsers; u++) {
        let c = 0;
        let na = 0;
        let nb = 0;
        for (let j = 0; j < d; j++) {
          c += world.initial[u * d + j] * P[u * d + j];
          na += world.initial[u * d + j] ** 2;
          nb += P[u * d + j] ** 2;
        }
        sum += Math.acos(Math.max(-1, Math.min(1, c / Math.sqrt(na * nb))));
      }
      return sum / p.nUsers;
    });
    arms.push({
      policy,
      meanDriftByStep,
      paths: SHOWN.map((u) => path.map((P) => project(P, u * d, d, pc))),
      driftRad: out.metrics.drift_rad,
      skipRate: out.metrics.skip_rate,
      exposureGini: out.metrics.exposure_gini,
      diversityIld: out.metrics.diversity_ild,
    });
  }
  return { settings: s, params: p, tracks, shownListeners: SHOWN, arms };
}

onmessage = async (ev: MessageEvent<WorkerRequest>) => {
  const m = ev.data;
  if (m.type === "cancel") {
    cancelled = true;
    return;
  }
  cancelled = false;
  try {
    const result = await simulate(m.settings);
    postMessage((result === null ? { type: "cancelled" } : { type: "done", result }) satisfies WorkerReply);
  } catch (e) {
    postMessage({ type: "error", message: e instanceof Error ? e.message : String(e) } satisfies WorkerReply);
  }
};
