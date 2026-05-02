import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import "@fontsource/inter/500.css";
import "@fontsource/inter/700.css";
import "@fontsource/inter/900.css";

const fontFamily = "Inter, Arial Black, sans-serif";

// ─── Colors ───────────────────────────────────────────────────────────────────
const BLACK = "#000000";
const NAVY = "#0a0e27";
const WHITE = "#FFFFFF";
const ORANGE = "#ff6b35";
const GOLD = "#FFD700";
const RED = "#ff3838";
const GREY = "#888888";
const DARK_GREY = "#666666";
const MID_GREY = "#B0B0B0";
const CARD_BG = "#0f0f1a";

// ─── Helpers ──────────────────────────────────────────────────────────────────
const cl = (
  val: number,
  fromRange: [number, number],
  toRange: [number, number]
) =>
  interpolate(val, fromRange, toRange, {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

const spr = (
  frame: number,
  fps: number,
  damping: number,
  stiffness: number,
  mass = 1
) => spring({ frame, fps, config: { damping, stiffness, mass } });

const fmt = (n: number) =>
  Math.floor(n).toLocaleString("nl-NL");

// ─── Deterministic particles (40) ─────────────────────────────────────────────
const PARTICLES = Array.from({ length: 40 }, (_, i) => ({
  x: ((Math.sin(i * 2.7) * 0.5 + 0.5) * 1080),
  y: ((Math.cos(i * 1.9) * 0.5 + 0.5) * 1920),
  size: 2 + (Math.sin(i * 3.1) * 0.5 + 0.5) * 4,
  opacity: 0.1 + (Math.sin(i * 1.3) * 0.5 + 0.5) * 0.2,
  speed: 0.4 + (Math.sin(i * 2.1) * 0.5 + 0.5) * 0.8,
  drift: Math.sin(i * 0.9) * 8,
}));

// 6 bokeh circles
const BOKEH = [
  { x: 200, y: 500, r: 280, col: ORANGE, op: 0.10, spd: 0.0015 },
  { x: 900, y: 900, r: 320, col: GOLD, op: 0.08, spd: 0.0012 },
  { x: 380, y: 1400, r: 260, col: ORANGE, op: 0.12, spd: 0.0018 },
  { x: 820, y: 250, r: 300, col: GOLD, op: 0.09, spd: 0.001 },
  { x: 120, y: 1250, r: 240, col: ORANGE, op: 0.11, spd: 0.0014 },
  { x: 750, y: 1720, r: 290, col: GOLD, op: 0.10, spd: 0.0016 },
];

// ─── Background ───────────────────────────────────────────────────────────────
function Background() {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill>
      {/* Base radial gradient */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: `radial-gradient(ellipse 70% 60% at 50% 50%, ${NAVY} 0%, ${BLACK} 100%)`,
        }}
      />

      {/* Film grain — SVG turbulence seeded by frame */}
      <svg
        style={{
          position: "absolute",
          width: "100%",
          height: "100%",
          opacity: 0.10,
          mixBlendMode: "overlay",
        }}
      >
        <filter id="grain">
          <feTurbulence
            type="fractalNoise"
            baseFrequency="0.65"
            numOctaves="4"
            seed={frame % 99}
            stitchTiles="stitch"
            result="noise"
          />
          <feColorMatrix type="saturate" values="0" in="noise" />
        </filter>
        <rect width="100%" height="100%" filter="url(#grain)" fill="white" />
      </svg>

      {/* Bokeh circles */}
      {BOKEH.map((b, i) => {
        const a = frame * b.spd + (i * Math.PI * 2) / 6;
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: b.x + Math.cos(a) * 60 - b.r / 2,
              top: b.y + Math.sin(a) * 80 - b.r / 2,
              width: b.r,
              height: b.r,
              borderRadius: "50%",
              background: `radial-gradient(circle, ${b.col} 0%, transparent 70%)`,
              opacity: b.op,
              filter: "blur(40px)",
            }}
          />
        );
      })}

      {/* Floating particles */}
      {PARTICLES.map((p, i) => {
        const y = ((p.y - p.speed * frame * 1.5) % 1920 + 1920) % 1920;
        const x = p.x + Math.sin(frame * 0.02 + i * 0.7) * p.drift;
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: x,
              top: y,
              width: p.size,
              height: p.size,
              borderRadius: "50%",
              background: WHITE,
              opacity: p.opacity,
              filter: "blur(1px)",
            }}
          />
        );
      })}

      {/* Lens vignette */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background:
            "radial-gradient(ellipse 85% 75% at 50% 50%, transparent 40%, rgba(0,0,0,0.25) 100%)",
          pointerEvents: "none",
        }}
      />
    </AbsoluteFill>
  );
}

