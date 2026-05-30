# Chapter 1 — Lesson 4: Containerized Development Workflow for AI Applications

In the previous lesson, we built a container strategy for our RAG system. We identified the services, thought about their requirements, and decided how to package them across the development, test, and deployment stages.

Now the question becomes: how do we actually get there?

In this lesson, we will walk through the overall Docker workflow we follow when developing an AI application — from the first idea all the way to a system running in production.

[CLICK]

Everything starts with a clear plan.

Before we write a single line of code or build a single image, we work with our AI code-generation tool to define a clear requirements document based on the project scope.

The output of this process is a project spec.

A good spec describes:

* The environment settings 
* The infrastructure requirements 
* The general architecture 
* And the implementation stages 

[CLICK]

One part of this spec is especially important for us right now: the development environment requirements.

These requirements describe exactly what our development environment needs, and we will use them to build our development image.


In chapter 2, we will focus in more detail on this Docker workflow: how requirements turn into a Dockerfile, how a Dockerfile is built into an image, and how an image runs as a container.

Requirements, to Dockerfile, to build image, to run container.

[CLICK]

Now let's look at the development stage for our RAG system.

Based on the strategy from lesson 3, we start with two containers.


The first is a vector database container, using ChromaDB.

The second is a Python development container, which we use to prototype the data ingestion and query pipelines.

We will develop directly inside the containerized environment using VS Code and the Dev Containers extension. This lets us write and run code inside the exact environment we defined in the spec, with no "it works on my machine" surprises.

We will focus on this prototype stage in chapter 3.

[CLICK]

Once the prototype is complete, we move into the testing stage.

Here we do three things.


First, we make the code robust by functionalizing it — turning exploratory prototype code into clean, reusable functions.

Second, we test the code.

Third, we move the different components into separate containers — one for the ingestion pipeline and one for the query pipeline.

This last step lets us test the code in an environment that is much closer to production, where we need to make sure the different components can actually connect — networking, access, and port settings.

We will cover this testing stage in chapter 4.

[CLICK]

The last step before deploying to production is to optimize the containers for each service.

These optimized containers are the ones we will use in production.

From this point, we can start to onboard the system components into the production environment gradually, testing as we go, until the system is fully deployed.

This will be the focus of chapter 5.

[CLICK]

So the full workflow looks like this:

Spec, then development, then test, then deployment.

And each stage maps to a chapter in this course — the Docker fundamentals behind the spec in chapter 2, the prototype in chapter 3, the testing stage in chapter 4, and deployment readiness in chapter 5.

The key takeaway is that containers are not something we add at the end of a project. They are part of the workflow from the beginning, allowing us to develop, test, and prepare applications for production in consistent environments.

[CLICK]

In the next chapter, we will dive into the Docker fundamentals and learn how requirements become a Dockerfile, an image, and a running container.
