# Parenting Support Chatbot

## Overview

This project implements a conversational AI assistant designed to support parents who may feel overwhelmed while dealing with common parenting challenges more specifically toddler phase. The chatbot provides evidence-informed guidance inspired by publicly available parenting resources such as summaries of 'Good Inside' book and a well known parenting advice service of the same name founded by clinical psychologist Dr Becky. I have also added related parenting podcast transcripts (freely available online). No copyright material has been included inside this.

The system combines semantic retrieval from parenting materials with tool-based responses to provide supportive suggestions and practical scripts parents can use in difficult moments.

The system demonstrates an applied **Retrieval-Augmented Generation (RAG)** architecture combined with tool-augmented reasoning.

---

# Service 1 – Semantic Query (Parenting Knowledge Base)

The main capability of the chatbot is answering parenting questions using semantic search over a curated parenting knowledge base.

The knowledge base contains:

* a PDF summary of *Good Inside*
* parenting podcast transcript pages

These documents are stored in:

```
assignment_chat/data/raw/
```
As I refine this app further, I'd like to add more freely available resources from Unconditional parenting theme.

### Embedding Process

Document embeddings are computed **offline during ingestion** using the `text-embedding-3-small` embedding model.

The ingestion process performs the following steps:

1. Raw documents are extracted and converted into structured JSONL format.
2. The documents are split into smaller text chunks.
3. Each chunk is embedded using the embeddings API.
4. The embeddings are stored in a persistent **ChromaDB** collection.

The vector database is stored in:

```
assignment_chat/data/chroma/
```

At runtime, only the **user query is embedded**, and semantic similarity search retrieves the most relevant parenting guidance from the vector database.

This design avoids recomputing embeddings during runtime and improves efficiency.

---

# Service 2 – Parenting Support Tool

In addition to retrieval, the system includes a structured support tool that generates short parenting scripts that parents can use in emotionally difficult situations.

Examples include:

* responding to tantrums
* setting boundaries when a child hits
* validating emotions while maintaining limits

This functionality is implemented in:

```
parenting_chat/tools_support.py
```

The tool returns short, practical scripts that combine emotional validation with clear boundaries.

---

# Service 3 – API Tool (Weather-Based Outdoor Reset)

The chatbot includes a weather-based tool that suggests a calm outdoor window for a parent-child reset activity.

This tool uses the **Open-Meteo weather API** to retrieve hourly weather forecasts.

The tool:

* evaluates precipitation probability and wind conditions
* identifies a calmer time window
* suggests an outdoor break such as a short walk

If the user does not provide a city, the system defaults to **Toronto, Canada**.

The implementation is located in:

```
parenting_chat/tools_weather.py
```

---

# Conversational Interface

The chatbot interface is implemented using **Gradio ChatInterface**.

Conversation state is maintained by passing the message history into the LangGraph workflow, allowing the assistant to respond in context during longer conversations.

The main conversational workflow is implemented in:

```
parenting_chat/main.py
```

---

# Guardrails

The system includes guardrails to prevent responses related to restricted topics required by the assignment.

The chatbot will refuse requests about:

* cats or dogs
* horoscopes or zodiac signs
* Taylor Swift

The chatbot will also refuse requests that attempt to reveal the system prompt.

---

# System Architecture

The overall architecture of the system is shown below.

```
User
  │
  ▼
Gradio Chat Interface
  │
  ▼
LangGraph Agent
  │
  ├── Parenting Knowledge Base (ChromaDB semantic search)
  │
  ├── Parenting Support Tool (script generation)
  │
  └── Weather API Tool (Open-Meteo outdoor reset suggestion)
  │
  ▼
LLM Response
```

The agent decides when to call each tool and integrates retrieved information into the final response.

---

# Implementation Location

All implementation code for the assignment is located in:

```
05_src/assignment_chat/
```

Key modules include:

```
assignment_chat/parenting_chat/
    app.py
    main.py
    prompts.py
    tools_rag.py
    tools_weather.py
    tools_support.py
```