// ─── Lens Flare ───────────────────────────────────────────────────────────────
function LensFlare({
  startFrame,
  cx = 540,
  cy = 700,
}: {
  startFrame: number;
  cx?: number;
  cy?: number;
}) {
  const frame = useCurrentFrame();
  const local = frame - startFrame;
  if (local < 0 || local > 6) return null;
  const op = interpolate(local, [0, 2, 4, 6], [0, 0.9, 0.6, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <div
        style={{
          position: "absolute",
          left: cx - 200,
          top: cy - 200,
          width: 400,
          height: 400,
          background: `radial-gradient(circle, rgba(255,107,53,0.8) 0%, rgba(255,214,0,0.4) 30%, transparent 70%)`,
          opacity: op,
          filter: "blur(4px)",
        }}
      />
      {[0, 60, 120, 180, 240, 300].map((angle, i) => (
        <div
          key={i}
          style={{
            position: "absolute",
            left: cx,
            top: cy,
            width: 280 + i * 20,
            height: 2,
            background: `linear-gradient(to right, rgba(255,107,53,0.5), transparent)`,
            transform: `rotate(${angle}deg)`,
            transformOrigin: "0 50%",
            opacity: op * 0.4,
          }}
        />
      ))}
    </AbsoluteFill>
  );
}

// ─── Motion blur wipe ─────────────────────────────────────────────────────────
function MotionBlurWipe({ startFrame }: { startFrame: number }) {
  const frame = useCurrentFrame();
  const local = frame - startFrame;
  if (local < 0 || local > 10) return null;
  const progress = cl(local, [0, 8], [0, 1]);
  const op = interpolate(local, [0, 2, 7, 10], [0, 1, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ pointerEvents: "none", overflow: "hidden" }}>
      {Array.from({ length: 10 }, (_, i) => (
        <div
          key={i}
          style={{
            position: "absolute",
            top: 0,
            bottom: 0,
            left: -1200 + progress * (1080 + 1200) + i * 50,
            width: 100 + i * 15,
            background: `rgba(255,255,255,${0.04 - i * 0.003})`,
            opacity: op,
            filter: "blur(4px)",
          }}
        />
      ))}
      {/* Black flash on frame 5 */}
      {local === 5 && (
        <div style={{ position: "absolute", inset: 0, background: BLACK }} />
      )}
    </AbsoluteFill>
  );
}

