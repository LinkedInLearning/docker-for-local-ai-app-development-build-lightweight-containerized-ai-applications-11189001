# Style tokens

The full `:root` token set every deck shares. Copy this verbatim when
starting a new deck.

```css
:root {
  /* surfaces */
  --bg:        #ffffff;
  --bg-soft:   #f7f9fc;
  --bg-grid:   #f1f5f9;

  /* ink */
  --ink:       #0f172a;
  --ink-soft:  #475569;
  --muted:     #94a3b8;

  /* lines */
  --line:      #e2e8f0;
  --line-soft: #eef2f7;

  /* blue (primary accent) */
  --blue-50:   #eff6ff;
  --blue-100:  #dbeafe;
  --blue-500:  #3b82f6;
  --blue-600:  #2563eb;
  --blue-700:  #1d4ed8;

  /* secondary palette */
  --teal-500:  #0ea5e9;
  --amber-500: #f59e0b;
  --amber-50:  #fffbeb;
  --green-500: #10b981;
  --green-50:  #ecfdf5;
  --pink-500:  #ec4899;
  --violet-500:#8b5cf6;
  --violet-50: #f5f3ff;
  --red-500:   #ef4444;
  --red-50:    #fef2f2;

  /* code */
  --code-bg:   #0f172a;
  --code-fg:   #e2e8f0;

  /* shadow + shape */
  --shadow-sm: 0 1px 2px rgba(15,23,42,.06);
  --shadow:    0 1px 2px rgba(15,23,42,.04), 0 12px 32px rgba(15,23,42,.07);
  --radius:    16px;
  --maxw:      1280px;
}
```

## Typography (presentation scale)

The deck is meant to be viewed at a desktop / projection size, so the
type scale is roughly 1.4× a normal browser-doc scale. All sizes below
are pixels.

| Element                | Size  | Weight | Notes                                                |
|------------------------|-------|--------|------------------------------------------------------|
| `.eyebrow`             | 17    | 700    | uppercase, letter-spacing .18em, **`--blue-700`** (~7.4:1) |
| `h1.title`             | 92    | 700    | letter-spacing −0.028em, line-height 1.04            |
| `.accent` (in title)   | inherit | 700  | gradient text (`--blue-600` → `--teal-500`)          |
| `h2.h`                 | 58    | 700    | letter-spacing −0.02em, line-height 1.1, mb 14       |
| `h3.sub`               | 26    | 500    | `--ink-soft`, line-height 1.5, max-width 1000px      |
| `p.lead`               | 28    | 400    | `--ink-soft`, line-height 1.5, max-width 1000px      |
| `.lead-small` (sidebar)| 22    | 400    | inside `.detail` sidebars                            |
| `.cap` (caption)       | 15    | 700    | uppercase, .14em tracking, used inside `.vis`        |
| `.flagname` (big code) | 52    | 700    | mono, decorative big-code badge                      |
| `.cmdline`             | 26    | normal | mono, centered command callout                       |
| `pre.code`             | 20    | normal | mono, line-height 1.6                                |
| `.takeaway-card .quote`| 30    | 600    | one-liner summary                                    |
| `.takeaway-card .foot` | 20    | normal | "next lesson →" line                                 |
| `.path .stop .ttl`     | 23    | 600    | path stop title                                      |
| `.path .stop .desc`    | 18    | normal | path stop description                                |
| `.inline`              | .92em | —      | mono pill for inline code                            |

