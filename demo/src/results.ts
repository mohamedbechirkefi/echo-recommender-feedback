// SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0
// Published results: loaded from public/data/results.json, which
// scripts/export_demo_data.py writes from committed results only.
// Validation fails closed: any missing or malformed field means no numbers are shown.

export const SCHEMA = "lab-demo-results";
export const SCHEMA_MAJOR = 1;

export interface Estimate {
  label: string;
  estimate: number;
  ci_low: number | null;
  ci_high: number | null;
  ci_level: number | null;
  unit: string;
  /** Exact text the manuscript prints for the estimate and interval; shown verbatim when present. */
  display: string | null;
  interval_display: string | null;
  /** ECHO extension: where the exact text is printed ("manuscript" or "supplementary"). */
  display_source: "manuscript" | "supplementary";
  /** ECHO extension: primary, secondary, sensitivity, descriptive or exploratory. */
  kind: string;
}

export interface Experiment {
  id: string;
  title: string;
  status: string;
  verdict: string;
  estimates: Estimate[];
  claim_ids: string[];
  report_path: string;
  notes: string[];
}

export interface Assumption {
  name: string;
  value: string;
  source: string;
}

export interface Source {
  path: string;
  sha256: string;
}

export interface Results {
  schema: string;
  schema_version: string;
  project: string;
  question: string;
  status_label: string;
  code_revision: string;
  sources: Source[];
  experiments: Experiment[];
  assumptions: Assumption[];
  limitations: string[];
  // ECHO extensions (validated by validateExtensions, failing closed).
  method: string[];
  sesoi_rad: number;
  contrast_chart: ChartRow[];
  arm_drift: Record<"EXP-002" | "EXP-004", ArmRow[]>;
  taste_map: TasteMap;
  owner_pending: string[];
}

export interface ChartRow extends Estimate {
  experiment: string;
  cell: string;
  decision: string;
  triggers_withdrawal: boolean;
}

export interface ArmRow extends Estimate {
  policy: string;
}

export interface TasteListener {
  listener: number;
  path: [number, number][];
  drift_by_step: number[];
}

export interface TastePolicy {
  mean_drift_by_step: number[];
  listeners: TasteListener[];
}

export interface TasteMap {
  label: string;
  source: string;
  generator: string;
  seed: number;
  setting: string;
  config: Record<string, unknown>;
  projection: { method: string; explained_variance_share: number[] };
  tracks: [number, number, number][];
  listeners: number[];
  policies: Record<string, TastePolicy>;
}

export const TASTE_POLICIES = ["RAND", "POP", "SIM", "MMR", "EXPLORE"] as const;

export class ResultsError extends Error {}

type Obj = Record<string, unknown>;

function obj(v: unknown, where: string): Obj {
  if (typeof v !== "object" || v === null || Array.isArray(v)) {
    throw new ResultsError(`${where}: expected an object`);
  }
  return v as Obj;
}

function str(o: Obj, k: string, where: string): string {
  const v = o[k];
  if (typeof v !== "string" || v.length === 0) {
    throw new ResultsError(`${where}.${k}: expected a non-empty string`);
  }
  return v;
}

function num(o: Obj, k: string, where: string, nullable = false): number | null {
  const v = o[k];
  if (nullable && v === null) return null;
  if (typeof v !== "number" || !Number.isFinite(v)) {
    throw new ResultsError(`${where}.${k}: expected a finite number`);
  }
  return v;
}

function arr(o: Obj, k: string, where: string): unknown[] {
  const v = o[k];
  if (!Array.isArray(v)) throw new ResultsError(`${where}.${k}: expected an array`);
  return v;
}

function strArr(o: Obj, k: string, where: string): string[] {
  return arr(o, k, where).map((v, i) => {
    if (typeof v !== "string") throw new ResultsError(`${where}.${k}[${i}]: expected a string`);
    return v;
  });
}

