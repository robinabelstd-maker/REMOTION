# BRAND.md — @mrvisionaire

Brand guidelines for Instagram Reels created with Remotion.

---

## Identity

- **Handle**: @mrvisionaire
- **Niche**: Mindset, groei, succes — voor ambitieuze jongeren (18–30)
- **Tone**: Direct, motiverend, no-bullshit. Spreekt de kijker aan als gelijke.
- **Language**: Nederlands (informeel, krachtig)

---

## Colors

| Role | Hex | Usage |
|---|---|---|
| Background dark | `#0a0a0a` | Gradient top |
| Background mid | `#1a1a2e` | Gradient bottom |
| Accent / numbers | `#ff6b35` | Numbers, highlights, CTA text |
| Primary text | `#ffffff` | All body and hook text |
| Secondary text | `#a0a0b0` | Optional subtitles or captions |

Background gradient: `linear-gradient(180deg, #0a0a0a 0%, #1a1a2e 100%)`

---

## Typography

| Role | Font | Weight | Size |
|---|---|---|---|
| Hook | Inter | 800 (ExtraBold) | 80px |
| Body points | Inter | 600 (SemiBold) | 58px |
| Accent numbers | Inter | 800 (ExtraBold) | 72px |
| CTA main | Inter | 800 (ExtraBold) | 72px |
| CTA handle | Inter | 900 (Black) | 88px |

Fallback stack: `'Inter', 'Arial Black', sans-serif`  
Letter spacing: `-1px` for hook/CTA, `-2px` for CTA handle  
Line height: `1.2` for hook, `1.3` for body

---

## Animation Principles

- **Hook**: typewriter effect with blinking orange cursor
- **Body**: slide-from-bottom with spring physics (`damping: 14, stiffness: 120, mass: 0.8`)
- **CTA**: sinusoidal pulse scale (1.0 → 1.06) with radial orange glow
- **Transitions**: fade-in/out with `interpolate`, never CSS transitions
- Stagger body items: 3s (90 frames) between each point

---

## Composition Defaults

- **Resolution**: 1080 × 1920 (9:16 portrait, Instagram Reel)
- **FPS**: 30
- **Default duration**: 20s (600 frames)
- **Padding**: 80px horizontal

---

## Standard Segment Structure

| Segment | Duration | Content |
|---|---|---|
| Hook | 0–4s | Bold statement with typewriter effect |
| Body | 4–15s | 2–4 bullet points, spring slide-in |
| CTA | 15–20s | Handle + action line with pulse |

---

## CTA Templates

- `Volg @mrvisionaire`
- `Sla op voor later 🔖`
- `Stuur dit naar iemand die dit nodig heeft`
- `Wat herken jij het meest? Comment hieronder ↓`

---

## Content Pillars

1. **Mindset** — Waarom de meeste mensen falen / wat succesvolle mensen anders doen
2. **Productiviteit** — Systemen, routines, focus
3. **Geld & vrijheid** — Financiële educatie, ondernemerschap
4. **Identiteit** — Wie je bent vs. wie je wilt worden
