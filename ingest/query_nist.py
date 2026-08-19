"""Queries the governance docs Chroma collection with a plain_english question"""

import chromadb

DB_PATH = "chroma_db"
COLLECTION_NAME = "governance_docs"

def query_db(question: str, n_results: int = 5) -> None:
    client = chromadb.PersistentClient(path = DB_PATH)
    collection = client.get_collection(COLLECTION_NAME)

    results = collection.query( #3 things in one call, embedding question, computing distance against all vectors and returning the 5 closest, ranked. 
        query_texts = [question],
        n_results = n_results,
    )

    print(f"\nQuery: {question}\n")
    ids = results["ids"][0] # has to do this because chroma wraps the results in 2 lists. so the second [0] is to pull it out of the outer-wrapped list
    distances = results["distances"][0]
    metadatas = results["metadatas"][0]

    for i in range(len(ids)):
        rank = i + 1
        chunk_id = ids[i]
        distance = distances[i]
        meta = metadatas[i]

        print(f"{rank}. {meta['display_id']}  (distance={distance:.4f})") #.4f is a format-spec syntax to print to 4 decimal places.
        print(f"   {meta['text']}")
        print()

if __name__ == "__main__":
    query_db("how does NIST think about third-party AI risk")