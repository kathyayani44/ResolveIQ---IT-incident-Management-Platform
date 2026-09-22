import sys
import traceback

print("Starting test_qdrant.py...")
try:
    from qdrant_client import QdrantClient
    print("Imported QdrantClient successfully!")
    client = QdrantClient(path="data/qdrant_db")
    print("QdrantClient opened data/qdrant_db successfully!")
    colls = client.get_collections()
    for c in colls.collections:
        info = client.get_collection(c.name)
        print(f"Collection: {c.name}, points_count: {info.points_count}")
    client.close()
    print("Test completed successfully!")
except Exception as e:
    traceback.print_exc()
    sys.exit(1)
