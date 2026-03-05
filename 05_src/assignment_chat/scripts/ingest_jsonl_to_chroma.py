#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import os

from dotenv import load_dotenv
#load_dotenv(".secrets")
ROOT_05_SRC = Path(__file__).resolve().parents[2]
SECRETS_PATH = ROOT_05_SRC / ".secrets"
load_dotenv(SECRETS_PATH)

import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter

# use LangChain embeddings through the course gateway
from langchain_openai import OpenAIEmbeddings

#JSONL_PATH = Path("05_src/assignment_chat/data/derived/parenting_corpus.jsonl")
#CHROMA_DIR = "05_src/assignment_chat/data/chroma"

from pathlib import Path

ROOT_05_SRC = Path(__file__).resolve().parents[2]  

JSONL_PATH = ROOT_05_SRC / "assignment_chat" / "data" / "derived" / "parenting_corpus.jsonl"
CHROMA_DIR = str(ROOT_05_SRC / "assignment_chat" / "data" / "chroma")


COLLECTION = "parenting_corpus"


def main():
    # no OPENAI_API_KEY; we require the gateway key instead
    if not os.getenv("API_GATEWAY_KEY"):
        raise ValueError("Missing API_GATEWAY_KEY in environment (.secrets)")

    if not JSONL_PATH.exists():
        raise FileNotFoundError(f"Missing {JSONL_PATH} — run extraction scripts first")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    # embeddings via gateway base_url + header
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        base_url="https://k7uffyg03f.execute-api.us-east-1.amazonaws.com/prod/openai/v1",
        api_key="any value",
        default_headers={"x-api-key": os.getenv("API_GATEWAY_KEY")},
    )

    client = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = client.get_or_create_collection(name=COLLECTION)

    docs, metas, ids = [], [], []

    n_in = 0
    with JSONL_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            obj = json.loads(line)
            n_in += 1
            text = obj["text"]
            chunks = splitter.split_text(text)

            for j, ch in enumerate(chunks):
                _id = f"{obj['source']}::{obj['section']}::{j}"
                ids.append(_id)
                docs.append(ch)
                metas.append({
                    "source": obj["source"],
                    "title": obj.get("title", ""),
                    "section": obj.get("section", "")
                })

    print(f"Loaded {n_in} records -> {len(docs)} chunks")

    # embed in batches, then store embeddings directly
    BATCH = 64
    for i in range(0, len(docs), BATCH):
        batch_docs = docs[i:i+BATCH]
        batch_ids = ids[i:i+BATCH]
        batch_metas = metas[i:i+BATCH]

        batch_vecs = embeddings.embed_documents(batch_docs)

        collection.add(
            ids=batch_ids,
            documents=batch_docs,
            metadatas=batch_metas,
            embeddings=batch_vecs,
        )
        print(f"Added {min(i+BATCH, len(docs))}/{len(docs)}")

    print(f"Done. Chroma persisted at {CHROMA_DIR} (collection={COLLECTION}).")


if __name__ == "__main__":
    main()