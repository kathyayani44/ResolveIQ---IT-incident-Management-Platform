import sys

print("Python version:", sys.version)
try:
    import qdrant_client.http.models.models as m
    print("models loaded successfully, number of attributes:", len(dir(m)))
except BaseException as e:
    print("Caught exception:", type(e), e)
