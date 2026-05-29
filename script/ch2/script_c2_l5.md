# Chapter 2 — Lesson 5: `docker run`

In the previous lesson, we built an image using `docker build`. Now we will use that image to launch an actual container.

A container is a running instance of an image. We can launch many containers from the same image, just like we can launch many processes from a single executable.

[CLICK]

The basic command is:

```bash
docker run my-image:0.1
```

Docker takes the image, creates a writable layer on top of it, and starts the process defined by the `CMD` or `ENTRYPOINT` instruction.

That is the minimum, but in practice we almost always pass a few flags. Let's go through the most useful ones.

[CLICK]

`-d` for **detached mode**.

By default, `docker run` attaches our terminal to the container. The container stops when we close the terminal. Adding `-d` runs it in the background and returns control to the shell.

We use this when running long-lived services such as APIs or databases.

[CLICK]

`-p` for **port publishing**.

Inside the container, the application may listen on port 8080. That port is not reachable from the host until we publish it.

```bash
docker run -p 8080:8080 my-image:0.1
```

The first number is the port on the host. The second is the port inside the container. They do not have to match.

`EXPOSE` in the Dockerfile is documentation. `-p` is what actually opens the port.

[CLICK]

`-v` for **volumes**.

Containers are ephemeral by default. When the container is removed, anything written inside it disappears.

Volumes solve this. We can mount a host directory or a named volume into the container, and files persist across container restarts.

```bash
docker run -v $(pwd)/data:/data my-image:0.1
```

This is also how we mount source code into a development container, so changes on our laptop appear instantly inside the container.

[CLICK]

`-e` for **environment variables**.

Most applications need configuration such as API keys or database URLs. We pass them at run time with `-e`:

```bash
docker run -e OPENAI_API_KEY=$OPENAI_API_KEY my-image:0.1
```

This keeps secrets out of the image.

[CLICK]

`--name` for a **friendly container name**.

By default, Docker assigns a random name like `amazing_einstein`. We can give the container a name we will recognize:

```bash
docker run --name rag-api my-image:0.1
```

This makes it easier to run `docker logs rag-api` or `docker stop rag-api` later.

[CLICK]

`--rm` to **clean up automatically**.

When the container exits, it is not deleted by default. It stays around in the stopped state. `--rm` tells Docker to remove the container as soon as it stops — very useful for one-off commands.

[CLICK]

`-it` for an **interactive session**.

These two flags combined give us an interactive terminal inside the container. We use this to drop into a shell and explore:

```bash
docker run -it --rm my-image:0.1 bash
```

[CLICK]

Putting it together, a realistic run command looks like this:

```bash
docker run -d --name rag-api \
  -p 8080:8080 \
  -v $(pwd)/data:/data \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  rag-api:0.1
```

Detached, named, with a published port, a mounted volume, and a passed environment variable.

[CLICK]

---

> **🎬 LIVE DEMO — pivot to the VS Code terminal.**
> Switch to VS Code and open the integrated terminal. We'll run the `demo:0.1`
> image we built back in Lesson 3 as a detached container, publish its port,
> and open the FastAPI app in the browser. Have a browser window ready.

Let's bring an image to life. This is the same `demo:0.1` image we built in Lesson 3 — a small **FastAPI** application listening on port 8080 inside the container.

We'll start it detached, give it a name, and publish the port so the host can reach it:

```bash
docker run -d --name rag-api -p 8080:8080 demo:0.1
```

Docker prints the container ID and immediately returns our prompt — that's the `-d` flag, the container is now running in the background. Let's confirm:

```bash
docker ps
```

There it is — one running container named `rag-api`, with the port mapping `0.0.0.0:8080->8080/tcp`. The host's port 8080 is now wired to the app inside the container.

Now the payoff — let's open it in the browser.

> **[SWITCH TO BROWSER]** Open `http://localhost:8080`.

There's the JSON response coming straight from the FastAPI app running *inside the container*. The process never touched our host Python — it's entirely contained, and we reached it only because we published the port with `-p`.

And because this is FastAPI, we get interactive API docs for free:

> **[SWITCH TO BROWSER]** Open `http://localhost:8080/docs`.

This is the auto-generated Swagger UI — every endpoint, its parameters, and a *Try it out* button, all served by the container.

[CLICK]

Now, why does this matter for **AI applications**?

This is *exactly* the shape of a real local AI service. Almost every AI application we build in this course is a Python service wrapped in a FastAPI app — and we ship and run it as a container the same way we just did.

Take a **RAG data-ingestion** service as the concrete example. It's a FastAPI app that exposes an endpoint like `POST /ingest`: you send it documents, it chunks them, generates embeddings, and writes them into a vector database. Running it looks like this:

```bash
docker run -d --name rag-ingest \
  -p 8080:8080 \
  -v $(pwd)/data:/data \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  rag-ingest:0.1
```

Same `docker run`, same flags — only the image and the configuration change. `-p` publishes the API so we can call `/ingest` and browse `/docs`. `-v` mounts the folder of documents we want to ingest. `-e` injects the API key the embedding model needs, without baking it into the image.

That's the whole pattern: build the FastAPI image once, then `docker run` it — published, mounted, and configured — wherever the work needs to happen. The `demo:0.1` container we just opened in the browser is the smallest possible version of that exact idea.

Before we move on, let's clean up the demo container:

```bash
docker rm -f rag-api
```

Back to the slides.

---

[CLICK]

Once the container is running, a few commands help us manage it:

* `docker ps` shows running containers.
* `docker logs` prints the container output.
* `docker exec` lets us run another command inside a running container.
* `docker stop` and `docker rm` stop and remove the container.

These flags and commands cover the vast majority of day-to-day Docker usage.

In the next lesson, we will look at managing containers and images — how to list, inspect, debug, and clean up the objects Docker creates as we work.
