"""
build_index.py -- Xây index CHUNK-LEVEL tự chứa cho sample model (không đụng Qdrant production).

- Nguồn: corpus/chunks.json (163 chunk × 51 tác phẩm, section: tóm tắt/nhân vật/chủ đề/...).
- Tài liệu nhúng = "{title}. {author}. {text}" (kèm tên+tác giả để bắt câu hỏi thực thể).
- Vector: AITeamVN/Vietnamese_Embedding (bge-m3, 1024 chiều) — chọn ở plan.
- BM25: rank_bm25 trên văn bản tách từ đơn giản.
- Lưu: index/vectors.npy, index/docs.json, index/bm25.pkl, index/index_meta.json.

Chạy: .venv/Scripts/python.exe sample_model/eval/build_index.py [--model MiniLM]
"""
import sys, json, pickle, argparse
from pathlib import Path
import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent   # sample_model/
SRC = ROOT / "corpus" / "chunks.json"
IDX = ROOT / "index"
IDX.mkdir(parents=True, exist_ok=True)

MODELS = {
    "bge-m3": "AITeamVN/Vietnamese_Embedding",
    "MiniLM": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", choices=list(MODELS), default="bge-m3")
    args = ap.parse_args()

    chunks = json.load(open(SRC, encoding="utf-8"))["chunks"]
    docs = []
    for c in chunks:
        text = f"{c['title']}. {c['author']}. {c['text']}"
        docs.append({
            "chunk_id": c["chunk_id"], "work_id": c["work_id"],
            "title": c["title"], "author": c["author"],
            "year": str(c["year"]), "genre": c["genre"], "section": c["section"],
            "text": text,
        })
    print(f"Số chunk: {len(docs)} (từ {len({d['work_id'] for d in docs})} tác phẩm)")

    # Vector embedding
    from sentence_transformers import SentenceTransformer
    model_id = MODELS[args.model]
    print(f"Đang nạp embedding: {model_id} ...")
    emb = SentenceTransformer(model_id)
    vecs = emb.encode([d["text"] for d in docs], normalize_embeddings=True,
                      show_progress_bar=True, batch_size=16)
    vecs = np.asarray(vecs, dtype=np.float32)
    np.save(IDX / "vectors.npy", vecs)
    print(f"Vector: {vecs.shape} -> {IDX/'vectors.npy'}")

    # BM25
    from rank_bm25 import BM25Okapi
    corpus_tok = [d["text"].lower().split() for d in docs]
    bm25 = BM25Okapi(corpus_tok)
    with open(IDX / "bm25.pkl", "wb") as f:
        pickle.dump({"bm25": bm25, "tokens": corpus_tok}, f)

    meta = {"model": model_id, "model_key": args.model, "dim": int(vecs.shape[1]),
            "n": len(docs), "level": "chunk", "source": "corpus/chunks.json"}
    json.dump(docs, open(IDX / "docs.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    json.dump(meta, open(IDX / "index_meta.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"Xong: {meta}")


if __name__ == "__main__":
    main()
