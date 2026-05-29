# Chapter 2 — Lesson 4: Working with Registries

In the previous lesson, we built an image and it landed in our **local** image store. That is fine for our own machine — but a teammate, a server, or a CI pipeline cannot see it there.

This lesson is about sharing images through a **registry**.

[CLICK]

A registry is a service that stores and distributes container images. You have already been using one without thinking about it.

Every time a build starts with `FROM python:3.11-slim`, Docker **pulls** that base image from a registry. By default, that registry is **Docker Hub** — the public registry Docker uses unless you tell it otherwise.

[CLICK]

We can also pull explicitly:

```bash
docker pull python:3.11-slim
```

This downloads the image and its layers into our local store, ready to use.

[CLICK]

To understand pushing, we first need to understand how images are **named**.

A full image reference looks like this:

```text
docker.io/library/python:3.11-slim
└─ registry ┘└ namespace ┘└ repo ┘└ tag ┘
```

When you type `python:3.11-slim`, Docker fills in the defaults: the `docker.io` registry and the `library` namespace that holds official images. To push your *own* image, the namespace must be **your Docker Hub username**.

[CLICK]

So sharing an image is three steps: **log in**, **tag**, **push**.

First, log in to Docker Hub:

```bash
docker login
```

This prompts for your Docker Hub username and a password or access token, and stores the credentials locally.

[CLICK]

Second, **tag** the local image with your namespace. Tagging does not copy the image — it adds a second name that points at the same image:

```bash
docker tag demo:0.1 myuser/demo:0.1
```

Now `demo:0.1` and `myuser/demo:0.1` are the same image; the second name is one a registry will accept.

[CLICK]

Third, **push** it:

```bash
docker push myuser/demo:0.1
```

Docker uploads each layer that the registry does not already have. Layers it already has are skipped — the same caching idea we saw with builds, now over the network.

[CLICK]

The image now lives on Docker Hub. On any other machine — a colleague's laptop, a server, a CI runner — it can be pulled by name:

```bash
docker pull myuser/demo:0.1
```

That round trip, push here and pull there, is how an image travels from your machine to where it actually runs.

[CLICK]

Two things worth knowing before we move on.

A repository can be **public** or **private**. Public images anyone can pull; private images require authentication. You choose this per repository on Docker Hub.

And the **tag** matters. If you push without a version — just `myuser/demo` — Docker assumes `latest`. That moving tag is convenient but unreliable for anything real, because it silently changes out from under you. We will come back to tagging strategy when we prepare images for production.

[CLICK]

That is the whole everyday workflow: pull base images, tag your own with your namespace, push to share, pull to deploy.

In the next lesson, we go back to running images — the `docker run` command and the flags you will use every day.
