# Docker for Local AI App Development: Build Lightweight, Containerized AI Applications
This is the repository for the LinkedIn Learning course `Docker for Local AI App Development: Build Lightweight, Containerized AI Applications`. The full course is available from [LinkedIn Learning][lil-course-url].

![lil-thumbnail-url]

## Course Description

_See the readme file in the main branch for updated instructions and information._
## Instructions
This repository has branches for each of the videos in the course. You can use the branch pop up menu in github to switch to a specific branch and take a look at the course at that stage, or you can add `/tree/BRANCH_NAME` to the URL to go to the branch you want to access.

## Branches
The branches are structured to correspond to the videos in the course. The naming convention is `CHAPTER#_MOVIE#`. As an example, the branch named `02_03` corresponds to the second chapter and the third video in that chapter. 
Some branches will have a beginning and an end state. These are marked with the letters `b` for "beginning" and `e` for "end". The `b` branch contains the code as it is at the beginning of the movie. The `e` branch contains the code as it is at the end of the movie. The `main` branch holds the final state of the code when in the course.

When switching from one exercise files branch to the next after making changes to the files, you may get a message like this:

    error: Your local changes to the following files would be overwritten by checkout:        [files]
    Please commit your changes or stash them before you switch branches.
    Aborting

To resolve this issue:
	
    Add changes to git using this command: git add .
	Commit changes using this command: git commit -m "some message"

## Installing
1. To use these exercise files, you must have the following installed:
	- [list of requirements for course]
2. Clone this repository into your local machine using the terminal (Mac), CMD (Windows), or a GUI tool like SourceTree.
3. [Course-specific instructions]

## Instructor

Instructor name

Instructor description

                            

Check out my other courses on [LinkedIn Learning](https://www.linkedin.com/learning/instructors/).

---

## Running the API

The FastAPI service (v1) runs via uvicorn **inside the existing `python` dev
container** — there is no separate `api` compose service in v1. The future
container lift is documented in `pm/v0_1_0/development_plan.md` §12.

### Environment setup

Copy `.env.example` to `.env` and set your API key:

```bash
cp .env.example .env
# Edit .env and set RAG_API_KEYS
```

Minimum required:

```dotenv
OPENAI_API_KEY=sk-...
RAG_API_KEYS=your-secret-api-key
```

Or disable auth for local dev:

```dotenv
RAG_API_REQUIRE_AUTH=false
```

### Start the API

Inside the dev container terminal:

```bash
export RAG_API_KEYS=your-key
uvicorn rag.api.main:app --host 0.0.0.0 --port 8080
```

VS Code forwards port 8080 automatically (see `devcontainer.json`
`forwardPorts`).

### Ingest PDFs and poll for completion

```bash
# Submit (returns 202 + job_id immediately)
curl -s -X POST http://localhost:8080/ingest \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{"source_dir": "pdf/"}'
# Response: {"job_id":"j_...","request_id":"...","status":"pending","poll_url":"/ingest/jobs/j_..."}

# Poll for terminal state (completed / failed)
curl -s -H "X-API-Key: your-key" \
  http://localhost:8080/ingest/jobs/j_...
```

### Query the indexed documents

```bash
curl -s -X POST http://localhost:8080/query \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{"question": "What was revenue?"}'
```

### API health check (unauthenticated)

```bash
curl -s http://localhost:8080/health
```

### Limitations (v1)

- Jobs are in-memory; they are lost on API process restart. Poll results
  include the hint `"jobs are not persisted across API process restarts in v1"`.
- Rate limits and the job registry are per-process. Run a single uvicorn
  worker (the default). Multi-worker deployments would each have independent
  in-memory state.
- If running behind a reverse proxy, ensure `X-Forwarded-For` is forwarded
  correctly so per-IP rate limiting works as expected. Tier 2 will add proper
  proxy trust configuration.


[0]: # (Replace these placeholder URLs with actual course URLs)

[lil-course-url]: https://www.linkedin.com/learning/
[lil-thumbnail-url]: https://media.licdn.com/dms/image/v2/D4E0DAQG0eDHsyOSqTA/learning-public-crop_675_1200/B4EZVdqqdwHUAY-/0/1741033220778?e=2147483647&v=beta&t=FxUDo6FA8W8CiFROwqfZKL_mzQhYx9loYLfjN-LNjgA

