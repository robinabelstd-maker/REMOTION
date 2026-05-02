import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
} from "remotion";

const HOOK_END = 120;   // 4s @ 30fps
const BODY_END = 450;   // 15s @ 30fps

const ORANGE = "#ff6b35";
const WHITE = "#ffffff";
const BG_TOP = "#0a0a0a";
const BG_BOTTOM = "#1a1a2e";

const BODY_ITEMS = [
  "Ze stoppen als het moeilijk wordt",
  "Ze missen consistentie en focus",
  "Ze geloven niet in zichzelf",
];

function useTypewriter(text: string, startFrame: number, endFrame: number) {
  const frame = useCurrentFrame();
  const progress = interpolate(frame, [startFrame, endFrame], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return text.slice(0, Math.floor(progress * text.length));
}

function Background() {
  return (
    <AbsoluteFill
      style={{
        background: `linear-gradient(180deg, ${BG_TOP} 0%, ${BG_BOTTOM} 100%)`,
      }}
    />
  );
}

function HookSection() {
  const frame = useCurrentFrame();
  const text = "De meeste mensen\nfalen omdat...";
  const displayed = useTypewriter(text, 10, HOOK_END - 10);

  const fadeIn = interpolate(frame, [0, 20], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const fadeOut = interpolate(frame, [HOOK_END - 15, HOOK_END], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const cursorVisible = Math.floor(frame / 15) % 2 === 0;

  return (
    <AbsoluteFill
      style={{
        justifyContent: "center",
        alignItems: "center",
        opacity: fadeIn * fadeOut,
        padding: "80px",
      }}
    >
      <p
        style={{
          fontFamily: "'Inter', 'Arial Black', sans-serif",
          fontWeight: 800,
          fontSize: "80px",
          color: WHITE,
          textAlign: "center",
          lineHeight: 1.2,
          margin: 0,
          whiteSpace: "pre-line",
          letterSpacing: "-1px",
          textShadow: "0 4px 30px rgba(0,0,0,0.5)",
        }}
      >
        {displayed}
        <span style={{ opacity: cursorVisible ? 1 : 0, color: ORANGE }}>|</span>
      </p>
    </AbsoluteFill>
  );
}

function BulletPoint({
  index,
  text,
  startFrame,
}: {
  index: number;
  text: string;
  startFrame: number;
}) {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  if (frame < startFrame) return null;

  const slideProgress = spring({
    frame: frame - startFrame,
    fps,
    config: { damping: 14, stiffness: 120, mass: 0.8 },
  });

  const opacity = interpolate(frame, [startFrame, startFrame + 10], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const fadeOut = interpolate(frame, [BODY_END - 20, BODY_END], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const translateY = interpolate(slideProgress, [0, 1], [80, 0]);

  return (
    <div
      style={{
        transform: `translateY(${translateY}px)`,
        opacity: opacity * fadeOut,
        display: "flex",
        alignItems: "flex-start",
        gap: "28px",
        marginBottom: "48px",
        padding: "0 80px",
      }}
    >
      <span
        style={{
          fontFamily: "'Inter', 'Arial Black', sans-serif",
          fontWeight: 800,
          fontSize: "72px",
          color: ORANGE,
          lineHeight: 1,
          minWidth: "60px",
          marginTop: "-4px",
        }}
      >
        {index + 1}.
      </span>
      <p
        style={{
          fontFamily: "'Inter', 'Arial', sans-serif",
          fontWeight: 600,
          fontSize: "58px",
          color: WHITE,
          margin: 0,
          lineHeight: 1.3,
        }}
      >
        {text}
      </p>
    </div>
  );
}

function BodySection() {
  const frame = useCurrentFrame();
  const FIRST_IN = HOOK_END + 20;
  const DELAY_BETWEEN = 90; // 3s between each item

  const opacity = interpolate(frame, [HOOK_END, HOOK_END + 15], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{ justifyContent: "center", flexDirection: "column", opacity }}
    >
      {BODY_ITEMS.map((text, i) => (
        <BulletPoint
          key={i}
          index={i}
          text={text}
          startFrame={FIRST_IN + i * DELAY_BETWEEN}
        />
      ))}
    </AbsoluteFill>
  );
}

function CTASection() {
  const frame = useCurrentFrame();
  const localFrame = frame - BODY_END;

  const fadeIn = interpolate(localFrame, [0, 25], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const pulse = 1 + 0.06 * Math.sin((localFrame / 30) * Math.PI * 2);
  const glowOpacity = 0.3 + 0.3 * Math.sin((localFrame / 30) * Math.PI * 2);

  return (
    <AbsoluteFill
      style={{ justifyContent: "center", alignItems: "center", opacity: fadeIn }}
    >
      <div
        style={{
          transform: `scale(${pulse})`,
          position: "relative",
          textAlign: "center",
        }}
      >
        <div
          style={{
            position: "absolute",
            inset: "-40px",
            borderRadius: "32px",
            background: `radial-gradient(ellipse, rgba(255,107,53,${glowOpacity}) 0%, transparent 70%)`,
          }}
        />
        <p
          style={{
            fontFamily: "'Inter', 'Arial Black', sans-serif",
            fontWeight: 800,
            fontSize: "72px",
            color: WHITE,
            margin: 0,
            marginBottom: "16px",
            letterSpacing: "-1px",
          }}
        >
          Klaar om te groeien?
        </p>
        <p
          style={{
            fontFamily: "'Inter', 'Arial Black', sans-serif",
            fontWeight: 900,
            fontSize: "88px",
            color: ORANGE,
            margin: 0,
            letterSpacing: "-2px",
          }}
        >
          Volg @mrvisionaire
        </p>
      </div>
    </AbsoluteFill>
  );
}

export const InstagramReel = () => {
  const frame = useCurrentFrame();

  return (
    <AbsoluteFill>
      <Background />
      {frame < HOOK_END && <HookSection />}
      {frame >= HOOK_END && frame < BODY_END && <BodySection />}
      {frame >= BODY_END && <CTASection />}
    </AbsoluteFill>
  );
};