// ─── SCENE 1: HOOK (0–90) ─────────────────────────────────────────────────────
function Scene1() {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (frame > 92) return null;

  const camScale = cl(frame, [0, 90], [1.0, 1.04]);

  // "97%" pop — frame 5
  const bigScale = frame >= 5 ? spr(frame - 5, fps, 10, 220) : 0;
  const bigOp = cl(frame, [5, 10], [0, 1]);

  // Stagger "VAN DE NEDERLANDERS" — frame 30
  const subLabel = "VAN DE NEDERLANDERS";

  // "BLIJFT ARM." bounce — frame 60
  const armScale = frame >= 60 ? spr(frame - 60, fps, 10, 220) : 0;
  const armOp = cl(frame, [60, 65], [0, 1]);

  // Red underline draw — frame 78
  const underW = cl(frame, [78, 88], [0, 100]);

  return (
    <AbsoluteFill
      style={{
        justifyContent: "center",
        alignItems: "center",
        transform: `scale(${camScale})`,
      }}
    >
      <div style={{ textAlign: "center", position: "relative", padding: "0 80px" }}>
        {/* 97% */}
        <div
          style={{
            fontFamily,
            fontWeight: 900,
            fontSize: 200,
            color: WHITE,
            lineHeight: 1,
            letterSpacing: "-6px",
            transform: `scale(${bigScale})`,
            opacity: bigOp,
            display: "inline-block",
            textShadow: `0 0 80px rgba(255,107,53,0.5)`,
          }}
        >
          97%
        </div>

        {/* VAN DE NEDERLANDERS — letter stagger */}
        {frame >= 30 && (
          <div
            style={{
              display: "flex",
              justifyContent: "center",
              flexWrap: "nowrap",
              marginTop: 8,
            }}
          >
            {subLabel.split("").map((ch, i) => {
              const cop = cl(frame, [30 + i, 33 + i], [0, 1]);
              return (
                <span
                  key={i}
                  style={{
                    fontFamily,
                    fontWeight: 700,
                    fontSize: 50,
                    color: GREY,
                    letterSpacing: "6px",
                    opacity: cop,
                  }}
                >
                  {ch === " " ? " " : ch}
                </span>
              );
            })}
          </div>
        )}

        {/* BLIJFT ARM. */}
        {frame >= 60 && (
          <div
            style={{
              position: "relative",
              marginTop: 24,
              display: "inline-block",
            }}
          >
            <div
              style={{
                fontFamily,
                fontWeight: 900,
                fontSize: 95,
                color: RED,
                letterSpacing: "-3px",
                transform: `scale(${armScale})`,
                opacity: armOp,
                display: "inline-block",
              }}
            >
              BLIJFT ARM.
            </div>
            <div
              style={{
                position: "absolute",
                bottom: -4,
                left: 0,
                height: 10,
                width: `${underW}%`,
                background: RED,
                borderRadius: 5,
              }}
            />
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
}

// ─── SCENE 3: HET PROBLEEM (100–240) ─────────────────────────────────────────
function Scene3() {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (frame < 100 || frame > 242) return null;
  const lo = frame - 100;

  // "Ze ruilen" slide from left
  const zeSlide = interpolate(spr(lo, fps, 14, 180), [0, 1], [-300, 0]);
  const zeOp = cl(lo, [0, 10], [0, 1]);

  // TIJD pop — lo 30
  const tijdScale = lo >= 30 ? spr(lo - 30, fps, 10, 220) : 0;

  // Arrow appears lo 60, continuous rotation
  const arrowOp = cl(lo, [60, 70], [0, 1]);
  const arrowRot = lo >= 60 ? ((lo - 60) / 90) * 360 : 0;

  // GELD pop — lo 75
  const geldScale = lo >= 75 ? spr(lo - 75, fps, 10, 220) : 0;

  // Red X — lo 120
  const xScale = lo >= 120 ? spr(lo - 120, fps, 12, 180) : 0;
  const xOp = cl(lo, [120, 126], [0, 0.7]);

  // Dim everything — lo 130
  const groupOp = cl(lo, [130, 140], [1, 0.3]);

  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      <div style={{ textAlign: "center", opacity: groupOp }}>
        {/* Ze ruilen */}
        <div
          style={{
            fontFamily,
            fontWeight: 700,
            fontSize: 80,
            color: WHITE,
            transform: `translateX(${zeSlide}px)`,
            opacity: zeOp,
            textShadow: `0 4px 24px rgba(255,107,53,0.3)`,
            marginBottom: 20,
          }}
        >
          Ze ruilen
        </div>

        {/* TIJD ⇄ GELD row */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: 24,
          }}
        >
          <div
            style={{
              fontFamily,
              fontWeight: 900,
              fontSize: 155,
              color: GOLD,
              letterSpacing: "-5px",
              transform: `scale(${tijdScale})`,
              display: "inline-block",
              textShadow: `0 0 60px rgba(255,214,0,0.5)`,
            }}
          >
            TIJD
          </div>

          {lo >= 60 && (
            <div
              style={{
                fontSize: 80,
                color: ORANGE,
                opacity: arrowOp,
                transform: `rotate(${arrowRot}deg)`,
                display: "inline-block",
                lineHeight: 1,
              }}
            >
              ⇄
            </div>
          )}

          {lo >= 75 && (
            <div
              style={{
                fontFamily,
                fontWeight: 900,
                fontSize: 155,
                color: GOLD,
                letterSpacing: "-5px",
                transform: `scale(${geldScale})`,
                display: "inline-block",
                textShadow: `0 0 60px rgba(255,214,0,0.5)`,
              }}
            >
              GELD
            </div>
          )}
        </div>

        {/* Red X overlay */}
        {lo >= 120 && (
          <div
            style={{
              position: "absolute",
              top: "50%",
              left: "50%",
              transform: `translate(-50%, -50%) scale(${xScale})`,
              fontSize: 280,
              color: RED,
              opacity: xOp,
              lineHeight: 1,
              fontFamily,
              fontWeight: 900,
              filter: "drop-shadow(0 0 50px rgba(255,56,56,0.7))",
              pointerEvents: "none",
            }}
          >
            ✕
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
}

// ─── SCENE 4: WHISPER (240–330) ───────────────────────────────────────────────
function Scene4() {
  const frame = useCurrentFrame();
  if (frame < 240 || frame > 332) return null;
  const lo = frame - 240;

  const blackFlash = cl(lo, [0, 8], [1, 0]);
  const text = "Maar er is een andere manier...";
  const shown = Math.floor(Math.max(0, (lo - 10) / 2));
  const displayed = text.slice(0, shown);
  const textOp = interpolate(lo, [8, 16, 68, 78], [0, 1, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const blink = Math.floor(lo / 14) % 2 === 0;

  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: BLACK,
          opacity: blackFlash,
        }}
      />
      <div
        style={{
          fontFamily,
          fontWeight: 500,
          fontSize: 55,
          color: GREY,
          fontStyle: "italic",
          textAlign: "center",
          padding: "0 100px",
          opacity: textOp,
          lineHeight: 1.4,
        }}
      >
        {displayed}
        <span style={{ opacity: blink ? 1 : 0, color: ORANGE }}>|</span>
      </div>
    </AbsoluteFill>
  );
}

// ─── SCENE 5: DE REVEAL (330–480) ─────────────────────────────────────────────
function Scene5() {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (frame < 330 || frame > 482) return null;
  const lo = frame - 330;

  // Glow burst
  const glowScale = cl(lo, [0, 20], [0, 4]);
  const glowOp = interpolate(lo, [0, 4, 20], [0, 0.6, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  // Camera zoom-out
  const camScale = cl(lo, [80, 110], [1.1, 1.0]);

  // "DIGITALE" letter pop starting lo 10, 3-frame stagger
  const DIGITALE = "DIGITALE";
  // "PRODUCTEN" starting lo 50
  const PRODUCTEN = "PRODUCTEN";

  // Counter €0 → €8347 (lo 90–140)
  const counterVal = cl(lo, [90, 140], [0, 8347]);
  const counterOp = cl(lo, [88, 96], [0, 1]);
  const euroPulse = 1 + 0.04 * Math.sin((lo / 30) * Math.PI * 2);

  // Label
  const labelOp = cl(lo, [138, 148], [0, 1]);

  return (
    <AbsoluteFill
      style={{
        justifyContent: "center",
        alignItems: "center",
        transform: `scale(${camScale})`,
      }}
    >
      {/* Glow burst */}
      <div
        style={{
          position: "absolute",
          left: "50%",
          top: "50%",
          width: 400,
          height: 400,
          transform: `translate(-50%, -50%) scale(${glowScale})`,
          background:
            "radial-gradient(circle, rgba(255,107,53,0.5) 0%, transparent 70%)",
          opacity: glowOp,
          filter: "blur(20px)",
          pointerEvents: "none",
        }}
      />

      <div style={{ textAlign: "center" }}>
        {/* DIGITALE — letter stagger */}
        <div
          style={{ display: "flex", justifyContent: "center", marginBottom: 4 }}
        >
          {DIGITALE.split("").map((ch, i) => {
            const sc = lo >= 10 + i * 3 ? spr(lo - (10 + i * 3), fps, 12, 200) : 0;
            return (
              <span
                key={i}
                style={{
                  fontFamily,
                  fontWeight: 900,
                  fontSize: 130,
                  color: WHITE,
                  letterSpacing: "-4px",
                  display: "inline-block",
                  transform: `scale(${sc})`,
                  textShadow: `0 4px 24px rgba(255,107,53,0.3)`,
                }}
              >
                {ch}
              </span>
            );
          })}
        </div>

        {/* PRODUCTEN — letter stagger */}
        <div
          style={{ display: "flex", justifyContent: "center", marginBottom: 48 }}
        >
          {PRODUCTEN.split("").map((ch, i) => {
            const sc = lo >= 50 + i * 3 ? spr(lo - (50 + i * 3), fps, 12, 200) : 0;
            return (
              <span
                key={i}
                style={{
                  fontFamily,
                  fontWeight: 900,
                  fontSize: 130,
                  color: ORANGE,
                  letterSpacing: "-4px",
                  display: "inline-block",
                  transform: `scale(${sc})`,
                  textShadow: `0 4px 24px rgba(255,107,53,0.5)`,
                }}
              >
                {ch}
              </span>
            );
          })}
        </div>

        {/* Counter */}
        {lo >= 88 && (
          <div style={{ opacity: counterOp }}>
            {lo >= 138 && (
              <div
                style={{
                  fontFamily,
                  fontWeight: 500,
                  fontSize: 32,
                  color: MID_GREY,
                  letterSpacing: "4px",
                  textTransform: "uppercase",
                  marginBottom: 8,
                  opacity: labelOp,
                }}
              >
                GEMIDDELDE OMZET / MAAND
              </div>
            )}
            <div
              style={{
                fontFamily,
                fontWeight: 900,
                fontSize: 90,
                color: GOLD,
                letterSpacing: "-3px",
                display: "flex",
                justifyContent: "center",
                alignItems: "baseline",
              }}
            >
              <span
                style={{
                  display: "inline-block",
                  transform: `scale(${euroPulse})`,
                }}
              >
                €
              </span>
              {fmt(counterVal)}
            </div>
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
}

// ─── SCENE 6: DE 3 REDENEN (480–720) ─────────────────────────────────────────

function CardView({
  number,
  title,
  subtitle,
  slideProgress,
  opacity,
  showChart,
  chartProgress,
}: {
  number: string;
  title: string;
  subtitle: string;
  slideProgress: number;
  opacity: number;
  showChart?: boolean;
  chartProgress?: number;
}) {
  const slideX = interpolate(slideProgress, [0, 1], [500, 0]);
  const chartW = 150;
  const chartH = 60;
  const cp = chartProgress ?? 0;
  const points = Array.from({ length: 20 }, (_, i) => {
    const t = i / 19;
    return `${t * chartW * cp},${chartH - Math.pow(t, 2) * chartH}`;
  });

  return (
    <div
      style={{
        transform: `translateX(${slideX}px)`,
        opacity,
        width: 880,
      }}
    >
      {/* Gradient border wrapper */}
      <div
        style={{
          padding: 2,
          borderRadius: 28,
          background:
            "linear-gradient(135deg, #ff6b35 0%, rgba(255,107,53,0.15) 60%, transparent 100%)",
        }}
      >
        <div
          style={{
            background: CARD_BG,
            borderRadius: 26,
            padding: "36px 48px",
            display: "flex",
            alignItems: "center",
            gap: 36,
          }}
        >
          <div
            style={{
              fontFamily,
              fontWeight: 900,
              fontSize: 96,
              color: ORANGE,
              lineHeight: 1,
              minWidth: 110,
              letterSpacing: "-3px",
            }}
          >
            {number}
          </div>
          <div style={{ flex: 1 }}>
            <div
              style={{
                fontFamily,
                fontWeight: 900,
                fontSize: 65,
                color: WHITE,
                lineHeight: 1.1,
                letterSpacing: "-2px",
                marginBottom: 6,
              }}
            >
              {title}
            </div>
            <div
              style={{
                fontFamily,
                fontWeight: 500,
                fontSize: 36,
                color: GREY,
              }}
            >
              {subtitle}
            </div>
          </div>
          {showChart && (
            <svg
              width={chartW}
              height={chartH + 10}
              style={{ overflow: "visible", flexShrink: 0 }}
            >
              <polyline
                points={points.join(" ")}
                fill="none"
                stroke={ORANGE}
                strokeWidth={8}
                strokeLinecap="round"
                strokeLinejoin="round"
                opacity={0.25}
              />
              <polyline
                points={points.join(" ")}
                fill="none"
                stroke={ORANGE}
                strokeWidth={3}
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          )}
        </div>
      </div>
    </div>
  );
}

function Scene6() {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (frame < 480 || frame > 722) return null;
  const lo = frame - 480;

  const introOp = cl(lo, [0, 12], [0, 1]);
  const labelOp = cl(lo, [10, 22], [0, 1]);

  // Card 1: lo 30; card 2: lo 110; card 3: lo 190
  const c1Start = 30;
  const c2Start = 110;
  const c3Start = 190;

  const c1Slide = lo >= c1Start ? spr(lo - c1Start, fps, 14, 180) : 0;
  const c1Op = cl(lo, [c1Start, c1Start + 10], [0, 1]);

  const c2Slide = lo >= c2Start ? spr(lo - c2Start, fps, 14, 180) : 0;
  const c2Op = cl(lo, [c2Start, c2Start + 10], [0, 1]);

  const c3Slide = lo >= c3Start ? spr(lo - c3Start, fps, 14, 180) : 0;
  const c3Op = cl(lo, [c3Start, c3Start + 10], [0, 1]);
  const chartProg = cl(lo, [c3Start + 20, c3Start + 50], [0, 1]);

  // When next card appears, previous ones scale down + move up
  const c1Scale = cl(lo, [c2Start, c2Start + 20], [1, 0.85]);
  const c1Fade = cl(lo, [c2Start, c2Start + 20], [1, 0.6]);
  const c1Shift = cl(lo, [c2Start, c2Start + 20], [0, -24]);

  const c2Scale = cl(lo, [c3Start, c3Start + 20], [1, 0.85]);
  const c2Fade = cl(lo, [c3Start, c3Start + 20], [1, 0.6]);
  const c2Shift = cl(lo, [c3Start, c3Start + 20], [0, -24]);

  return (
    <AbsoluteFill
      style={{
        opacity: introOp,
        paddingTop: 300,
        paddingBottom: 440,
        paddingLeft: 100,
        paddingRight: 100,
        flexDirection: "column",
      }}
    >
      {/* Section label */}
      <div
        style={{
          fontFamily,
          fontWeight: 700,
          fontSize: 38,
          color: DARK_GREY,
          letterSpacing: "4px",
          textTransform: "uppercase",
          marginBottom: 36,
          opacity: labelOp,
        }}
      >
        WAAROM DIT WERKT →
      </div>

      {/* Card stack */}
      <div
        style={{ display: "flex", flexDirection: "column", gap: 16, flex: 1, justifyContent: "center" }}
      >
        {lo >= c1Start && (
          <div
            style={{
              transform: `translateY(${c1Shift}px) scale(${c1Scale})`,
              opacity: c1Fade * c1Op,
              transformOrigin: "top center",
            }}
          >
            <CardView
              number="01"
              title="GEEN VOORRAAD"
              subtitle="Geen risico, geen kosten"
              slideProgress={c1Slide}
              opacity={1}
            />
          </div>
        )}
        {lo >= c2Start && (
          <div
            style={{
              transform: `translateY(${c2Shift}px) scale(${c2Scale})`,
              opacity: c2Fade * c2Op,
              transformOrigin: "top center",
            }}
          >
            <CardView
              number="02"
              title="24/7 VERKOPEN"
              subtitle="Slaap terwijl je verdient"
              slideProgress={c2Slide}
              opacity={1}
            />
          </div>
        )}
        {lo >= c3Start && (
          <CardView
            number="03"
            title="ONEINDIG SCHAALBAAR"
            subtitle="1 product, 10.000 klanten"
            slideProgress={c3Slide}
            opacity={c3Op}
            showChart
            chartProgress={chartProg}
          />
        )}
      </div>
    </AbsoluteFill>
  );
}

// ─── SCENE 7: SOCIAL PROOF + CTA (720–900) ────────────────────────────────────
function Scene7() {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (frame < 720) return null;
  const lo = frame - 720;

  // Dark overlay transition
  const overlayOp = cl(lo, [0, 10], [0, 0.82]);

  // Social proof counter (lo 15–50 count, lo 50+ "doen dit al.")
  const countVal = cl(lo, [15, 45], [0, 12847]);
  const countScale = lo >= 15 ? spr(lo - 15, fps, 12, 200) : 0;
  const countOp = cl(lo, [13, 20], [0, 1]);
  const doitOp = cl(lo, [50, 62], [0, 1]);
  const groupFade = cl(lo, [86, 96], [1, 0]);

  // Handle + CTA (lo 100)
  const handleScale = lo >= 100 ? spr(lo - 100, fps, 12, 200) : 0;
  const handleOp = cl(lo, [98, 107], [0, 1]);
  const ctaOp = cl(lo, [128, 140], [0, 1]);

  // Pulse on handle group
  const pulse = 1 + 0.025 * Math.sin((lo / 25) * Math.PI * 2);

  // 4 rotating orange glows
  const glows = [0, 1, 2, 3].map((i) => {
    const a = (lo / 240) * 2 * Math.PI + (i * Math.PI) / 2;
    return { x: 540 + Math.cos(a) * 260, y: 960 + Math.sin(a) * 260 };
  });

  // Vignette intensifies at close
  const vigOp = cl(lo, [158, 180], [0.25, 0.55]);

  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      {/* Dark overlay */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: BLACK,
          opacity: overlayOp,
          pointerEvents: "none",
        }}
      />

      {/* Rotating glows */}
      {lo >= 100 &&
        glows.map((g, i) => (
          <div
            key={i}
            style={{
              position: "absolute",
              left: g.x - 200,
              top: g.y - 200,
              width: 400,
              height: 400,
              borderRadius: "50%",
              background:
                "radial-gradient(circle, rgba(255,107,53,0.22) 0%, transparent 70%)",
              filter: "blur(60px)",
              pointerEvents: "none",
            }}
          />
        ))}

      {/* Social proof */}
      {lo >= 13 && lo < 97 && (
        <div style={{ textAlign: "center", opacity: groupFade }}>
          <div
            style={{
              fontFamily,
              fontWeight: 900,
              fontSize: 90,
              color: WHITE,
              letterSpacing: "-3px",
              transform: `scale(${countScale})`,
              opacity: countOp,
              display: "inline-block",
            }}
          >
            {fmt(countVal)} mensen
          </div>
          <div
            style={{
              fontFamily,
              fontWeight: 700,
              fontSize: 70,
              color: ORANGE,
              opacity: doitOp,
              marginTop: 12,
            }}
          >
            doen dit al.
          </div>
        </div>
      )}

      {/* Handle + CTA */}
      {lo >= 98 && (
        <div
          style={{
            textAlign: "center",
            transform: `scale(${pulse})`,
            opacity: handleOp,
          }}
        >
          <div
            style={{
              fontFamily,
              fontWeight: 900,
              fontSize: 130,
              color: WHITE,
              letterSpacing: "-4px",
              transform: `scale(${handleScale})`,
              display: "inline-block",
              textShadow: `0 4px 24px rgba(255,107,53,0.35)`,
            }}
          >
            @jouwhandle
          </div>
          <div
            style={{
              fontFamily,
              fontWeight: 700,
              fontSize: 60,
              color: ORANGE,
              opacity: ctaOp,
              marginTop: 18,
            }}
          >
            Volg voor meer →
          </div>
        </div>
      )}

      {/* Intensifying vignette */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: `radial-gradient(ellipse 80% 70% at 50% 50%, transparent 30%, rgba(0,0,0,${vigOp}) 100%)`,
          pointerEvents: "none",
        }}
      />
    </AbsoluteFill>
  );
}

// ─── Root Composition ─────────────────────────────────────────────────────────
export const DigitaleProducten = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{ background: BLACK }}>
      <Background />
      <Scene1 />
      <Scene3 />
      <Scene4 />
      <Scene5 />
      <Scene6 />
      <Scene7 />
      <LensFlare startFrame={15} cx={540} cy={680} />
      <MotionBlurWipe startFrame={90} />
    </AbsoluteFill>
  );
};
