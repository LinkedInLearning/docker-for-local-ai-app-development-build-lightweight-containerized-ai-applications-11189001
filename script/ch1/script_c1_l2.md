# Chapter 1 — Lesson 2: Introduction to RAG

In the previous lesson, we discussed why containers matter and how they help solve the "it works on my machine" problem.

Before we start thinking about containers, we first need to understand what a modern AI application looks like.

[CLICK]

Throughout this course, we will use a Retrieval-Augmented Generation system, or RAG for short, as our running example.

We chose RAG because it is an AI system with multiple components, which makes it a great fit for learning Docker. While we focus on RAG throughout the course, the same concepts can be applied to many other AI and agentic applications.

This is not a RAG course, so we are not going to dive deeply into the underlying concepts. Instead, we want to understand the big picture and give you the tools and intuition that you can later apply to your own unique use cases.

At a high level, [CLICK] a RAG system enables a language model to answer questions about information it was not trained on and does not have access to [CLICK] by using external data. For example, this could be your company's travel policy, internal documentation, or a financial report that was released an hour ago.

To make this possible, [CLICK] the external information is converted into embeddings, allowing the language model to retrieve relevant information and [CLICK] use it when generating an answer.

[CLICK]

Now let's walk through this RAG architecture diagram and see how the different components fit together.

[CLICK]

The first component is the data ingestion pipeline.

It may sound surprising, but large language models do not work directly with raw text. Instead, they work with numerical representations of text called embeddings.

The role of the ingestion pipeline is to process information from different sources, such as PDF files, break the text into smaller chunks, convert those chunks into vectors using embedding models, and store them in a vector database.

[CLICK]

The second component is the query pipeline.

This pipeline takes a user's question, converts it into a vector using a similar embedding model, and searches the vector database for related information.

The search may return multiple results. A ranking process identifies the most relevant information and sends it to the language model as additional context. The model then uses that information to generate an answer.

This is only a simplified view of the system. In production environments, you may have additional components such as logging, monitoring, and observability services, and of course, a user interface.

AI agents, forecasting systems, recommendation systems, and many other AI applications often follow similar patterns.

The specific components may change, but the overall structure often remains the same.

The key takeaway from this lesson is not how RAG works internally.

The key takeaway is that modern AI systems are usually composed of multiple independent components working together.

Once we identify those components, we can start thinking about an important question:

Should everything run in one container, or should different components run independently?

In the next lesson, we will use this RAG example to plan a container strategy and decide how these different pieces fit together.
