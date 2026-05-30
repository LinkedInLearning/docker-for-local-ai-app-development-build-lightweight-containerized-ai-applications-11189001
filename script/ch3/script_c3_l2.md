# Chapter 3 — Lesson 2: Docker Compose

In the previous lesson, we discussed how to design a containerized Python development environment. However, our RAG application consists of multiple services, including a Python application and a vector database.

In this lesson, we'll learn how to use Docker Compose to define, launch, and manage multiple containers as a single application.

We'll start with the core concepts on the slides, then switch to the terminal and bring the environment up in practice.


[CLICK]

So far, every container we started took its own `docker run` command with its own flags — ports, volumes, environment variables, and networks. That's fine for one container. However, it falls apart the moment you have two or three that need to start together, talk to each other, and share configuration.

Docker Compose solves that. You describe the whole environment **declaratively** in a single `docker-compose.yaml` file, and bring it all up with one command.

[CLICK]

A Compose file describes a set of **services**. Each service is a container — its image, its ports, its volumes, its environment, and the network it joins.

```yaml
services:
  python:
    image: rkrispin/python-dev-rag-docker:0.0.3
    ...
  chromadb:
    image: chromadb/chroma:1.3.5
    ...
```

The shape of the file mirrors `docker run`: everything you used to pass as a flag now has a line in the file. The difference is it's version-controlled, reviewable, and reproducible — anyone on the team gets the exact same environment.

[CLICK]

For our RAG prototype, we need **two** services.

The first is `python` — our development container, built from the dev image we've been designing. This is where we write and run code.

The second is `chromadb` — the vector database. And here's a point worth pausing on: we don't build ChromaDB ourselves. We used a community built in image,similar to the official Python images.

We just pin a version and run it.

[CLICK]

This is a common and important pattern. Infrastructure components such as databases, observability and other manged services usually have **off-the-shelf images** maintained by their authors. You don't Dockerize Postgres or ChromaDB; you pull a known-good version.

Your own application code goes in images **you** build. And uses a built-in image when applicable. Compose is what stitches the two kinds together into one environment.

[CLICK]

The last piece is how the two containers talk. In the Compose file we put both services on a shared **network**.

```yaml
networks:
  rag-docker:
    driver: bridge
```

Compose creates a network for the application and manage the connects of all the services.

On that network, each service can be reached by its service name. For example, our Python application connects to the vector database using the hostname chromadb on port 8000. We don't need to manage IP addresses because Compose handles the networking and DNS configuration for us.

The depends_on Settings let us define the startup order between services. In our case, it ensures the Python application starts after the chromadb service.

[CLICK]

That's the theory. We have two services, a shared network, and service-name networking, all declared in one file. Let's switch to the terminal and run it.

[SWITCH TO TERMINAL]

I'm in the `chapter_3/l2` folder, where there's a minimal `docker-compose.yaml` with exactly those two services.

First, bring the whole environment up in the background:

```bash
docker compose up -d
```

Compose reads the file, pulls any images it doesn't have, creates the network, and starts both containers. The `-d` flag — detached — returns the prompt instead of streaming logs.

[CLICK]

Now let's confirm both containers are alive:

```bash
docker compose ps
```

We should see two services, `python` and `chromadb`, both with a state of `running` (or `Up`). The `chromadb` row shows port `8000` mapped to the host.

[CLICK]

Let's check the database is actually responding. ChromaDB exposes a heartbeat endpoint, and because we published port 8000, we can hit it from the host:

```bash
curl http://localhost:8000/api/v2/heartbeat
```

A JSON response with a nanosecond timestamp means the database is up and serving.

[CLICK]

We can also look at what a service is doing:

```bash
docker compose logs chromadb
```

And to prove the networking works, let's open a shell **inside** the python container and reach the database by its service name:

```bash
docker compose exec python bash
curl http://chromadb:8000/api/v2/heartbeat
```

Notice the hostname is `chromadb`, not `localhost` — from inside the network, the service name is the address.

[CLICK]

When we're done, one command tears the whole thing down:

```bash
docker compose down
```

That stops and removes both containers and the network — but, because our data lives in a mounted volume, the ingested vectors survive for next time.

[CLICK]

That's Docker Compose: one file describing the whole environment, one command to start it, one to stop it.

But there's still friction — we ran our code by shelling into the container. In the next lesson, we connect our **editor** directly to this environment using Dev Containers, so development feels local while running fully inside the container.
