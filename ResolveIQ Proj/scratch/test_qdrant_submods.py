import sys

submods = [
    "qdrant_client.http",
    "qdrant_client.http.models",
    "qdrant_client.local",
    "qdrant_client.local.qdrant_local",
    "qdrant_client.qdrant_client",
]

for s in submods:
    try:
        __import__(s)
        print("OK:", s)
    except Exception as e:
        print("FAIL:", s, e)
