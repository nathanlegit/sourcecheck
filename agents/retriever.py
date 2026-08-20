"""Retriever agent: question in, ranked chunks out. How this is different for parse_nist: This script returns a list of dicts instead of printing, so we can pass these to the answerer agent."""

import chromadb

DB_PATH = "chroma_db"
COLLECTION_NAME = "governance_docs"


def retrieve(question: str, n_results: int = 5) -> list[dict]:
    """Return the n_results chunks most relevant to question.

    Each result is a dict: chunk_id, display_id, document, text,
    scored, distance.
    """
    client = chromadb.PersistentClient(path=DB_PATH)
    collection = client.get_collection(COLLECTION_NAME)

    results = collection.query(
        query_texts=[question],
        n_results=n_results,
    )

    ids = results["ids"][0]
    distances = results["distances"][0]
    metadatas = results["metadatas"][0]

    chunks = [] 
    for chunk_id, distance, meta in zip(ids, distances, metadatas): #easier way to write what was written in parse_nist.py. basically maintains a triple set mapping. 
        chunks.append({
            "chunk_id": chunk_id,
            "display_id": meta["display_id"],
            "document": meta["document"],
            "text": meta["text"],
            "scored": meta["scored"],
            "distance": distance,
        })

    return chunks


if __name__ == "__main__": #preserved for a manual-test capability
    results = retrieve("What does NIST say about legal and regulatory requirements?")
    for r in results:
        print(f"{r['display_id']}  ({r['distance']:.4f})  {r['text'][:80]}")