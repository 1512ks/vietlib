"""
run_ragas.py -- Chạy RAGAS THẬT (thư viện) với Gemini làm judge trên dataset đã cache.

Đọc results/ragas_dataset.json (question/answer/contexts/ground_truth).
Metric: faithfulness, answer_relevancy, context_precision, context_recall.
Judge LLM: gemini-2.5-flash (temperature 0) qua langchain-google-genai.

Chạy: .venv/Scripts/python.exe -m sample_model.eval.run_ragas [--n 12]
"""
from __future__ import annotations
import argparse, json, os, sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT.parent))
DATASET = ROOT / "results" / "ragas_dataset.json"
OUT = ROOT / "results" / "ragas_real_results.json"


def load_key():
    if os.environ.get("GEMINI_API_KEY"):
        return
    sec = ROOT.parent / ".streamlit" / "secrets.toml"
    if sec.exists():
        for l in sec.read_text(encoding="utf-8").splitlines():
            if l.strip().startswith("GEMINI_API_KEY"):
                os.environ["GEMINI_API_KEY"] = l.split("=", 1)[1].strip().strip('"').strip("'")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=12, help="Số mẫu (giới hạn API)")
    args = ap.parse_args()
    load_key()
    os.environ.setdefault("GOOGLE_API_KEY", os.environ.get("GEMINI_API_KEY", ""))

    data = json.load(open(DATASET, encoding="utf-8"))[: args.n]

    from ragas import evaluate
    from ragas.dataset_schema import EvaluationDataset, SingleTurnSample
    from ragas.metrics import (Faithfulness, ResponseRelevancy,
                               LLMContextPrecisionWithReference, LLMContextRecall)
    from ragas.llms import LangchainLLMWrapper
    from ragas.embeddings import LangchainEmbeddingsWrapper
    from ragas.run_config import RunConfig
    from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

    judge = LangchainLLMWrapper(ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0))
    emb = LangchainEmbeddingsWrapper(GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001"))

    samples = [SingleTurnSample(user_input=d["question"], response=d["answer"],
                                retrieved_contexts=d["contexts"], reference=d["ground_truth"])
               for d in data]
    ds = EvaluationDataset(samples=samples)

    metrics = [Faithfulness(llm=judge), ResponseRelevancy(llm=judge, embeddings=emb),
               LLMContextPrecisionWithReference(llm=judge), LLMContextRecall(llm=judge)]

    print(f"Chạy RAGAS trên {len(samples)} mẫu (judge=gemini-2.5-flash)...")
    result = evaluate(dataset=ds, metrics=metrics,
                      run_config=RunConfig(max_workers=2, timeout=180))
    print("\n=== RAGAS (thư viện thật) ===")
    print(result)

    df = result.to_pandas()
    summary = {c: round(float(df[c].mean()), 4) for c in df.columns
               if df[c].dtype.kind in "fi"}
    out = {"n": len(samples), "judge": "gemini-2.5-flash", "summary": summary,
           "per_query": df.to_dict(orient="records")}
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2, default=str)
    print(f"\nTB: {summary}\n💾 Lưu: {OUT}")


if __name__ == "__main__":
    main()
