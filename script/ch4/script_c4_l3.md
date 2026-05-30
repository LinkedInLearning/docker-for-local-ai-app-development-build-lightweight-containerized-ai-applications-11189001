# Chapter 4 — Lesson 3: Orchestrating the Stack with Compose

We now have dedicated images for the ingestion and query services, along with our database container.

In this lesson, we'll use Docker Compose to bring all three services together into a single application stack. We'll start with the concepts on the slides, then switch to the terminal and run everything in practice.

[CLICK]

We already used Docker Compose in Chapter 3, so the tool itself is familiar. What's different here is the purpose of the Compose file.

In Chapter 3, we used a development Compose file. It mounted our source code into the container and kept the environment running so we could edit code interactively.

This time, we're using a test Compose file. There are no source mounts and no development shell. Each container runs directly from the image we built in the previous lesson.

That means we're testing the same artifacts we would use in production.

[CLICK]

The stack consists of three services connected on a shared network: the ingestion service on port 8081, the query service on port 8080, and ChromaDB on port 8000.

The ingestion and query services are built directly from the Dockerfiles we created in the previous lesson. Compose doesn't just run containers—it can also build the images for us.

The other important addition is a database health check combined with depends_on.

[CLICK]

Why do we need a health check?

By itself, depends_on only waits for a container to start. It doesn't guarantee that the service inside the container is ready to accept connections.

For a database, that difference matters. The container may be running while the database is still initializing.

The health check solves this problem. Compose repeatedly checks the database heartbeat endpoint and waits until it reports healthy. Only then do the ingestion and query services start.

This prevents startup failures caused by services trying to connect before the database is ready.

[CLICK]

Let's go back to the terminal.

[SWITCH TO TERMINAL]

From the project root, a single command builds the images and starts all three services:

docker compose -f chapter_4/l3/docker-compose.test.yaml up -d --build

Compose builds the service images, starts ChromaDB, waits for the health check to pass, and then starts the ingestion and query services.

[CLICK]

Let's verify everything is running:

docker compose -f chapter_4/l3/docker-compose.test.yaml ps

We should see all three services running, with the database reported as healthy.

[CLICK]

We can also inspect the logs for one of the services:

docker compose -f chapter_4/l3/docker-compose.test.yaml logs query

This confirms the application started successfully.

[CLICK]

Now let's perform a quick smoke test using the multi-service Streamlit client:

bash clients/run_streamlit_services.sh

From the sidebar, I'll select Check Health. Both the ingestion and query services respond, confirming that the stack is running and reachable.

[CLICK]

At this point, the application is running as separate containers, just as it would in production.

But running isn't the same as working. We still need to verify that the services can communicate correctly and complete end-to-end workflows.

In the next lesson, we'll test exactly that by ingesting documents through one service and querying them through another.