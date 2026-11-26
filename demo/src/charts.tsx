// SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0
// Hand-written SVG charts. Colours come from CSS classes (style.css), so both
// colour schemes stay legible. Every chart has a text description next to it.
import { useRef } from "react";
import type { ArmRow, ChartRow } from "./results";
import { useInView } from "./Record";

const nice = (lo: number, hi: number, n = 6): number[] => {
  const step0 = (hi - lo) / n;
  const mag = 10 ** Math.floor(Math.log10(step0));
  const step = [1, 2, 2.5, 5, 10].map((m) => m * mag).find((s) => s >= step0) ?? step0;
  const out: number[] = [];
  for (let v = Math.ceil(lo / step) * step; v <= hi + 1e-12; v += step) out.push(Math.round(v / step) * step);
  return out;
};
const tickText = (v: number) => (Math.abs(v) < 1e-12 ? "0" : Number(v.toPrecision(3)).toString());

function groupOf(r: ChartRow): string {
  if (r.experiment === "EXP-002") return "EXP-002, synthetic catalogue (primary)";
  if (r.experiment === "EXP-004") return "EXP-004, real FMA catalogue (second test)";
  return r.cell.endsWith("/oracle") ? "EXP-003, oracle profile" : "EXP-003, estimated profile";
}

function rowLabel(r: ChartRow): string {
  if (r.experiment !== "EXP-003") return "SIM minus RAND";
  const [rule, eta] = r.cell.split("/");
  return `${rule} / ${eta.replace("eta=", "eta ")}`;
}

/** Forest plot of every SIM minus RAND drift contrast, with the SESOI band. */
export function ContrastForest({ rows, sesoi }: { rows: ChartRow[]; sesoi: number }) {
  const W = 860, left = 190, plotW = 360, right = left + plotW + 16, rowH = 30, top = 34;
  const lo = Math.min(...rows.map((r) => r.ci_low!), -sesoi) - 0.02;
  const hi = Math.max(...rows.map((r) => r.ci_high!), sesoi) + 0.02;
  const x = (v: number) => left + ((v - lo) / (hi - lo)) * plotW;
  const items: ({ kind: "head"; text: string } | { kind: "row"; r: ChartRow })[] = [];
  let g = "";
  for (const r of rows) {
    if (groupOf(r) !== g) {
      g = groupOf(r);
      items.push({ kind: "head", text: g });
    }
    items.push({ kind: "row", r });
  }
  const H = top + items.length * rowH + 40;
  const ticks = nice(lo, hi);
  return (
    <svg className="chart forest" viewBox={`0 0 ${W} ${H}`} width={W} height={H} role="img"
      aria-label="Forest plot of the SIM minus RAND drift contrast in radians with 95 % bootstrap intervals for EXP-002, the 18 EXP-003 cells and EXP-004. The shaded band is the smallest effect size of interest.">
      <rect className="band" x={x(-sesoi)} y={top - 8} width={x(sesoi) - x(-sesoi)} height={items.length * rowH + 8} />
      <line className="zero" x1={x(0)} x2={x(0)} y1={top - 8} y2={top + items.length * rowH} />
      <text className="axis-title" x={left} y={16}>SIM minus RAND, mean drift difference (rad)</text>
      <text className="axis-title" x={right} y={16}>Mean diff [95 % CI], decision</text>
      {items.map((it, i) => {
        const y = top + i * rowH + rowH / 2;
        if (it.kind === "head") return <text key={i} className="group" x={8} y={y + 4}>{it.text}</text>;
        const r = it.r;
        const trig = r.triggers_withdrawal;
        return (
          <g key={i} className={trig ? "row trigger" : "row"}>
            <text className="label" x={24} y={y + 4}>{rowLabel(r)}</text>
            <line className="ci" x1={x(r.ci_low!)} x2={x(r.ci_high!)} y1={y} y2={y} />
            <line className="ci" x1={x(r.ci_low!)} x2={x(r.ci_low!)} y1={y - 5} y2={y + 5} />
            <line className="ci" x1={x(r.ci_high!)} x2={x(r.ci_high!)} y1={y - 5} y2={y + 5} />
            {trig ? (
              <path className="point" d={`M ${x(r.estimate)} ${y - 6} l 6 6 l -6 6 l -6 -6 z`} />
            ) : (
              <circle className="point" cx={x(r.estimate)} cy={y} r={4.5} />
            )}
            <text className="value" x={right} y={y - 1}>{r.display} {r.interval_display}</text>
            <text className="decision" x={right} y={y + 12}>{r.decision}{trig ? "; triggers withdrawal" : ""}</text>
          </g>
        );
      })}
      {ticks.map((t) => (
        <g key={t}>
          <line className="tick" x1={x(t)} x2={x(t)} y1={top + items.length * rowH} y2={top + items.length * rowH + 5} />
          <text className="tick-label" x={x(t)} y={top + items.length * rowH + 20} textAnchor="middle">{tickText(t)}</text>
        </g>
      ))}
    </svg>
  );
}

