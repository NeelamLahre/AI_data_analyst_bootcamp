import faiss
import pickle
import pandas as pd
from sentence_transformers import SentenceTransformer
from pypdf import PdfReader
from config import DOCS_DIR, DATASET_XLSX, DATA_PROCESSED

model = SentenceTransformer("all-MiniLM-L6-v2")
chunks = []

# Circle targets - load FIRST, since offer chunks below need circle_name_map from this
circle_targets = pd.read_excel(DATASET_XLSX, "circle_targets")
for _, row in circle_targets.iterrows():
    chunks.append(f"Circle target for {row['circle']}: {row.to_dict()}")

# Offer catalogue - one chunk per offer row, with circle codes expanded to full names
circle_name_map = dict(zip(circle_targets["circle_code"], circle_targets["circle"]))

offer_catalogue = pd.read_excel(DATASET_XLSX, "offer_catalogue")
for _, row in offer_catalogue.iterrows():
    codes = [c.strip() for c in str(row["approved_circles"]).split(",")]
    full_names = [circle_name_map.get(c, c) for c in codes]
    chunk_text = (
        f"Offer {row['offer_code']} ({row['offer_name']}): {row.to_dict()}. "
        f"Approved circles (full names): {', '.join(full_names)}"
    )
    chunks.append(chunk_text)

# Engagement brief PDF - chunked by 500 characters
reader = PdfReader(DOCS_DIR / "Jio_Retention_Brief.pdf")
for page in reader.pages:
    page_text = page.extract_text()
    for i in range(0, len(page_text), 500):
        chunks.append(page_text[i:i + 500])

print(f"Total chunks: {len(chunks)}")

embeddings = model.encode(chunks, show_progress_bar=True)
index = faiss.IndexFlatL2(embeddings.shape[1])
index.add(embeddings)

faiss.write_index(index, str(DATA_PROCESSED / "rag_index.faiss"))
with open(DATA_PROCESSED / "rag_chunks.pkl", "wb") as f:
    pickle.dump(chunks, f)

print("Saved rag_index.faiss and rag_chunks.pkl")