function estimate(v: unknown, where: string): Estimate {
  const o = obj(v, where);
  const e: Estimate = {
    label: str(o, "label", where),
    estimate: num(o, "estimate", where) as number,
    ci_low: num(o, "ci_low", where, true),
    ci_high: num(o, "ci_high", where, true),
    ci_level: num(o, "ci_level", where, true),
    unit: typeof o.unit === "string" ? o.unit : "",
    display: typeof o.display === "string" ? o.display : null,
    interval_display: typeof o.interval_display === "string" ? o.interval_display : null,
    display_source: o.display_source === "supplementary" ? "supplementary" : "manuscript",
    kind: typeof o.kind === "string" ? o.kind : "",
  };
  if (o.display_source !== "manuscript" && o.display_source !== "supplementary") {
    throw new ResultsError(`${where}.display_source: expected "manuscript" or "supplementary"`);
  }
  // ECHO: every published number is shown exactly as printed, so the exact text is required.
  if (e.display === null) throw new ResultsError(`${where}.display: expected the manuscript text`);
  if ((e.ci_low === null) !== (e.interval_display === null)) {
    throw new ResultsError(`${where}: interval text must accompany an interval`);
  }
  if (e.ci_low !== null && !(e.ci_low <= e.estimate && e.estimate <= e.ci_high!)) {
    throw new ResultsError(`${where}: estimate outside its interval`);
  }
  if ((e.ci_low === null) !== (e.ci_high === null)) {
    throw new ResultsError(`${where}: interval must have both bounds or neither`);
  }
  if (e.ci_low !== null && e.ci_high !== null && e.ci_low > e.ci_high) {
    throw new ResultsError(`${where}: ci_low exceeds ci_high`);
  }
  return e;
}

export function validateResults(raw: unknown): Results {
  const o = obj(raw, "results");
  if (o.schema !== SCHEMA) throw new ResultsError(`results.schema: expected "${SCHEMA}"`);
  const version = str(o, "schema_version", "results");
  if (Number(version.split(".")[0]) !== SCHEMA_MAJOR) {
    throw new ResultsError(`results.schema_version: unsupported major version ${version}`);
  }
  const experiments = arr(o, "experiments", "results").map((v, i) => {
    const w = `experiments[${i}]`;
    const e = obj(v, w);
    return {
      id: str(e, "id", w),
      title: str(e, "title", w),
      status: str(e, "status", w),
      verdict: str(e, "verdict", w),
      estimates: arr(e, "estimates", w).map((x, j) => estimate(x, `${w}.estimates[${j}]`)),
      claim_ids: strArr(e, "claim_ids", w),
      report_path: str(e, "report_path", w),
      notes: strArr(e, "notes", w),
    };
  });
  if (experiments.length === 0) throw new ResultsError("results.experiments: empty");
  return {
    schema: SCHEMA,
    schema_version: version,
    project: str(o, "project", "results"),
    question: str(o, "question", "results"),
    status_label: str(o, "status_label", "results"),
    code_revision: str(o, "code_revision", "results"),
    sources: arr(o, "sources", "results").map((v, i) => {
      const s = obj(v, `sources[${i}]`);
      const sha = str(s, "sha256", `sources[${i}]`);
      if (!/^[0-9a-f]{64}$/.test(sha)) throw new ResultsError(`sources[${i}].sha256: not a sha256`);
      return { path: str(s, "path", `sources[${i}]`), sha256: sha };
    }),
    experiments,
    assumptions: arr(o, "assumptions", "results").map((v, i) => {
      const a = obj(v, `assumptions[${i}]`);
      return {
        name: str(a, "name", `assumptions[${i}]`),
        value: str(a, "value", `assumptions[${i}]`),
        source: str(a, "source", `assumptions[${i}]`),
      };
    }),
    limitations: strArr(o, "limitations", "results"),
    ...validateExtensions(o),
  };
}

function finiteArr(v: unknown, where: string, len?: number): number[] {
  if (!Array.isArray(v) || (len !== undefined && v.length !== len)) {
    throw new ResultsError(`${where}: expected an array${len !== undefined ? ` of length ${len}` : ""}`);
  }
  return v.map((x, i) => {
    if (typeof x !== "number" || !Number.isFinite(x)) throw new ResultsError(`${where}[${i}]: expected a finite number`);
    return x;
  });
}

function bool(o: Obj, k: string, where: string): boolean {
  if (typeof o[k] !== "boolean") throw new ResultsError(`${where}.${k}: expected a boolean`);
  return o[k] as boolean;
}

