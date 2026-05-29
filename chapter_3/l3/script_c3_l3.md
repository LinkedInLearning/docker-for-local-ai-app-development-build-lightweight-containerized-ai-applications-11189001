# Chapter 3 — Lesson 3: Dev Containers

In the last lesson, we brought our environment up with Docker Compose — but to run anything, we had to shell into the container. Our editor was still on the host, disconnected from where the code actually runs.

This lesson closes that gap with **Dev Containers**: a VS Code feature that attaches your editor *inside* the container. We'll cover the idea on slides, then open the project as a dev container and develop in it.

[CLICK]

A Dev Container moves the whole development experience into the container. VS Code keeps its familiar window on your host, but the **server side** of the editor — the language server, the terminal, the debugger, the extensions — all run inside the container.

The result is full isolation. The container has the exact Python version, the exact libraries, the exact system tools. Your laptop stays clean. And critically, the environment your editor sees is **identical** to the one that will run in test and production.

[CLICK]

Compare the two setups. Without a dev container, your editor runs against whatever is installed on your host, and you reach into the container with `docker exec`. The editor and the runtime are two different worlds.

With a dev container, there's one world. IntelliSense, "go to definition", the integrated terminal, notebook kernels, the debugger — all of it operates on the container's filesystem and interpreter. What you see is what runs.

[CLICK]

The configuration lives in one file: `.devcontainer/devcontainer.json`. A few features make it powerful.

First, it can build on what we already have. Instead of defining a new environment, our `devcontainer.json` points at the **same `docker-compose.yaml`** from the previous lesson and picks the `python` service:

```json
"dockerComposeFile": ["../docker-compose.yaml"],
"service": "python",
"workspaceFolder": "/workspace/"
```

A dev container can attach to a Compose service or to a plain image — either works.

[CLICK]

Second, **project-level extensions**. You list the VS Code extensions the project needs, and they're installed *inside the container*, scoped to this project:

```json
"customizations": {
  "vscode": {
    "extensions": [
      "ms-python.python",
      "charliermarsh.ruff",
      "ms-toolsai.jupyter"
    ]
  }
}
```

Every teammate who opens the project gets the same Python, Ruff, and Jupyter tooling — no "works on my setup" drift in the editor either.

[CLICK]

Third, **mounts and ports**. We can mount folders from *beyond* the project directory — a shared cache, a credentials file, shell history — so they're available inside the container without copying them into the image:

```json
"mounts": [
  "source=${localEnv:HOME}/.zsh_history_dev,target=/root/.zsh_history,type=bind"
],
"forwardPorts": [8501, 8080]
```

And `forwardPorts` auto-publishes the app's ports to your browser, so a Streamlit app on 8501 just opens on the host.

[CLICK]

Let's see it. I'll switch to VS Code and open the project as a dev container.

[SWITCH TO VS CODE]

This is our project. In the bottom-left corner there's a green remote indicator. I'll click it and choose **"Reopen in Container."**

[CLICK]

VS Code reads `.devcontainer/devcontainer.json`, starts the Compose services — our `python` container and `chromadb` alongside it — and reconnects the window to the running container. The first time it builds; after that it's quick.

Watch the remote indicator: it now reads **"Dev Container: RAG Docker Dev."** We are now *inside* the container.

[CLICK]

Two quick checks. Open the integrated terminal — this shell is running in the container, not on my Mac. If I check the Python interpreter:

```bash
which python
python --version
```

It points at `/opt/python-3.11-dev/bin/python` — the interpreter baked into our image, exactly the version we pinned.

[CLICK]

And the extensions panel shows our project extensions — Python, Ruff, Jupyter — all marked as installed in the container. The editor's intelligence is now backed by the container's environment.

From here, opening a file gives us full IntelliSense against the container's libraries, the database is reachable at `chromadb:8000`, and forwarded ports open in the browser.

[CLICK]

That's the payoff: our editor and our runtime are finally the same environment. We write code locally-feeling, but everything executes in the container.

Now that the environment is set and our editor is wired into it, we're ready to actually build the application. In the next lesson, we start developing the RAG code inside this container — with an AI assistant in the loop.
