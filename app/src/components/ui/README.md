# 21st.dev component archive

Components pasted from 21st.dev. **These are now wired up and rendering** — the `/app`
scaffold has TypeScript, Tailwind v4, the `@/*` path alias, and the shadcn token layer.
Run `npm run dev` and every component below renders in a gallery at `localhost:5173`
(with a light/dark toggle).

## Components

- `morphing-text.tsx` — blurred cross-fade text morph between a list of strings
- `spotlight-card.tsx` (`GlowCard`) — pointer-tracked radial glow border card
- `background-paths.tsx` — animated SVG line-path hero background + letter-by-letter title reveal
- `animated-tabs.tsx` — tab switcher with a `layoutId` sliding active-tab highlight
- `spinner.tsx` — 8 loader variants (default/circle/pinwheel/circle-filled/ellipsis/ring/bars/infinite)
- `gradient-button.tsx` — cva-based button with a gradient variant
- `shimmer-text.tsx` — background-clip gradient sweep across text, 20 color variants
- `animated-beam.tsx` — SVG beam with an animated gradient between two element refs

Plus `button.tsx` — a standard shadcn Button, added because `background-paths.tsx`
imports it.

Each component has a matching `*.demo.tsx` showing example usage. `app/src/App.tsx`
renders all of them as a gallery.

## Setup notes

- Tailwind v4 via `@tailwindcss/vite` (no `tailwind.config.js` — theme lives in
  `app/src/index.css` under `@theme inline`).
- Dark mode is class-based (`<html class="dark">`), wired to the gallery's toggle.
- `index.css` also carries the plain-CSS `.gradient-button` rules that
  `gradient-button.tsx` expects; they don't ship as Tailwind utilities.
- `motion` and `framer-motion` are both installed — the newer snippets import
  `motion/react`, the older ones `framer-motion`. Same library post-rename.

## Known rough edges

- `spotlight-card.demo.tsx` uses `w-screen h-screen`, so inside the gallery frame it
  overflows and only 2 of its 3 cards are visible.
- `animated-beam.demo.tsx` uses hand-drawn approximations of the SolidWorks / KiCad /
  Blender / Raspberry Pi / Arduino / Claude marks. Swap in `simple-icons` paths for
  accurate artwork.
- `AnimatedBeam` recomputes its path only on container resize, so beams go stale if
  children move without the container changing size (visible under HMR; fine on reload).
