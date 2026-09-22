import faiss
import pickle
from sentence_transformers import SentenceTransformer
from config import DATA_PROCESSED

model = SentenceTransformer("all-MiniLM-L6-v2")
index = faiss.read_index(str(DATA_PROCESSED / "rag_index.faiss"))
chunks = pickle.load(open(DATA_PROCESSED / "rag_chunks.pkl", "rb"))

def retrieve(question, k=3):
    q_embedding = model.encode([question])
    distances, indices = index.search(q_embedding, k)
    return [chunks[i] for i in indices[0]]

if __name__ == "__main__":
    results = retrieve("What retention offers are approved for Bihar", k=5)
    for r in results:
        print("---")
        print(r)