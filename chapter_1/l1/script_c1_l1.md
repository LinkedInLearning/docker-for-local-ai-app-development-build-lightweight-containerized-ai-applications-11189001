# Chapter 1 — Lesson 1: Why Docker Containers?

In this course, we will learn how to use Docker containers to develop production-ready AI applications.

Before we start building containers, it is worth asking a simple question: [CLICK]

Why do we need containers in the first place?

If you have worked on software projects before, you have probably seen the classic problem:[CLICK]

"It works on my machine." [CLICK]

An application runs perfectly on the developer's laptop [CLICK], but when another team member [CLICK] tries to run it, or [CLICK] when it is deployed to a server [CLICK], it breaks [CLICK].

[CLICK]

Maybe the Python version is different.

[CLICK]

Maybe a package version changed.

[CLICK]

Maybe one machine uses Linux, and another uses macOS or Windows.

And maybe the CPU architecture is different.

Even small differences in the environment can cause an application to behave differently.

Traditional applications already face this challenge, but AI applications make it even more difficult.

[CLICK]

AI systems typically rely on many moving parts:

* Python libraries and model dependencies
* External APIs or LLM providers
* Vector databases
* Data ingestion pipelines
* GPU libraries and system packages
* Backend services and web frameworks

As AI applications become more sophisticated, the number of dependencies and services increases rapidly.

[CLICK]

Consider a Retrieval-Augmented Generation system, or in short, RAG. It may include:

* A document ingestion process
* Embedding models
* A vector database
* Query APIs, which include
* Large language models, and
* Frontend applications

All of these components need to work together correctly.

Imagine building a RAG system on your laptop and then sending it to another engineer with a message saying:

"Install Python 3.12, these 25 libraries, a vector database, download this model, configure these environment variables, and hopefully everything works."

That approach quickly becomes difficult to maintain. [CLICK]

This is where containers help.

Containers package the [CLICK] application together with its dependencies and system configuration into a reproducible environment. [CLICK]

Instead of sharing setup instructions, [CLICK] we share the environment itself.

The AI application should have a consistent behavior regardless of where it runs. If it works locally [CLICK], it should run successfully on other devices [CLICK]. Likewise, [CLICK] if it fails on other devices [CLICK], it is easy to reproduce the error in the local development environment.

[CLICK]

The same environment can then be used during:

* Development
* Testing
* Deployment, and
* Production

This creates consistency across the entire application lifecycle.

The main benefit is not simply making things easier to run.

The real benefit is reproducibility.

If something works during development, we want the same behavior during testing and production.

Throughout this course, we will use a RAG system as our running example and learn how containers help us package, develop, test, and deploy AI applications consistently.

In the next lesson, we will explore the main components of a RAG system and how they interact. This will help us later on in the course to build our container strategy.
