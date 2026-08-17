# 21st.dev component archive

Snippets pasted from 21st.dev, saved as-is for later integration. Not yet wired up —
they assume TypeScript, Tailwind, shadcn/ui conventions (`@/lib/utils` → `cn`), and these
packages that aren't installed yet: `@radix-ui/react-slot`, `class-variance-authority`,
`lucide-react`, `tailwind-merge` / `clsx`. The current `/app` scaffold is plain JS + Framer
Motion only (no TypeScript, no Tailwind).

## Archived so far

- `morphing-text.tsx` — blurred cross-fade text morph between a list of strings
- `spotlight-card.tsx` (`GlowCard`) — pointer-tracked radial glow border card
- `background-paths.tsx` — animated SVG line-path hero background + letter-by-letter title reveal
- `animated-tabs.tsx` — tab switcher with a `layoutId` sliding active-tab highlight
- `spinner.tsx` — 8 loader variants (default/circle/pinwheel/circle-filled/ellipsis/ring/bars/infinite)
- `gradient-button.tsx` — cva-based button with a gradient variant

Each component has a matching `*.demo.tsx` showing example usage.

## Still to come

More snippets to be pasted in (up to ~10 total per the original request).

## Integration TODO (once all snippets are in)

1. Add TypeScript to the Vite app (`tsconfig.json`, rename remaining `.jsx` → `.tsx`).
2. Add Tailwind CSS + configure `@/*` path alias to `app/src/*`.
3. Add `app/src/lib/utils.ts` exporting `cn` (clsx + tailwind-merge).
4. Install `@radix-ui/react-slot`, `class-variance-authority`, `lucide-react`, `clsx`, `tailwind-merge`.
5. Add a shadcn-style `Button` component (referenced by `background-paths.tsx`).
6. Verify each demo renders.
