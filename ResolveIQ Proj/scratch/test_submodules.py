import sys

modules = ["h2", "hpack", "hyperframe", "portalocker", "google.protobuf", "win32api", "grpc"]
for m in modules:
    try:
        __import__(m)
        print("OK:", m)
    except Exception as e:
        print("FAIL:", m, e)
