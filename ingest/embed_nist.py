"""Embeds the NIST chunks into a local Chroma Collection"""

import json

import chromadb

INPUT_PATH = "corpus/parsed/nist.jsonl"
DB_PATH = "chroma_db"
COLLECTION_NAME = "governance_docs"

def load_records(path: str) -> list[dict]:
    """Loads the parsed NIST JSONL file and returns a list of records"""
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f]

def embed_records(records: list[dict]) -> None:
    """Main function to embed NIST chunks"""
    client = chromadb.PersistentClient(path = DB_PATH) #Chroma has 2 modes, in-memory where everything vanishes when process exits, or persistent where everything is written to disk. The latter is what we want.
    collection = client.get_or_create_collection(name = COLLECTION_NAME) #Collection is Chrom's word for a table or a named bucket of vectors

    collection.upsert( #used upsert to insert or update records incase it already exists in the colection. Matter as we will re run this script to tweak embed_text
        ids = [r["chunk_id"] for r in records], #primary key
        documents = [r["text"] for r in records], #was originally r["embed_text"], see RESULTS.MD for the experiment and why this was changed to get rid of the prepending
        metadatas = [ #direct record of everyting else retrievable along with the match. "text" is here not embed_text so we can pullo out the actual text for scoring or display
            {
                "display_id": r["display_id"],
                "document": r["document"],
                "function": r["function"],
                "category_id": r["category_id"],
                "text": r["text"],
                "scored": r["scored"],
            }
            for r in records
        ],
    )
    print(f"Embedded {len(records)} records into Chroma collection '{COLLECTION_NAME}' at '{DB_PATH}'")

if __name__ == "__main__":
    records = load_records(INPUT_PATH)
    embed_records(records)