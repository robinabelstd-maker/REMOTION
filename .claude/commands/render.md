# /render

Re-render the current Instagram Reel to `out/reel.mp4`.

## Steps

1. Run the render command using the Playwright headless shell (no network required):

```bash
npx remotion render src/index.ts InstagramReel out/reel.mp4 \
  --browser-executable=/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell
```

2. When complete, confirm the output file size and path:

```bash
ls -lh out/reel.mp4
```

3. Report the file size and full path to the user.

## Notes

- Output: `out/reel.mp4` — 1080×1920, 30fps, 20s (600 frames)
- Codec: H.264
- Browser: uses local Playwright headless shell at `/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell`
- Do NOT attempt to download Chrome — it is blocked in this environment
