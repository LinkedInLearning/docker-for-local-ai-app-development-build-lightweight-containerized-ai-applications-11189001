# Slide patterns

Each pattern below is a reusable slide skeleton. Drop the HTML into the
deck, and copy the matching CSS block from the lesson where it was first
introduced.

> Convention: every pattern lives inside `<section class="slide"> <div class="wrap"> … </div> </section>`.
> Outer chrome is omitted from the snippets here.

---

## Title slide

```html
<section class="slide active" style="position:relative;overflow:hidden;">
  <svg class="title-art" viewBox="0 0 720 720" aria-hidden="true">
    <!-- decorative SVG, faded to ~55% opacity -->
  </svg>
  <div class="wrap title-wrap">
    <p class="eyebrow">Chapter N · Lesson M</p>
    <h1 class="title">Plain words <span class="accent">accent</span></h1>
    <h3 class="sub">One-sentence positioning statement.</h3>
    <p style="margin-top:32px;color:var(--muted);font-size:14px;letter-spacing:.04em;">
      Docker for Local AI · Building AI Applications with Containers
    </p>
  </div>
</section>
```

---

## "Where we are" slide (3-stop path)

```html
<section class="slide">
  <div class="wrap">
    <p class="eyebrow">Where we are</p>
    <h2 class="h">Short positioning headline.</h2>
    <p class="lead">One paragraph explaining the transition.</p>

    <div class="path">
      <div class="stop">
        <div class="lbl">Lesson N-1 · done</div>
        <div class="ttl">Previous topic</div>
        <div class="desc">One-line recap.</div>
      </div>
      <div class="connector"><svg viewBox="0 0 24 24" fill="none">
        <path d="M5 12h14M13 6l6 6-6 6" stroke="currentColor" stroke-width="1.8"
              stroke-linecap="round" stroke-linejoin="round"/></svg></div>
      <div class="stop now">
        <div class="lbl">Lesson N · here</div>
        <div class="ttl">Current topic</div>
        <div class="desc">One-line preview.</div>
      </div>
      <div class="connector"><!-- same arrow --></div>
      <div class="stop">
        <div class="lbl">Lesson N+1 · next</div>
        <div class="ttl">Next topic</div>
        <div class="desc">One-line tease.</div>
      </div>
    </div>
  </div>
</section>
```

---

## Four-step / overview row

```html
<div class="fourstep">
  <div class="stepcard">
    <div class="badge">1</div>
    <span class="kind">Verb</span>
    <svg class="icon" viewBox="0 0 48 48" fill="none">…</svg>
    <h4>Step name</h4>
    <p class="what">One-line description.</p>
  </div>
  <!-- repeat for 2, 3, 4 -->
</div>
```

CSS lives in C2 L1's deck.

---

## Detail slide (sidebar + visualization)

```html
<div class="detail">
  <div class="step-side">
    <div class="step-num">N</div>
    <h2>Headline of this step.</h2>
    <p>A short paragraph.</p>
    <div class="quote">"Memorable one-liner."</div>
  </div>
  <div class="step-vis">
    <div class="cap">Caption</div>
    <!-- the focus visual: code block, infographic, etc. -->
  </div>
</div>
```

C2 L2 uses a similar `idetail` layout — same idea, different proportions.

---

## Annotated Dockerfile

```html
<div class="dfile">
  <div class="ln">
    <span class="gut">1</span>
    <span class="kw">FROM</span> python:3.11-slim
    <span class="tag">Base image</span>
  </div>
  <!-- one .ln per line, optional .tag annotation on the right -->
</div>
```

Use `.kw` for keywords, `.str` for strings, `.cmt` for comments.

---

## Before / after columns

```html
<div class="ba">
  <div class="col bad">
    <div class="lbl">✗ Bad</div>
    <pre class="code">...</pre>
    <div class="note">Why it's bad.</div>
    <div class="metric">measurable downside</div>
  </div>
  <div class="col good">
    <div class="lbl">✓ Good</div>
    <pre class="code">...</pre>
    <div class="note">Why it's better.</div>
    <div class="metric">measurable upside</div>
  </div>
</div>
```

C2 L5's main pattern. Use for anti-pattern vs. best practice.

---

## Practice header (numbered)

```html
<div class="ph">
  <div class="pnum">N</div>
  <div class="ptxt">
    <div class="ptag">Best practice · N of M</div>
    <h2>Practice headline.</h2>
  </div>
</div>
<p class="pwhy">One-paragraph rationale.</p>
```

C2 L5 uses this on every practice slide.

---

## Object grid (taxonomy)

```html
<div class="objgrid">
  <div class="objcard images focus">
    <div class="focuspill">focus</div>
    <div class="ic"><svg>…</svg></div>
    <h4>Item name</h4>
    <p class="what">One-line description.</p>
    <div class="verbs">verb a<br>verb b<br>verb c</div>
  </div>
  <!-- 3 more -->
</div>
```

C2 L6's main pattern. Add `.focus` to the cards the lesson actually covers.

---

## Terminal mock

```html
<div class="term">
  <div><span class="prompt">$</span> <span class="cmd">docker</span> ps</div>
  <div class="hd">CONTAINER ID   IMAGE   STATUS   NAMES</div>
  <div class="out">3b9f1c…   demo:0.1   <span class="ok">Up 12 minutes</span>   demo</div>
  <hr/>
  <div><span class="prompt">$</span> <span class="cmd">docker</span> images</div>
  <!-- … -->
</div>
```

