import traceback

try:
    import qdrant_client
    print("qdrant_client imported successfully!")
except Exception as e:
    traceback.print_exc()
