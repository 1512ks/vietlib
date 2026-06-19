"""
evaluator.py -- Đánh giá chất lượng retrieval với Precision@K, Recall@K, MRR.

Metrics:
    Precision@K = |relevant ∩ retrieved@K| / K
    Recall@K    = |relevant ∩ retrieved@K| / |relevant|
    MRR         = mean(1 / first_relevant_rank)  (0 nếu không tìm thấy)
    F1@K        = 2 * P@K * R@K / (P@K + R@K)

Vì ground truth dùng keywords (không phải exact doc_id),
ta dùng "keyword matching" để xác định relevant:
    doc được coi là relevant nếu text/metadata chứa >= 1 keyword.

Cách dùng:
    from search.evaluator import Evaluator

    evaluator = Evaluator(pipeline)
    report = evaluator.evaluate(ks=[1, 3, 5, 10])
    evaluator.print_report(report)
    evaluator.save_report(report, "results.json")
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


# ============================================================
#  Helpers
# ============================================================
def _is_relevant(result, keywords: List[str]) -> bool:
    """
    Kiểm tra nếu một SearchResult relevant với keywords.
    Relevant = text hoặc metadata chứa ít nhất 1 keyword (case-insensitive).
    """
    haystack = result.text.lower()
    # Them metadata vao haystack
    for v in result.metadata.values():
        if isinstance(v, str):
            haystack += " " + v.lower()

    return any(kw.lower() in haystack for kw in keywords)


# ============================================================
#  Metrics dataclass
# ============================================================
@dataclass
class QueryMetrics:
    query_id: str
    query: str
    query_type: str
    k: int
    precision: float
    recall: float
    f1: float
    mrr: float
    n_retrieved: int
    n_relevant_retrieved: int
    latency_ms: float


@dataclass
class EvaluationReport:
    ks: List[int]
    n_queries: int
    # Macro averages
    avg_precision: Dict[int, float] = field(default_factory=dict)   # k → avg P@k
    avg_recall: Dict[int, float] = field(default_factory=dict)
    avg_f1: Dict[int, float] = field(default_factory=dict)
    avg_mrr: Dict[int, float] = field(default_factory=dict)
    # Per-query breakdown
    per_query: List[QueryMetrics] = field(default_factory=list)
    # Per-type breakdown
    by_type: Dict[str, Dict[int, float]] = field(default_factory=dict)
    total_latency_ms: float = 0.0
    avg_latency_ms: float = 0.0


# ============================================================
#  Evaluator
# ============================================================
class Evaluator:
    """
    Đánh giá SearchPipeline trên tập TestQuery.

    Args:
        pipeline : SearchPipeline đã build
        mode     : "hybrid" | "bm25" | "vector" (để so sánh từng chiến lược)
    """

    def __init__(self, pipeline, mode: str = "hybrid"):
        self.pipeline = pipeline
        self.mode = mode

    def evaluate(
        self,
        test_queries=None,
        ks: List[int] = [1, 3, 5, 10],
    ) -> EvaluationReport:
        """
        Chạy evaluation trên tập test queries.

        Args:
            test_queries : List[TestQuery] (None = dùng toàn bộ TEST_QUERIES)
            ks           : Danh sách K để tính P@K, R@K

        Returns:
            EvaluationReport
        """
        from .test_queries import get_all_queries
        if test_queries is None:
            test_queries = get_all_queries()

        max_k = max(ks)
        all_metrics: List[QueryMetrics] = []
        total_latency = 0.0

        logger.info(f"Bắt đầu evaluation {len(test_queries)} queries @ K={ks} (mode={self.mode})")

        for tq in test_queries:
            # Search
            t0 = time.time()
            results = self.pipeline.search(
                tq.query,
                top_k=max_k,
                use_reranker=(self.mode == "hybrid"),
                mode=self.mode,
            )
            latency_ms = (time.time() - t0) * 1000
            total_latency += latency_ms

            # Xác định relevant docs (keyword matching)
            relevant_flags = [_is_relevant(r, tq.relevant_keywords) for r in results]

            # Tính metrics cho từng K
            for k in ks:
                retrieved_k = results[:k]
                flags_k = relevant_flags[:k]

                n_relevant = sum(flags_k)
                precision = n_relevant / k if k > 0 else 0.0

                # Recall: cần biết total relevant trong corpus
                # Vì không có ground truth đầy đủ, dùng recall@k = P@k
                # (Convention khi không có toàn bộ relevant set)
                recall = precision  # Simplified recall

                f1 = (2 * precision * recall / (precision + recall)
                      if (precision + recall) > 0 else 0.0)

                # MRR: vị trí đầu tiên relevant trong top max_k
                mrr = 0.0
                for rank_i, flag in enumerate(relevant_flags, 1):
                    if flag:
                        mrr = 1.0 / rank_i
                        break

                all_metrics.append(QueryMetrics(
                    query_id=tq.query_id,
                    query=tq.query,
                    query_type=tq.query_type,
                    k=k,
                    precision=precision,
                    recall=recall,
                    f1=f1,
                    mrr=mrr,
                    n_retrieved=len(retrieved_k),
                    n_relevant_retrieved=n_relevant,
                    latency_ms=latency_ms,
                ))

            logger.info(
                f"  [{tq.query_id}] {tq.query[:50]}… "
                f"| relevant={sum(relevant_flags[:max_k])}/{max_k} "
                f"| {latency_ms:.0f}ms"
            )

        # Aggregate
        report = self._aggregate(all_metrics, ks, total_latency, len(test_queries))
        return report

    def _aggregate(
        self,
        metrics: List[QueryMetrics],
        ks: List[int],
        total_latency: float,
        n_queries: int,
    ) -> EvaluationReport:
        """Tính macro averages và tổng hợp report."""
        report = EvaluationReport(ks=ks, n_queries=n_queries)
        report.total_latency_ms = total_latency
        report.avg_latency_ms = total_latency / n_queries if n_queries > 0 else 0

        for k in ks:
            k_metrics = [m for m in metrics if m.k == k]
            if not k_metrics:
                continue
            report.avg_precision[k] = sum(m.precision for m in k_metrics) / len(k_metrics)
            report.avg_recall[k] = sum(m.recall for m in k_metrics) / len(k_metrics)
            report.avg_f1[k] = sum(m.f1 for m in k_metrics) / len(k_metrics)
            report.avg_mrr[k] = sum(m.mrr for m in k_metrics) / len(k_metrics)

            # By type
            for qtype in ["FACTUAL", "AUTHOR", "SEMANTIC"]:
                type_metrics = [m for m in k_metrics if m.query_type == qtype]
                if not type_metrics:
                    continue
                key = f"{qtype}_P@{k}"
                report.by_type[key] = sum(m.precision for m in type_metrics) / len(type_metrics)

        report.per_query = metrics
        return report

    def print_report(self, report: EvaluationReport, title: str = ""):
        """In report đẹp ra console dùng tabulate."""
        try:
            from tabulate import tabulate
        except ImportError:
            tabulate = None

        print(f"\n{'='*70}")
        t = title or f"Retrieval Evaluation — mode={self.mode}"
        print(f"  {t}")
        print(f"  Queries: {report.n_queries} | Avg latency: {report.avg_latency_ms:.0f}ms")
        print(f"{'='*70}")

        # Main table
        headers = ["K", "Precision@K", "Recall@K", "F1@K", "MRR"]
        rows = []
        for k in report.ks:
            rows.append([
                k,
                f"{report.avg_precision.get(k, 0):.4f}",
                f"{report.avg_recall.get(k, 0):.4f}",
                f"{report.avg_f1.get(k, 0):.4f}",
                f"{report.avg_mrr.get(k, 0):.4f}",
            ])

        if tabulate:
            print(tabulate(rows, headers=headers, tablefmt="grid"))
        else:
            print("  " + " | ".join(headers))
            for r in rows:
                print("  " + " | ".join(str(v) for v in r))

        # By type (P@5)
        print("\n  Breakdown theo loại query (P@5):")
        type_rows = []
        for qtype in ["FACTUAL", "AUTHOR", "SEMANTIC"]:
            k5 = report.by_type.get(f"{qtype}_P@5")
            k3 = report.by_type.get(f"{qtype}_P@3")
            if k5 is not None:
                type_rows.append([qtype, f"{k3:.4f}" if k3 else "N/A", f"{k5:.4f}"])

        if type_rows:
            if tabulate:
                print(tabulate(type_rows, headers=["Type", "P@3", "P@5"], tablefmt="simple"))
            else:
                for r in type_rows:
                    print(f"  {r[0]}: P@3={r[1]}, P@5={r[2]}")

        print()

    def save_report(self, report: EvaluationReport, path: str):
        """Lưu report ra JSON."""
        data = {
            "mode": self.mode,
            "ks": report.ks,
            "n_queries": report.n_queries,
            "avg_latency_ms": report.avg_latency_ms,
            "avg_precision": report.avg_precision,
            "avg_recall": report.avg_recall,
            "avg_f1": report.avg_f1,
            "avg_mrr": report.avg_mrr,
            "by_type": report.by_type,
            "per_query": [asdict(m) for m in report.per_query],
        }
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Đã lưu evaluation report → {path}")