Keep output realistic but minimal — invented IDs and timestamps are fine.

---

## State machine (lifecycle)

C2 L6 has a hand-drawn SVG with 4 boxes (created → running → stopped → removed)
and dashed arrows. For a different state machine, reuse the SVG layout and
update box labels and transitions. Keep box width 120px, height 56px,
radius 12px.

---

## Severity cascade (safe → nuclear)

```html
<div class="prune">
  <div class="prunecard safe"><div class="pl">✓ Safe</div>...</div>
  <div class="prunecard med"><div class="pl">! Aggressive</div>...</div>
  <div class="prunecard danger"><div class="pl">⚠ Nuclear</div>...</div>
</div>
```

C2 L6's prune cascade. Use for any progression of options ranked by risk.

---

## Cheat sheet table

```html
<div class="cheat">
  <div class="ch head"><span>Question</span><span>Command</span></div>
  <div class="ch"><span>What containers are running?</span><code>docker ps</code></div>
  <!-- … -->
</div>
```

Two-column. Left = question / human intent, right = command. C2 L6.

---

## Loop diagram (4-node circular)

C2 L1's `loop-vis` — 4 nodes positioned at top/right/bottom/left with curved
SVG arrows in a clockwise loop. Use for cyclic processes.

---

## Big quote slide

```html
<div class="bigquote">
  <span class="qmark">"</span>
  <p class="qtext">Quoted line with <em>highlighted</em> words.</p>
  <div class="qfoot">— attribution</div>
</div>
```

C1 L1's "It works on my machine" pattern. Use for memorable one-liners
that deserve a whole slide. The `.qmark` is a giant decorative
opening-quote in a faded blue. The `.em` inside `.qtext` gets the
blue → teal gradient text treatment.

---

## Machine triad (status-stamped cards)

```html
<div class="triad">
  <div class="machine ok">
    <span class="stamp">✓</span>
    <div class="icon"><svg>...</svg></div>
    <div class="role"><span class="pulse"></span>Developer</div>
    <div class="who">macOS · M2</div>
    <div class="specs"><div>python: <span>3.12.11</span></div>...</div>
  </div>
  <div class="machine bad">…</div>
  <div class="machine bad">…</div>
</div>
```

C1 L1's "it works on my machine" panel — three machine cards with
green check or red X stamps showing the same code with different
specs. Reuse for any "works here / fails there" comparison.

---

## High-level "AI in the middle" diagram

C1 L2's `.hl` panel — three columns (User → AI → Output), with an
"External Inputs" sub-panel underneath connected by a vertical
double-arrow. Use for any system where one component sits in the
middle and external state flows in from below.

---

## RAG pipeline diagram (CSS replica of the drawio)

```html
<div class="rag-diagram">
  <div class="pl-label ingest">INGESTION PIPELINE · offline / batch</div>
  <div class="pipeline">
    <div class="rag-node docs"><b>Document Sources</b><div class="docs-list">…</div></div>
    <div class="rag-node green"><b>Document Parsing</b><div class="small">…</div></div>
    <div class="rag-node green"><b>Chunking / Splitting</b><div class="small">…</div></div>
    <div class="rag-node purple"><b>Embedding Model</b><div class="small">…</div></div>
    <div class="rag-node cyl"><b>Vector Store</b><div class="small">…</div></div>
  </div>
  <div class="rag-divider"><span>knowledge base ready · same store below</span></div>
  <div class="pl-label query">QUERY PIPELINE · online / real-time</div>
  <div class="pipeline">…</div>
</div>
```

C1 L2's reproduction of the drawio "RAG Design Architecture" diagram.
Use the `--rag-*` color tokens (yellow docs, green pipeline, purple
embedding, cyl vector store, indigo retrieval, blue context) so it
matches the source diagram. Wrap with `.rag-highlight` (pink border) to
focus attention on a single pipeline.

---

## Two-input formula (A + B = C)

C1 L3's `.twoinputs` block — two cards joined by a `+` and an `=` ending
with a gradient result card. Use whenever the slide makes a simple
"these two inputs determine that outcome" point.

---

## Service taxonomy (named cards with colored borders)

C1 L3's `.services` row — three cards, each with its own brand color
(green ingestion, dark-green vector store, blue query). Pulled directly
from the RAG diagram palette so the same colors mean the same services
across decks.

---

## Dev → Test → Deploy stages

C1 L3's `.stages` panel — three large cards with `📦` package icons
listing what containers exist at each stage. Use for any progression
that adds, splits, or relocates artifacts as a project matures.

---

## Three-step principle

C1 L3's `.principle` row — three numbered steps separated by arrows,
each on its own card. Use for "do this, then this, then this" rules
where the order itself is the point.

---

## Takeaway slide

```html
<section class="slide">
  <div class="wrap" style="text-align:center;">
    <p class="eyebrow">Takeaway</p>
    <h2 class="h" style="margin-bottom:6px;">Headline</h2>
    <h3 class="sub" style="margin:0 auto 18px;">Subheadline.</h3>
    <div class="takeaway-card">
      <div class="quote">
        <code class="inline" style="font-size:.85em">step1</code> ·
        <code class="inline" style="font-size:.85em">step2</code> ·
        <code class="inline" style="font-size:.85em">step3</code>
      </div>
      <div class="foot">Next lesson → topic.</div>
    </div>
  </div>
</section>
```

For the last lesson of a chapter, change the eyebrow to
`Takeaway · end of Chapter N` and have the foot point to the next chapter.
