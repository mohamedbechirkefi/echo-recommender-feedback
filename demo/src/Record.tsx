// SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0
// The record pictures. HeroRecord is an illustration and shows no number.
// NeedleDial draws published per-policy mean drift (radians) as literal angles
// on a quarter record: the needle angle is the drift.
import { useEffect, useRef, useState, type RefObject } from "react";
import type { ArmRow } from "./results";

export const reducedMotion = () =>
  typeof window !== "undefined" && typeof window.matchMedia === "function" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

/** True once the element has entered the viewport (never resets). */
export function useInView<T extends Element>(ref: RefObject<T | null>): boolean {
  const [seen, setSeen] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el || seen) return;
    if (typeof IntersectionObserver === "undefined" || reducedMotion()) { setSeen(true); return; }
    const io = new IntersectionObserver((es) => { if (es.some((e) => e.isIntersecting)) { setSeen(true); io.disconnect(); } }, { rootMargin: "0px 0px -15% 0px" });
    io.observe(el);
    return () => io.disconnect();
  }, [ref, seen]);
  return seen;
}

/** Hero illustration: a record slides out of its sleeve and a tonearm swings in. */
export function HeroRecord() {
  const grooves = [140, 128, 116, 104, 92, 80, 68];
  return (
    <figure className="hero-art">
      <svg viewBox="0 0 520 400" aria-hidden="true" focusable="false">
        <g className="disc">
          <circle cx="330" cy="200" r="150" className="vinyl" />
          {grooves.map((r) => <circle key={r} cx="330" cy="200" r={r} className="groove" />)}
          <path d="M330,50 A150,150 0 0 1 452,113" className="sheen" />
          <circle cx="330" cy="200" r="48" className="label" />
          <circle cx="330" cy="200" r="40" className="label-ring" />
          <rect x="300" y="168" width="60" height="5" rx="2.5" className="label-mark" />
          <rect x="310" y="227" width="40" height="5" rx="2.5" className="label-mark" />
          <circle cx="330" cy="200" r="6" className="spindle" />
        </g>
        <g className="sleeve">
          <rect x="20" y="40" width="320" height="320" rx="4" className="sleeve-body" />
          {[118, 96, 74, 52, 30].map((r, i) => <circle key={r} cx="180" cy="200" r={r} className="ripple" style={{ opacity: 1 - i * 0.16 }} />)}
          <rect x="20" y="40" width="320" height="320" rx="4" className="sleeve-edge" />
        </g>
        <g className="arm">
          <circle cx="478" cy="62" r="20" className="arm-base" />
          <path d="M478,62 L452,236 L440,262" className="arm-rod" />
          <rect x="426" y="256" width="26" height="16" rx="3" transform="rotate(25 439 264)" className="arm-head" />
          <circle cx="478" cy="62" r="7" className="arm-pin" />
        </g>
      </svg>
      <figcaption>Illustration, not study data</figcaption>
    </figure>
  );
}

const CX = 30, CY = 296, R = 262;
const pt = (r: number, a: number): [number, number] => [CX + r * Math.cos(a), CY - r * Math.sin(a)];
const P = ([x, y]: [number, number]) => `${x.toFixed(1)},${y.toFixed(1)}`;

/** Quarter record with one groove per policy: interval arc, estimate dot, and SIM and RAND needles. */
export function NeedleDial({ rows, title, id }: { rows: ArmRow[]; title: string; id: string }) {
  const ref = useRef<HTMLDivElement>(null);
  const seen = useInView(ref);
  const sim = rows.find((r) => r.policy === "SIM");
  const rand = rows.find((r) => r.policy === "RAND");
  const needles = [rand, sim].filter((x): x is ArmRow => !!x);
  const radius = (i: number) => R * (0.9 - i * 0.085);
  const ticks = [0, 0.25, 0.5, 0.75, 1, 1.25, 1.5];
  const hi = needles.length === 2 ? (needles[0].estimate > needles[1].estimate ? 0 : 1) : 0;
  return (
    <div ref={ref} className={`dial${seen ? "" : " pending"}`}>
      <svg viewBox="0 0 340 320" role="img" aria-labelledby={`${id}-t`}>
        <title id={`${id}-t`}>{`${title}: mean angular drift per policy drawn as an angle from the start direction, with 95 % intervals. ${rows.map((r) => `${r.policy} ${r.display} ${r.interval_display}`).join("; ")} rad.`}</title>
        <path d={`M${CX},${CY} L${CX + R},${CY} A${R},${R} 0 0 0 ${CX},${CY - R} Z`} className="disc-q" />
        {[0.97, 0.5, 0.42, 0.34].map((f) => <path key={f} d={`M${P(pt(R * f, 0))} A${R * f},${R * f} 0 0 0 ${P(pt(R * f, Math.PI / 2))}`} className="groove" />)}
        {ticks.map((t) => (
          <g key={t}>
            <line x1={pt(R, t)[0]} y1={pt(R, t)[1]} x2={pt(R + 6, t)[0]} y2={pt(R + 6, t)[1]} className="tick" />
            {t === 0 && <text x={CX + R + 6} y={CY + 20} textAnchor="end" className="tick-label">0 rad: start taste</text>}
            {t > 0 && t % 0.5 === 0 && <text x={pt(R + 12, t)[0]} y={pt(R + 12, t)[1] + 4} textAnchor={t > 1.4 ? "middle" : "start"} className="tick-label">{`${t} rad`}</text>}
          </g>
        ))}
        {rows.map((r, i) => {
          const rr = radius(i);
          if (r.ci_low === null || r.ci_high === null) return null;
          return (
            <g key={r.policy} className={`groove-pol pol-${r.policy}`} style={{ transitionDelay: `${300 + i * 60}ms` }}>
              <path d={`M${P(pt(rr, r.ci_low))} A${rr},${rr} 0 0 0 ${P(pt(rr, r.ci_high))}`} className="ci-arc" />
              <circle cx={pt(rr, r.estimate)[0]} cy={pt(rr, r.estimate)[1]} r={4} className="est" />
            </g>
          );
        })}
        {needles.map((n, i) => (
          <g key={n.policy} className={`needle pol-${n.policy}`}
            style={{ transform: seen ? `rotate(${(-n.estimate * 180) / Math.PI}deg)` : "rotate(0deg)", transitionDelay: `${i * 80}ms` }}>
            <line x1={CX} y1={CY} x2={CX + R + 2} y2={CY} />
            <text x={CX + 26} y={CY + (i === hi ? -6 : 14)} className="needle-label">{n.policy} {n.display}</text>
          </g>
        ))}
        <circle cx={CX} cy={CY} r={9} className="hub" />
      </svg>
    </div>
  );
}
