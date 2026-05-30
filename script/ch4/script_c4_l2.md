# Chapter 4 — Lesson 2: Dedicated Images per Service

In the previous lesson, we reviewed the motivation to split the application into separate services. In this lesson, we'll build a dedicated image for each one.

We'll start with the design on the slides, then switch to the terminal and build the images.

The key decision is simple: one image for ingestion and one image for query. Each service gets its own Dockerfile and dependency set.

[CLICK]

Let's start with dependencies, because that's where the split delivers the biggest benefit.

The ingestion service parses PDFs, so it requires Docling and its supporting libraries. The query service never parses documents. It retrieves context and calls an LLM.

As a result, we maintain two requirements files. requirements-ingestion.txt contains Docling and the embedding stack. requirements-query.txt contains only the libraries needed for serving queries, such as FastAPI, LangChain clients, and the ChromaDB client.

The key difference is that the query image doesn't include Docling or any of its dependencies.

[CLICK]

Next, the application entry points.

Today, all routes live in a single FastAPI application. To support dedicated services, we split those routes into two routers: one for ingestion and one for query.

We then create two lightweight application modules. ingestion_app.py exposes only the ingestion routes, while query_app.py exposes only the query routes. Both keep the /health endpoint.

This separation matters because the query application never imports the ingestion code. As a result, it never loads Docling and can remain lightweight.

[CLICK]

Now for the Dockerfiles.

Both follow the same best practices from earlier chapters: a pinned base image, dependency layers before application code, and an execution with the CMD commands.

The differences are minimal: the requirements file, the application entry point, and the exposed port.

The query image uses the lightweight dependency set, while the ingestion image adds the system libraries required by Docling and runs on port 8081.

Let's go back to VSCode and build them.

[SWITCH TO TERMINAL]

From the project root, we'll build the query image first:

docker build -f chapter_4/l2/Dockerfile_Query -t rag-query:0.1.0 .

[CLICK]

Next, the ingestion image:

docker build -f chapter_4/l2/Dockerfile_Ingestion -t rag-ingestion:0.1.0 .

This build takes longer because it includes the document parsing stack.

[CLICK]

Now let's compare the results:

docker images | grep rag-

The query image is significantly smaller than the ingestion image because it doesn't include the parsing dependencies.

That means faster image transfers, faster startup times, and a smaller attack surface whenever we update the query service.

[CLICK]

At this point, we have two images, each optimized for a specific job.

Notice that we're reusing everything we've already learned: Dockerfile best practices from Chapter 2 and image design strategies from Chapter 3. The only new idea is creating separate entry points and images for each service.

In the next lesson, we'll bring everything together with Docker Compose and run ingestion, query, and ChromaDB as a single application stack.