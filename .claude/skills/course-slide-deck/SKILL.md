---
name: course-slide-deck
description: Build HTML slide decks for the "Docker for Local AI" course (and similar courses). Presentation-scale typography, viewport-locked slides with cross-fade transitions, top-anchored content, and a clean unadorned canvas (only a slim progress bar). Use whenever creating a new lesson's slides.html.
---

# Course slide-deck skill

Reference and templates for building consistent HTML slide decks across course
lessons. Every lesson under `chapter_*/l*/` ships a `slides.html` that follows
the same visual language. This skill captures that language.

When creating a new lesson deck, **read** the relevant pieces below — don't
copy-paste blindly. Keep the typography, layout, and nav script identical;
vary the per-slide infographics to match the lesson's content.

> **Format note.** This skill describes the *current* "presentation" format
> used for new decks. The first decks built (chapter_1, chapter_2 lessons 1-3,
> 5-6) are in an earlier "compact" format with on-screen chrome (brand strip,
> page counter, nav-hint) and smaller body text. New decks should follow the
> presentation format below. The canonical boilerplate is
> `templates/base-deck.html`; for full real-world examples in this format see
> `chapter_2/l4/slides_c2_l4.html` and the chapter_3 decks
> (`chapter_3/l*/slides_c3_l*.html`).

---

## When to use

Trigger this skill any time the user asks for:

- a new lesson `slides.html`
- a slide deck for a chapter
- HTML slides matching the course format
- a deck that "looks like the chapter_3 decks" or "the latest deck format"

Don't use this skill for:

- the lesson script (`script_cN_lM.md`) — that's a separate written artifact
- the lesson README — that's prose explanation, not a deck
- non-course slide decks (use a presentation tool like keykit instead)

---

## Authoring workflow

1. **Read the lesson script** (`script_cN_lM.md`). Each `[CLICK]` marker is
   roughly one slide boundary. Plan ~8–12 slides per lesson.
2. **Pick the slide types** for the lesson. Every deck has:
   - 1 × title slide
   - 1 × "where we are" slide with a 3-stop path
   - several content slides (varies)
   - 1 × takeaway slide
3. **Start from the boilerplate** in `templates/base-deck.html` and add
   per-slide CSS only for visualizations the boilerplate doesn't already cover.
4. **Test in a browser** — open the file directly. Verify keyboard nav
   (`←`/`→`/`space`) and the progress bar.
5. **Check the tallest slide fits the viewport.** Slides are hard-capped at
   `100vh` with `overflow: hidden`; anything that doesn't fit gets clipped.
   Tighten paddings or trim content rather than letting it scroll.

---

## Visual system

The full design tokens are in `references/style-tokens.md`. Key rules:

- **Unadorned canvas.** The only chrome on screen is a slim progress bar at
  the very top. No brand strip, no page counter, no keyboard hints — slide
  content owns the canvas.
- **Eyebrow** above each h2 — uppercase, `--blue-700` (7.4:1 contrast),
  letter-spacing 0.18em. Tells the reader where they are in the lesson.
- **Title slide** uses an abstract SVG `title-art` decoration on the right —
  layered rectangles, circles, or grids in low-opacity blue/teal/green
  gradients. Pick a motif that matches the lesson topic (layers for
  Dockerfiles, grid for managing containers, arrows for workflows, etc.).
- **Takeaway slide** ends with a `takeaway-card` containing a one-liner
  quote and a `foot` line that points to the next lesson.
- **Maximum content width** is `--maxw: 1280px` — never let prose stretch
  wider.
- **Top-anchored content.** Every slide pins its `.wrap` at the top
  (`align-items: flex-start; margin: 0 auto`) so the eyebrow and title sit at
  the same Y coordinate across all slides — they don't move during navigation.
- **Viewport-locked, no scroll.** Each slide is `height: 100vh; overflow: hidden`.
  The bottom area on shorter slides is allowed to be empty; the *tallest*
  slide implicitly sets the floor for what fits.
- **Cross-fade transitions.** All slides are `position: absolute; inset: 0`
  and stacked. Toggling the `.active` class triggers an opacity cross-fade
  (`.55s cubic-bezier(.4,0,.2,1)`) — both outgoing and incoming slides are
  visible during the transition. No `display: none` flip, no spatial motion.

---

## Standard slide types

### 1. Title slide

- `<p class="eyebrow">Chapter N · Lesson M</p>`
- `<h1 class="title">Plain text <span class="accent">accent words</span></h1>`
- `<h3 class="sub">Single-sentence positioning statement.</h3>`
- Footer line: `Docker for Local AI · Building AI Applications with Containers`
- Decorative SVG via `class="title-art"`, absolutely positioned right.

### 2. "Where we are" slide

3-stop horizontal path:

- `Lesson N-1 · done` — what we just covered
- `Lesson N · here` (now) — current lesson, blue gradient background
- `Lesson N+1 · next` — what comes next

