from toon import encode

data = {
    "metadata": {"version": 1, "author": "test"},
    "items": [
        {"id": 1, "name": "Item1"},
        {"id": 2, "name": "Item2"},
    ],
    "tags": ["alpha", "beta", "gamma"],
}
print(encode(data))
