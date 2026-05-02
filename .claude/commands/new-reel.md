# /new-reel

Scaffold a new Instagram Reel composition based on BRAND.md guidelines.

## Steps

1. Read `BRAND.md` in the project root to load brand colors, fonts, tone, and content structure.

2. Ask the user for:
   - **Topic/Hook**: What is the hook line? (e.g. "De meeste mensen weten niet dat...")
   - **Body points**: 2–4 bullet points to display in the body section
   - **CTA**: The call-to-action text (default: "Volg @mrvisionaire")
   - **Duration**: Total reel duration in seconds (default: 20s)
   - **Output file name**: e.g. `reel-2` (default: `reel`)

3. Create a new composition file at `src/<OutputName>.tsx` by duplicating the structure of `src/InstagramReel.tsx` and applying:
   - Brand colors and fonts from `BRAND.md`
   - The provided hook, body points, and CTA
   - Register it in `src/Root.tsx` as a new `<Composition>` with a unique `id`

4. Type-check the new file:
   ```bash
   npx tsc --noEmit
   ```

5. Render a single still frame at the 1-second mark to sanity-check layout:
   ```bash
   npx remotion still src/index.ts <CompositionId> out/<OutputName>-preview.png \
     --browser-executable=/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell \
     --frame=30 --scale=0.25
   ```

6. Report what was created and ask the user if they want to run `/render` to produce the full MP4.

## Notes

- Always respect brand guidelines from `BRAND.md` — colors, typography, tone
- CSS transitions and Tailwind animation classes are FORBIDDEN in Remotion (use `interpolate` + `spring`)
- Use `useCurrentFrame()` + `interpolate()` for all animations
- Headless shell: `/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell`