/** Validates the ECHO-specific top-level keys. Any problem rejects the whole file. */
export function validateExtensions(o: Obj) {
  const method = strArr(o, "method", "results");
  if (method.length === 0) throw new ResultsError("results.method: empty");
  const sesoi = num(o, "sesoi_rad", "results") as number;
  if (!(sesoi > 0)) throw new ResultsError("results.sesoi_rad: expected a positive number");

  const chart = arr(o, "contrast_chart", "results").map((v, i) => {
    const w = `contrast_chart[${i}]`;
    const r = obj(v, w);
    const e = estimate(r, w);
    if (e.ci_low === null) throw new ResultsError(`${w}: a chart row needs an interval`);
    return { ...e, experiment: str(r, "experiment", w), cell: str(r, "cell", w), decision: str(r, "decision", w),
             triggers_withdrawal: bool(r, "triggers_withdrawal", w) };
  });
  if (chart.length !== 20) throw new ResultsError("results.contrast_chart: expected 20 rows (EXP-002, 18 EXP-003 cells, EXP-004)");

  const armsObj = obj(o.arm_drift, "results.arm_drift");
  const arm_drift = {} as Record<"EXP-002" | "EXP-004", ArmRow[]>;
  for (const exp of ["EXP-002", "EXP-004"] as const) {
    const rows = arr(armsObj, exp, "arm_drift").map((v, i) => {
      const w = `arm_drift.${exp}[${i}]`;
      const r = obj(v, w);
      const e = estimate(r, w);
      if (e.ci_low === null) throw new ResultsError(`${w}: an arm row needs an interval`);
      return { ...e, policy: str(r, "policy", w) };
    });
    if (rows.map((r) => r.policy).join() !== TASTE_POLICIES.join()) throw new ResultsError(`arm_drift.${exp}: expected the five policies in order`);
    arm_drift[exp] = rows;
  }

  const t = obj(o.taste_map, "results.taste_map");
  const tw = "taste_map";
  const tracks = arr(t, "tracks", tw).map((v, i) => {
    const xs = finiteArr(v, `${tw}.tracks[${i}]`, 3);
    if (!Number.isInteger(xs[2]) || xs[2] < 0) throw new ResultsError(`${tw}.tracks[${i}]: bad cluster`);
    return xs as [number, number, number];
  });
  if (tracks.length < 10) throw new ResultsError(`${tw}.tracks: too few tracks`);
  const listeners = finiteArr(t.listeners, `${tw}.listeners`);
  const pol = obj(t.policies, `${tw}.policies`);
  const policies: Record<string, TastePolicy> = {};
  let steps = -1;
  for (const p of TASTE_POLICIES) {
    const pw = `${tw}.policies.${p}`;
    const po = obj(pol[p], pw);
    const mean = finiteArr(po.mean_drift_by_step, `${pw}.mean_drift_by_step`);
    if (steps < 0) steps = mean.length;
    if (mean.length !== steps || steps < 2) throw new ResultsError(`${pw}: inconsistent step count`);
    const ls = arr(po, "listeners", pw).map((v, i) => {
      const lw = `${pw}.listeners[${i}]`;
      const lo = obj(v, lw);
      const path = arr(lo, "path", lw).map((q, j) => finiteArr(q, `${lw}.path[${j}]`, 2) as [number, number]);
      const drift = finiteArr(lo.drift_by_step, `${lw}.drift_by_step`, steps);
      if (path.length !== steps) throw new ResultsError(`${lw}.path: expected ${steps} points`);
      return { listener: num(lo, "listener", lw) as number, path, drift_by_step: drift };
    });
    if (ls.length !== listeners.length) throw new ResultsError(`${pw}.listeners: count mismatch`);
    policies[p] = { mean_drift_by_step: mean, listeners: ls };
  }
  const proj = obj(t.projection, `${tw}.projection`);
  const taste_map: TasteMap = {
    label: str(t, "label", tw),
    source: str(t, "source", tw),
    generator: str(t, "generator", tw),
    seed: num(t, "seed", tw) as number,
    setting: str(t, "setting", tw),
    config: obj(t.config, `${tw}.config`),
    projection: { method: str(proj, "method", `${tw}.projection`),
                  explained_variance_share: finiteArr(proj.explained_variance_share, `${tw}.projection.explained_variance_share`, 2) },
    tracks,
    listeners,
    policies,
  };
  if (!/exploratory/i.test(taste_map.label)) throw new ResultsError(`${tw}.label: must say it is exploratory`);
  return { method, sesoi_rad: sesoi, contrast_chart: chart, arm_drift, taste_map, owner_pending: strArr(o, "owner_pending", "results") };
}

export async function loadResults(url = "./data/results.json"): Promise<Results> {
  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) throw new ResultsError(`could not load ${url} (HTTP ${res.status})`);
  let raw: unknown;
  try {
    raw = await res.json();
  } catch {
    throw new ResultsError(`${url} is not valid JSON`);
  }
  return validateResults(raw);
}

/** Formats a number for display without inventing precision. */
export function fmt(x: number, digits = 3): string {
  if (Number.isInteger(x)) return x.toString();
  return Number(x.toPrecision(digits)).toString();
}

export function fmtEstimate(e: Estimate, digits = 3): string {
  return e.display ?? `${fmt(e.estimate, digits)}${e.unit ? " " + e.unit : ""}`;
}

export function fmtInterval(e: Estimate, digits = 3): string {
  if (e.interval_display !== null) return e.interval_display;
  if (e.ci_low === null || e.ci_high === null) return "no interval";
  const level = e.ci_level === null ? "" : `${Math.round(e.ci_level * 100)}% `;
  return `${level}[${fmt(e.ci_low, digits)}, ${fmt(e.ci_high, digits)}]`;
}