**Eyebrow contrast.** Use `--blue-700` (#1d4ed8, ~7.4:1 on white), not
`--blue-600` (~5.1:1). At eyebrow size 17 px the text is small enough
to need the higher ratio.

## Code blocks

```css
pre.code {
  background: var(--code-bg);
  color: var(--code-fg);
  padding: 18px 22px;
  border-radius: 14px;
  font: 20px/1.6 ui-monospace, SFMono-Regular, Menlo, monospace;
  overflow-x: auto;
  box-shadow: 0 6px 18px rgba(15,23,42,.15);
  margin: 0;
}
pre.code .k { color: #93c5fd; font-weight: 600; }  /* keywords */
pre.code .s { color: #fcd34d; }                    /* strings */
pre.code .c { color: #64748b; }                    /* comments */
pre.code .v { color: #86efac; }                    /* values */
pre.code .f { color: #fcd34d; font-weight: 600; }  /* flags */
```

## Color usage cheatsheet

- **Blue-600 → teal-500 gradient**: title `.accent`, badges, CTAs,
  takeaway pills, the progress bar.
- **Green-500**: "running", "good", "fresh", check marks, healthy states.
- **Amber-500**: "stopped", warning, build-time/ARG.
- **Red-500**: "bad", anti-pattern column header, danger pruning.
- **Violet-500 / pink-500**: secondary highlights for variety —
  port stickers, networks, env vars.

Never apply the gradient at full saturation across a large surface.
Reserve it for small accents (badges, headlines, the progress bar).

## Spacing

- **Slide padding**: `40px 56px 56px` desktop, `32px 28px 60px` at the
  smaller-viewport breakpoint. Top padding is small and fixed so the
  eyebrow lands at the same Y on every slide.
- **Vertical rhythm between blocks**: 14–22px is the default
  (`h2.h` mb 14, `h3.sub` mb 22, `p.lead` mb 18).
- **Card padding**: 18–24px.
- **Card gap in grids**: 14–18px (default), 24px when only a few items.
- **`.path` margin-top**: 28px (was 48px in the older format —
  reduced for top-anchored content).

## Layout primitives

- **Max content width**: `--maxw: 1280px`.
- **Sidebar in `.detail`**: 420px wide, gap 32px to the visualization.
- **Slides are absolutely positioned** (`position: absolute; inset: 0`)
  inside a relative `.deck`. The deck itself is `height: 100vh`.
- **Top-anchored**: `.slide.active { align-items: flex-start; }` and
  `.slide .wrap { margin: 0 auto; }`.

## Transitions

- **Slide change**: opacity cross-fade, `.55s cubic-bezier(.4, 0, .2, 1)`.
  Both outgoing and incoming slides are visible during the transition.
- **Progress bar**: `width .25s ease`.
- Don't add other animations on top — they compete with the cross-fade.

## Shadows

- Use `--shadow-sm` for static cards inside a `.vis` panel.
- Use `--shadow` (the bigger one) for hero cards, takeaway cards,
  and items on plain `--bg` backgrounds.
- Code blocks get their own dark shadow (`0 6px 18px rgba(15,23,42,.15)`).

## Title art

Every lesson's title slide ships an abstract decorative SVG positioned
right and faded to ~50% opacity. Patterns used so far:

| Lesson | Motif                                             |
|--------|---------------------------------------------------|
| C1 L1  | Stylized container with internal compartments     |
| C1 L2  | Two-row pipeline (boxes + cylinders)              |
| C1 L3  | 6-box package grid (cardboard layout)             |
| C2 L1  | Stacked translucent rectangles                    |
| C2 L2  | Lines on a card (file lines)                      |
| C2 L3  | Layered build artifacts                           |
| C2 L4  | Image → 3 containers (fan-out)                    |
| C2 L5  | Circle with checkmark                             |
| C2 L6  | 2-column grid of containers + dots                |

Pick something simple that **suggests** the topic. Don't render literal
Docker whales or icons — keep it abstract.

## Chrome (or lack of it)

The presentation format keeps the canvas clean. The only on-screen
chrome is a slim 4-px progress bar pinned to the top:

```css
.progress {
  position: fixed; top: 0; left: 0;
  height: 4px; width: 0%;
  background: linear-gradient(90deg, var(--blue-600), var(--teal-500));
  z-index: 50;
  transition: width .25s ease;
}
```

No brand strip. No page counter. No keyboard-hint kbd. Slide content
owns the canvas.

## RAG architecture diagram palette

When a deck reproduces the drawio "RAG Design Architecture" diagram
(C1 L2 is the canonical example), use this extra palette to match the
source. These colors are semantically tied to specific services — keep
them consistent across decks so a reader who learns the colors in C1 L2
recognizes them again in later chapters.

```css
:root {
  --rag-yellow-bg:#FFF9C4; --rag-yellow-stroke:#F57F17;  /* Document Sources */
  --rag-green-bg:#E8F5E9;  --rag-green-stroke:#2E7D32;   /* Parsing / Chunking / ingestion */
  --rag-purple-bg:#F3E5F5; --rag-purple-stroke:#6A1B9A;  /* Embedding / LLM */
  --rag-cyl-bg:#DCEDC8;    --rag-cyl-stroke:#33691E;     /* Vector Store */
  --rag-blue-bg:#E3F2FD;   --rag-blue-stroke:#1565C0;    /* Context / query */
  --rag-indigo-bg:#E8EAF6; --rag-indigo-stroke:#283593;  /* Search / Reranker */
  --rag-user-bg:#dae8fc;   --rag-user-stroke:#6c8ebf;    /* User Question */
}
```

| Service                | Background           | Border                    |
|------------------------|----------------------|---------------------------|
| Document Sources       | `--rag-yellow-bg`    | `--rag-yellow-stroke`     |
| Document Parsing       | `--rag-green-bg`     | `--rag-green-stroke`      |
| Chunking / Splitting   | `--rag-green-bg`     | `--rag-green-stroke`      |
| Embedding Model        | `--rag-purple-bg`    | `--rag-purple-stroke`     |
| Vector Store           | `--rag-cyl-bg`       | `--rag-cyl-stroke`        |
| User Question          | `--rag-user-bg`      | `--rag-user-stroke`       |
| Similarity Search      | `--rag-indigo-bg`    | `--rag-indigo-stroke`     |
| Reranker               | `--rag-indigo-bg`    | `--rag-indigo-stroke`     |
| Context Assembly       | `--rag-blue-bg`      | `--rag-blue-stroke`       |
| Large Language Model   | `--rag-purple-bg`    | `--rag-purple-stroke`     |
| Grounded Response      | `--rag-green-bg`     | `--rag-green-stroke`      |

Source of truth: `docs/rag_system_architecture.drawio`, "RAG Design
Architecture" tab. If the drawio updates, mirror the changes here.
