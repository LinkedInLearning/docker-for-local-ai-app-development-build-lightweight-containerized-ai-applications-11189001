# Chapter 1 — Lesson 3: Container Strategy

In the previous lesson, we reviewed a RAG system to understand the different components inside a modern AI system.

Now the question becomes [CLICK]:

How do we translate those components into containers? [CLICK]

There is no universal answer because container strategy depends on both [CLICK] the application architecture and the [CLICK] production environment where the application will eventually run.

[CLICK]

Let's return to our RAG architecture diagram and identify the main services that make up the system.

At a high level, we can break it down into three core components:

[CLICK]

* An ingestion pipeline [CLICK]
* A vector database, and [CLICK]
* A query pipeline

As we saw in the previous lesson, the ingestion pipeline processes documents and stores their embeddings in the vector database.

The vector database stores those embeddings and enables fast retrieval of relevant information.

The query pipeline receives user requests, retrieves the most relevant context from the vector database, sends it to the language model, and returns the final response.

Now we need to decide how these services should be organized.

[CLICK]

One approach would be to put both pipelines inside a single container.

This might work for a quick prototype, but it quickly becomes difficult to manage.

The ingestion pipeline and query pipeline have different responsibilities and may have different requirements.

However, that does not automatically mean they should always run in separate containers.

For example, imagine an application where users upload documents during a session and immediately ask questions about them.

The documents are processed temporarily, used during the session, and discarded afterward rather than being stored permanently.

In this type of application, it may make sense to combine the ingestion and query pipelines into a single container, since they operate together as a single workflow.

In that case, splitting them into multiple services could add unnecessary complexity without providing much benefit.

The decision depends on the application requirements and how the system will eventually run in production.

[CLICK]

On the other hand, there are many situations where separating those two services becomes useful.

For example:

* The ingestion process may run occasionally when new documents arrive.
* The query service, on the other hand, may need to run continuously and respond to users.
* One service may need more CPU or memory than another, and
* Different services may scale independently.

Because of that, components that operate independently are often good candidates for separate containers.

[CLICK]

During the development, [CLICK] we will use dedicated Python and vector database containers.

The Python development container provides a reproducible environment for writing code, installing dependencies, and experimentation.

[CLICK]

Once the individual services stabilize, we can separate them into dedicated and optimized containers and test the pipelines in an environment similar to production.

[CLICK]

This will enable us to smoothly deploy those services in our production environment.

That is important because our goal is not simply to make the application run.

Our goal is to make deployment more predictable and consistent across environments.

The important takeaway from this lesson is that we first identify the services, then define the requirements, and only then decide how to package those services into containers.

In the next lesson, we will put this plan into practice and walk through the overall Docker workflow for building AI applications.