For the last lesson of a chapter, use `Chapter N+1 · next` instead of
the next lesson.

### 3. Content slides

Mix and match these patterns based on what the lesson teaches:

| Pattern | Use for |
|---------|---------|
| `fourstep` cards (C2 L1) | Sequential phases (4 of them) |
| `detail` (sidebar + vis) (C2 L1, C2 L2, C2 L4) | Step-by-step explanation with one focus visual |
| `instr-grid` chips (C2 L2) | Multi-item overview ("the 7 things we'll cover") |
| `phases` vertical list (C2 L2) | Anatomy / structural breakdown |
| `path` / 3-stop (everywhere) | Where-we-are or any 3-step sequence |
| Annotated `cmdline` + `annos` (C2 L3) | Command-line anatomy with token callouts |
| `term` (terminal mock) (C2 L3, C2 L4, C2 L6) | Sample shell output |
| Before/after `ba` columns (C2 L5) | Anti-pattern vs. best practice |
| `objgrid` (C2 L6) | Categorical taxonomy of N items |
| `lc` state machine (C2 L6) | Lifecycle / state transitions |
| `prune` / cascade (C2 L6) | Severity-ranked options |
| `bigquote` (C1 L1) | Memorable one-liner that owns the slide |
| `triad` machine cards (C1 L1) | Same code, different machines comparison |
| `hl` AI-in-the-middle (C1 L2) | System with central component + external state |
| `rag-diagram` pipeline (C1 L2) | Reproduction of the drawio RAG architecture |
| `twoinputs` A + B = C (C1 L3) | "Two factors determine the outcome" framing |
| `services` named cards (C1 L3) | Service taxonomy with brand colors per service |
| `stages` dev/test/deploy (C1 L3) | Progression that adds or splits artifacts |
| `principle` numbered steps (C1 L3) | "Do this, then this, then this" rules |

### 4. Takeaway slide

- `<p class="eyebrow">Takeaway</p>` (or `Takeaway · end of Chapter N` for the last lesson)
- One short H2 + one short H3 sub
- `takeaway-card` with the one-liner summary in `.quote`
- `.foot` line pointing to the next lesson or chapter

---

## CSS conventions

- All decks use the **same `:root` token set**. Don't invent new colors —
  pick from the palette in `references/style-tokens.md`.
- **Inline styles are OK** for small per-slide tweaks (`style="margin-top:..."`
  to add or remove vertical rhythm). Don't reinvent layout primitives.
- **Per-slide CSS classes** (e.g. `.fourstep`, `.objgrid`, `.prune`) live in
  the deck's `<style>` block. Keep them grouped under a comment header
  matching the section they decorate.
- **Slides are absolutely positioned** (`position: absolute; inset: 0`) inside
  a relative `.deck`. Don't change this — the cross-fade depends on it.
- **Top-anchor everything.** Use `align-items: flex-start` on `.slide.active`
  and `margin: 0 auto` on `.wrap` so the eyebrow always lands at the same Y.
- Always include the `@media (max-width:1100px)` block. The deck targets
  desktop presentation; the smaller-viewport fallback shrinks type proportionally.

---

## Tone & copy

- **H1/H2 lines are short and declarative.** "It's a loop, not a line."
  "One RUN, not five." "From building to operating."
- **Use the second person sparingly.** The deck is a quiet voice next to
  the script — let the script do the storytelling.
- **Code in slides is for shape, not depth.** 3–8 lines per `pre.code` block.
  Long examples belong in the README.
- **Accent words go in the H1's `.accent` span.** Pick the noun the lesson
  is named after (Workflow, Dockerfile, Build, Run, Practices, Images).
- **Eyebrow text** matches the slide's role: "Where we are", "Definition",
  "Anatomy", "Step 1 of 4", "Takeaway", etc.

---

## Files in this skill

- `templates/base-deck.html` — minimal lesson deck (3 slides: title, where-we-are,
  takeaway) with all styling and the navigation script wired up. Drop new
  content slides into it.
- `references/style-tokens.md` — full color and typography reference.
- `references/slide-patterns.md` — each pattern's HTML skeleton with notes.

---

## Anti-patterns to avoid

- Don't introduce new fonts. Inter / ui-monospace only.
- Don't use emojis in the deck unless the user asks. Use SVG icons.
- Don't add reveal-on-click animations. The cross-fade handles transitions;
  any extra motion competes with it.
- Don't use `display: none` on slides — it breaks the cross-fade. Slides are
  always rendered and toggled via opacity.
- Don't add spatial transforms (`translateY`, slide-in/out) on top of the
  fade. Pure opacity is the agreed-upon transition.
- Don't reintroduce the brand strip, page counter, or keyboard hint — they
  were intentionally removed. The progress bar is the only on-screen chrome.
- Don't let any slide overflow `100vh`. Trim content or split into two slides.
- Don't hard-code chapter or lesson numbers in JS — the script reads from
  the DOM.