/** Per-policy mean drift with 95 % CIs for one experiment. */
export function ArmDrift({ rows, title }: { rows: ArmRow[]; title: string }) {
  const W = 420, left = 80, plotW = 300, rowH = 30, top = 30;
  const lo = Math.min(...rows.map((r) => r.ci_low!));
  const hi = Math.max(...rows.map((r) => r.ci_high!));
  const pad = (hi - lo) * 0.08;
  const a = lo - pad, b = hi + pad;
  const x = (v: number) => left + ((v - a) / (b - a)) * plotW;
  const H = top + rows.length * rowH + 34;
  return (
    <svg className="chart arms" viewBox={`0 0 ${W} ${H}`} role="img"
      aria-label={`${title}: mean angular drift in radians per policy, adaptive preferences, with 95 % bootstrap intervals over 10 seeds.`}>
      <text className="axis-title" x={8} y={16}>{title}</text>
      {rows.map((r, i) => {
        const y = top + i * rowH + rowH / 2;
        return (
          <g key={r.policy}>
            <text className="label" x={8} y={y + 4}>{r.policy}</text>
            <line className={`ci pol-${r.policy}`} x1={x(r.ci_low!)} x2={x(r.ci_high!)} y1={y} y2={y} />
            <circle className={`point pol-${r.policy}`} cx={x(r.estimate)} cy={y} r={4.5} />
          </g>
        );
      })}
      {nice(a, b, 4).map((t) => (
        <g key={t}>
          <line className="tick" x1={x(t)} x2={x(t)} y1={top + rows.length * rowH} y2={top + rows.length * rowH + 5} />
          <text className="tick-label" x={x(t)} y={top + rows.length * rowH + 20} textAnchor="middle">{tickText(t)}</text>
        </g>
      ))}
    </svg>
  );
}

export interface MapPath {
  policy: string;
  points: [number, number][];
}

/** Taste map: catalogue tracks in a 2-D projection, with preference trajectories. */
export function TasteMapSvg({ tracks, paths, label }: { tracks: [number, number, number][]; paths: MapPath[]; label: string }) {
  const S = 420, m = 14;
  const xs = [...tracks.map((t) => t[0]), ...paths.flatMap((p) => p.points.map((q) => q[0]))];
  const ys = [...tracks.map((t) => t[1]), ...paths.flatMap((p) => p.points.map((q) => q[1]))];
  const x0 = Math.min(...xs), x1 = Math.max(...xs), y0 = Math.min(...ys), y1 = Math.max(...ys);
  const span = Math.max(x1 - x0, y1 - y0) || 1;
  const sx = (v: number) => m + ((v - x0) / span) * (S - 2 * m);
  const sy = (v: number) => S - m - ((v - y0) / span) * (S - 2 * m);
  return (
    <svg className="chart map" viewBox={`0 0 ${S} ${S}`} role="img" aria-label={label}>
      <rect className="map-bg" x={0} y={0} width={S} height={S} />
      {tracks.map((t, i) => (
        <circle key={i} className="track" cx={sx(t[0])} cy={sy(t[1])} r={1.8} />
      ))}
      {paths.map((p, i) => {
        const pts = p.points.map((q) => `${sx(q[0]).toFixed(1)},${sy(q[1]).toFixed(1)}`).join(" ");
        const [sx0, sy0] = [sx(p.points[0][0]), sy(p.points[0][1])];
        const end = p.points[p.points.length - 1];
        return (
          <g key={i} className={`traj pol-${p.policy}`}>
            <polyline points={pts} />
            <circle className="start" cx={sx0} cy={sy0} r={5} />
            <rect className="end" x={sx(end[0]) - 4.5} y={sy(end[1]) - 4.5} width={9} height={9} />
          </g>
        );
      })}
    </svg>
  );
}

/** Mean drift by session step, one line per policy. */
export function DriftCurves({ series, label, yMax }: { series: { policy: string; values: number[] }[]; label: string; yMax?: number }) {
  const W = 520, H = 270, left = 52, right = 92, top = 16, bottom = 40;
  const n = Math.max(...series.map((s) => s.values.length));
  const ymax = yMax ?? Math.max(...series.flatMap((s) => s.values)) * 1.05;
  const x = (i: number) => left + (i / (n - 1)) * (W - left - right);
  const y = (v: number) => top + (1 - v / ymax) * (H - top - bottom);
  const ends = series.map((s) => ({ s, yy: y(s.values[s.values.length - 1]) })).sort((a, b) => a.yy - b.yy);
  for (let i = 1; i < ends.length; i++) ends[i].yy = Math.max(ends[i].yy, ends[i - 1].yy + 14);
  const ref = useRef<SVGSVGElement>(null);
  const seen = useInView(ref);
  return (
    <svg ref={ref} className={`chart curves${seen ? "" : " pending"}`} viewBox={`0 0 ${W} ${H}`} role="img" aria-label={label}>
      {nice(0, ymax, 4).map((t) => (
        <g key={t}>
          <line className="grid" x1={left} x2={W - right} y1={y(t)} y2={y(t)} />
          <text className="tick-label" x={left - 6} y={y(t) + 4} textAnchor="end">{tickText(t)}</text>
        </g>
      ))}
      {nice(0, n - 1, 4).map((t) => (
        <text key={t} className="tick-label" x={x(t)} y={H - bottom + 18} textAnchor="middle">{tickText(t)}</text>
      ))}
      <text className="axis-title" x={(left + W - right) / 2} y={H - 4} textAnchor="middle">session step</text>
      <text className="axis-title" x={12} y={top + 4} transform={`rotate(-90 12 ${top + 4})`} textAnchor="end">mean drift (rad)</text>
      <g className="lines">
      {series.map((s) => (
        <polyline key={s.policy} className={`line pol-${s.policy}`} points={s.values.map((v, i) => `${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(" ")} />
      ))}
      </g>
      {ends.map(({ s, yy }) => (
        <text key={s.policy} className={`end-label pol-${s.policy}`} x={W - right + 6} y={yy + 4}>{s.policy}</text>
      ))}
    </svg>
  );
}
