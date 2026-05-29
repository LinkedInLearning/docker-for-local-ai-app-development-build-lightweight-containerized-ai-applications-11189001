# Course Naming & Structure Convention

> The single source of truth for how this course is organized: chapter map,
> folder layout, file names, and the title format used across READMEs,
> scripts, and slides. Follow this whenever you add or rename a lesson so the
> structure stays consistent.

---

## 1. The course at a glance

The course takes a RAG application from idea to production. Each chapter is
one stage of that journey. The **Title** column is the official chapter title
(updated 2026-05-28); the **Short form** is the concise label to use when one
chapter is cross-referenced from another (slide "where we are" stops, "what's
next" lines) where the full title is too long.

| Chapter | Folder      | Title (official) | Short form | Focus |
| ------- | ----------- | ---------------- | ---------- | ----- |
| —       | `chapter_0` | Course meta | — | Opening, closing, and conventions (no lessons). |
| 1       | `chapter_1` | Introduction to Docker for AI Applications | Intro to Docker for AI | Why containers matter, especially for AI apps. |
| 2       | `chapter_2` | Docker Workflow and Best Practices | Docker Workflow & Best Practices | End-to-end Docker workflow and best practices. |
| 3       | `chapter_3` | Building a Containerized AI Development Environment | Containerized Dev Environment | Build a dev environment to prototype the AI application. |
| 4       | `chapter_4` | Testing Multi-Container AI Applications with Docker | Testing Multi-Container Apps | Split the prototype into dedicated containers and test near-production. |
| 5       | `chapter_5` | Preparing AI Applications for Production with Docker | Preparing for Production | Optimize images, production readiness, and validation. |

`chapter_1`, `chapter_2`, and `chapter_3` are complete. `chapter_0` holds
course-level material. `chapter_4`–`chapter_5` are the remaining build-out.

> **Note.** Chapter titles do **not** appear in lesson H1s, `<title>` tags, or
> script headers — those carry only the chapter *number* and the *lesson*
> title (see §4). So renaming a chapter touches only the chapter_0 docs and the
> cross-chapter references catalogued in §6.

---

## 2. Folder layout

```
chapter_0/                     course-level material (no lessons)
  script_opening.md
  script_closing.md
  naming_convention.md         ← this file

chapter_{N}/                   one folder per chapter, N = 1..5
  l{M}/                        one folder per lesson, M = 1..k
    README.md                  lesson notes / reference
    script_c{N}_l{M}.md        narration / teleprompter script
    slides_c{N}_l{M}.html      slide deck
    <supporting files>         Dockerfile, *.py, *.sh, *.drawio, etc.
```

Rules:

- **Chapters** are `chapter_{N}`, zero-padded only if we ever exceed 9 (we won't).
- **Lessons** are `l{M}` — lowercase `l`, no padding (`l1`, `l2`, … `l10`).
- Lesson folders are numbered in teaching order. Do not reuse a number; if a
  lesson is removed, renumber the rest so the sequence has no gaps.

---

## 3. File naming

Every lesson folder has three core files. The chapter/lesson numbers are
**embedded in the file name** so a file is unambiguous even when opened
outside its folder.

| File          | Pattern                  | Example                |
| ------------- | ------------------------ | ---------------------- |
| Lesson notes  | `README.md`              | `README.md`            |
| Script        | `script_c{N}_l{M}.md`    | `script_c2_l3.md`      |
| Slides        | `slides_c{N}_l{M}.html`  | `slides_c2_l3.html`    |

Where `{N}` = chapter number, `{M}` = lesson number.

- Use `c{N}_l{M}` exactly — lowercase `c`/`l`, underscore separator.
- The numbers in the file name **must match the folder** it lives in. A file
  named `slides_c2_l1.html` inside `chapter_1/l1/` is a bug.
- Course-level scripts in `chapter_0` use a descriptive name instead of
  `c_l` numbering: `script_opening.md`, `script_closing.md`.
- **No bare `slides.html`.** Always include the `_c{N}_l{M}` suffix so files
  are greppable and never collide when copied.
- Supporting assets (Dockerfiles, `main.py`, `build.sh`, `.drawio`, …) keep
  their natural, tool-expected names — they are not renamed to the lesson scheme.

---

## 4. Title format

The same human-readable title appears in three places, in two formats. Keep
the wording identical across all three; only the punctuation differs.

**READMEs and scripts** — H1 with an em dash and a colon:

```
# Chapter {N} — Lesson {M}: {Title}
```

> `# Chapter 2 — Lesson 3: docker build`

**Slides** — `<title>` and the title slide use a middle dot then an em dash:

```
Chapter {N} · Lesson {M} — {Title}
```

> `Chapter 2 · Lesson 3 — docker build`

Title rules:

- **One canonical title per lesson.** The README, script, and slide title
  must use the same words. If they disagree today, the README is the source
  of truth — update the others to match.
- Use **Title Case** for the lesson title.
- Render Docker commands as plain text in titles (`docker build`, not
  `` `docker build` ``); backticks are fine in body copy.

---

## 5. Current chapter map (chapters 1–3)

The canonical lesson titles as they should appear everywhere:

**Chapter 1 — Introduction to Docker for AI Applications**

| Lesson | Title |
| ------ | ----- |
| 1 | Why Docker Containers? |
| 2 | Introduction to RAG |
| 3 | Container Strategy |
| 4 | Containerized Development Workflow for AI Applications |

**Chapter 2 — Docker Workflow and Best Practices**

| Lesson | Title |
| ------ | ----- |
| 1 | The Docker Workflow |
| 2 | Core Dockerfile Commands |
| 3 | docker build |
| 4 | docker run |
| 5 | Dockerfile Best Practices |
| 6 | Managing Containers and Images |

**Chapter 3 — Building a Containerized AI Development Environment**

| Lesson | Title |
| ------ | ----- |
| 1 | Designing Images for Change |
| 2 | Docker Compose |
| 3 | Dev Containers |
| 4 | Developing Inside the Container |
| 5 | Development Environment Best Practices |

---

## 6. Chapter rename — impact & required fixes (pending)

On 2026-05-28 the five chapter titles were updated (see §1). Because chapter
titles never appear in lesson H1s / `<title>` / script headers, **no lesson
file needs a title edit.** The only impact is on:

1. **chapter_0 docs — already updated:** this file (§1, §5) and
   `learning_goals.md` (chapter section headers).
2. **Cross-chapter references inside lessons** — short focus labels that name
   an adjacent chapter. These are listed below for the author to reconcile to
   the §1 **Short form** at leisure. They are cosmetic (the decks still work);
   fix them when polishing the affected deck.

The most common mismatch: the older decks label **Chapter 2 as "Docker 101"**
and **Chapter 3 as "Apply to RAG"** — informal names, not the chapter titles.
Line numbers below are exact as of 2026-05-29.

| File | Line(s) | Current text | → Short form |
| ---- | ------- | ------------ | ------------ |
| `chapter_1/l3/slides_c1_l3.html` | 295 | "Docker 101" ttl (Chapter 2 · next stop) | "Docker Workflow & Best Practices" |
| `chapter_1/l4/slides_c1_l4.html` | 258, 344, 517 | "Docker 101" for Chapter 2 (stop ttl, inline `<b>`, takeaway foot) | "Docker Workflow & Best Practices" |
| `chapter_1/l4/slides_c1_l4.html` | 380, 419, 454 | "prototype stage" / "testing stage" / "Deployment to production" — focus of Ch 3/4/5 | optional: Containerized Dev Environment / Testing Multi-Container Apps / Preparing for Production |
| `chapter_1/l4/slides_c1_l4.html` | 473, 480, 487, 494 | `chbadge` "Chapter 2/3/4/5" (bare numbers) | no change — numbers only, no title |
| `chapter_1/l4/README.md` | 100, 127, 133 | "focus of Chapter 3/4/5" prose | optional: append short-form titles |
| `chapter_1/l4/script_c1_l4.md` | 54, 72, 90 | "chapter 3/4/5" stage prose | optional: append short-form titles |
| `chapter_2/l1/slides_c2_l1.html` | 280, 288, 296 | ttls "Why containers" / "Docker 101" / "Apply to RAG" (Ch 1 done · Ch 2 here · Ch 3 next) | "Intro to Docker for AI" / "Docker Workflow & Best Practices" / "Containerized Dev Environment" |
| `chapter_2/l6/slides_c2_l6.html` | 296 | "Apply to RAG" ttl (Chapter 3 · next stop) | "Containerized Dev Environment" |
| `chapter_3/l1/slides_c3_l1.html` | 223 | "Docker workflow & best practices" ttl (Chapter 2 · done) | already aligned — at most Title-case to "Docker Workflow & Best Practices" |
| `chapter_3/l5/slides_c3_l5.html` | 251, 450 | "Testing" ttl + "Chapter 4 · Testing" foot | "Testing Multi-Container Apps" |

> Everything else the impact search surfaced (e.g. "run in production",
> "testing stage", "prototype") is ordinary prose, not a chapter reference, and
> needs no change.

---

## 7. Deviation log

The deviations below were found in the initial audit and have since been
**resolved** (2026-05-28). Kept here as a record; the tree now follows §3–§4.

| File | Problem | Resolution |
| ---- | ------- | ---------- |
| `chapter_1/l1/slides_c2_l1.html` | labeled `c2` but lives in chapter 1 | renamed → `slides_c1_l1.html` |
| `chapter_2/l3/slides.html` | missing `c{N}_l{M}` suffix | renamed → `slides_c2_l3.html` |
| `chapter_2/l4/slides.html` + `slides_prototype.html` | two slide files, no suffix | kept canonical deck → `slides_c2_l4.html`; dropped `slides_prototype.html` |
| `chapter_2/l5/slides.html` | missing suffix | renamed → `slides_c2_l5.html` |
| `chapter_2/l6/slides.html` | missing suffix | renamed → `slides_c2_l6.html` |
| Chapter 2, Lesson 2 title | README/script/slide disagreed | unified to **Core Dockerfile Commands** across all three |

---

## 8. Checklist for adding a lesson

1. Create `chapter_{N}/l{M}/`.
2. Add `README.md`, `script_c{N}_l{M}.md`, `slides_c{N}_l{M}.html`.
3. Use one canonical Title Case title in all three (see §4 formats).
4. Verify the `c{N}_l{M}` in every file name matches the folder.
5. Keep supporting assets under their natural names.
6. If this changes the lesson order, renumber so the sequence has no gaps.
