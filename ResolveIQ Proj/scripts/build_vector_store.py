"""
Script to build the local Qdrant vector store for ResolveIQ (Day 3).
Generates embeddings for chunks and inserts them into Qdrant.
"""

import argparse
import json
import sys
import time
from pathlib import Path

# Ensure src module can be imported
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.embeddings.embedder import ResolveIQEmbedder
from src.vectorstore.qdrant_store import ResolveIQQdrantStore

RUNBOOK_CHUNKS_FILE = Path("data/chunks/runbook_chunks.jsonl")
POSTMORTEM_CHUNKS_FILE = Path("data/chunks/postmortem_chunks.jsonl")

COLLECTION_RUNBOOKS = "resolveiq_runbooks"
COLLECTION_POSTMORTEMS = "resolveiq_postmortems"


def load_chunks(file_path: Path) -> list:
    if not file_path.exists():
        print(f"Warning: {file_path} not found.")
        return []
    
    chunks = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                chunks.append(json.loads(line))
    return chunks


def process_collection(
    collection_name: str,
    file_path: Path,
    embedder: ResolveIQEmbedder,
    store: ResolveIQQdrantStore,
    rebuild: bool,
    batch_size: int,
):
    print(f"\n--- Processing Collection: {collection_name} ---")
    
    dim = embedder.get_dimension()
    ready = store.setup_collection(collection_name, dimension=dim, rebuild=rebuild)
    
    if not ready:
        print(f"Skipping {collection_name} because it already exists and --rebuild was not specified.")
        return 0
    
    chunks = load_chunks(file_path)
    if not chunks:
        print(f"No chunks loaded for {collection_name}.")
        return 0
    
    total_chunks = len(chunks)
    print(f"Loaded {total_chunks} chunks.")
    
    # Process in batches
    processed = 0
    for i in range(0, total_chunks, batch_size):
        batch = chunks[i : i + batch_size]
        texts = [chunk.get("content", "") for chunk in batch]
        
        # Generate embeddings
        print(f"Generating embeddings for batch {i} to {min(i + batch_size, total_chunks)}...")
        embeddings = embedder.embed_batch(texts, batch_size=batch_size)
        
        # Insert into Qdrant
        print("Inserting into Qdrant...")
        store.insert_chunks(
            collection_name=collection_name,
            chunks=batch,
            embeddings=embeddings,
            batch_size=batch_size
        )
        processed += len(batch)
        
    print(f"Finished processing {processed} chunks for {collection_name}.")
    return processed


def print_validation_report(
    embedder: ResolveIQEmbedder,
    store: ResolveIQQdrantStore,
    runbooks_processed: int,
    postmortems_processed: int
):
    print("\n=====================================================================================")
    print("DAY 3 VALIDATION REPORT")
    print("=====================================================================================")
    print(f"1. Embedding model name         : {embedder.get_model_name()}")
    print(f"2. Embedding vector dimension   : {embedder.get_dimension()}")
    print(f"3. Runbook chunks processed     : {runbooks_processed:,}")
    print(f"4. Postmortem chunks processed  : {postmortems_processed:,}")
    
    rb_stats = store.get_collection_stats(COLLECTION_RUNBOOKS)
    pm_stats = store.get_collection_stats(COLLECTION_POSTMORTEMS)
    
    rb_vectors = rb_stats.get("vectors_count", 0)
    pm_vectors = pm_stats.get("vectors_count", 0)
    
    print(f"5. Vectors stored in runbooks   : {rb_vectors:,}")
    print(f"   Vectors stored in postmortems: {pm_vectors:,}")
    print(f"6. Total vectors stored         : {rb_vectors + pm_vectors:,}")
    print(f"7. Database location            : {store.db_path}")
    
    print("\n8. Sample Payloads:")
    rb_sample = store.get_sample_payload(COLLECTION_RUNBOOKS)
    if rb_sample:
        print(f"   Runbooks sample ID: {rb_sample.get('chunk_id')}")
        print(f"   Title: {rb_sample.get('title')}")
    else:
        print("   Runbooks sample: None")
        
    pm_sample = store.get_sample_payload(COLLECTION_POSTMORTEMS)
    if pm_sample:
        print(f"   Postmortems sample ID: {pm_sample.get('chunk_id')}")
        print(f"   Title: {pm_sample.get('title')}")
    else:
        print("   Postmortems sample: None")
        
    print("\n--- TEST QUERY ---")
    query = "database connection timeout"
    print(f"Query: '{query}'")
    
    query_vector = embedder.embed_batch([query], batch_size=1)[0]
    
    for coll_name in [COLLECTION_RUNBOOKS, COLLECTION_POSTMORTEMS]:
        print(f"\nTop 3 results from {coll_name}:")
        if store.client.collection_exists(coll_name):
            results = store.search(coll_name, query_vector, limit=3)
            for idx, res in enumerate(results, 1):
                payload = res["payload"]
                score = res["score"]
                title = payload.get("title", "No Title")
                section = payload.get("section", "No Section")
                content_preview = payload.get("content", "").replace("\n", " ")[:80]
                print(f"  {idx}. Score: {score:.4f} | Title: {title}")
                print(f"     Section: {section}")
                print(f"     Preview: \"{content_preview}...\"")
        else:
            print("  Collection not found.")


def main():
    parser = argparse.ArgumentParser(description="Build ResolveIQ vector store.")
    parser.add_argument("--rebuild", action="store_true", help="Delete and recreate existing collections.")
    parser.add_argument("--batch-size", type=int, default=128, help="Batch size for embedding generation.")
    args = parser.parse_args()

    print("=====================================================================================")
    print("RESOLVEIQ VECTOR STORE BUILDER (DAY 3)")
    print("=====================================================================================")

    embedder = ResolveIQEmbedder()
    store = ResolveIQQdrantStore()

    start_time = time.time()

    rb_processed = process_collection(
        collection_name=COLLECTION_RUNBOOKS,
        file_path=RUNBOOK_CHUNKS_FILE,
        embedder=embedder,
        store=store,
        rebuild=args.rebuild,
        batch_size=args.batch_size
    )

    pm_processed = process_collection(
        collection_name=COLLECTION_POSTMORTEMS,
        file_path=POSTMORTEM_CHUNKS_FILE,
        embedder=embedder,
        store=store,
        rebuild=args.rebuild,
        batch_size=args.batch_size
    )

    elapsed = time.time() - start_time
    print(f"\nTotal processing time: {elapsed:.2f} seconds.")

    print_validation_report(
        embedder=embedder,
        store=store,
        runbooks_processed=rb_processed,
        postmortems_processed=pm_processed
    )


if __name__ == "__main__":
    main()
