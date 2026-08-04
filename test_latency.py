import requests
import time
import sys


def test_query(question):
    url = "http://localhost:8000/api/v1/pipeline/customer/query"
    payload = {
        "bucket_name": "openai-bucket",
        "question": question,
        "thread_id": "latency-test",
        "embeddings_model": "sentence-transformers/all-MiniLM-L6-v2",
    }

    print(f"\n{'=' * 60}")
    print(f"Query: '{question}'")
    print(f"{'=' * 60}")

    start_time = time.time()

    try:
        response = requests.post(url, json=payload, timeout=60)
        end_time = time.time()
        elapsed = end_time - start_time

        if response.status_code == 200:
            data = response.json()
            answer = data.get("answer", "No answer")
            print(f"\n[OK] Response received in {elapsed:.2f}s")
            print(f"Answer: {answer}")
        else:
            print(f"\n[ERROR] Status {response.status_code} in {elapsed:.2f}s")
            print(f"Detail: {response.text[:500]}")

        return elapsed

    except requests.exceptions.ConnectionError:
        print("[ERROR] Could not connect to server. Is uvicorn running on port 8000?")
        return None
    except Exception as e:
        end_time = time.time()
        elapsed = end_time - start_time
        print(f"[ERROR] after {elapsed:.2f}s: {e}")
        return elapsed


if __name__ == "__main__":
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
    else:
        question = "What is this document about?"

    elapsed = test_query(question)

    if elapsed is not None:
        print(f"\n{'=' * 60}")
        print(f"Total response time: {elapsed:.2f} seconds")
        print(f"{'=' * 60}")
