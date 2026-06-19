"""
_test_pipeline.py -- Kiểm thử nhanh SearchPipeline (chạy 1 lần, xóa sau khi verify)
"""
import sys, logging
sys.path.insert(0, '.')
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s', datefmt='%H:%M:%S')

from vector_store.qdrant_client_app import QdrantManager
from chunking.embedder import Embedder
from search.search_pipeline import SearchPipeline, PipelineConfig

qdrant = QdrantManager(collection_name='vn_literature_gbooks')
print(f'Collection: {qdrant.client.count(collection_name="vn_literature_gbooks").count} chunks')

embedder = Embedder(model_name=Embedder.FAST_MODEL)

config = PipelineConfig(
    n_candidates=20, n_rerank=10, top_k=5,
    use_reranker=False,
    bm25_cache_path='data/bm25_index.pkl',
)
pipeline = SearchPipeline.build(qdrant_manager=qdrant, embedder=embedder, config=config, force_rebuild_bm25=True)

TEST_QUERIES = [
    ('truyen ngan cua Nam Cao ve nguoi nong dan ngheo', 'hybrid'),
    ('sach cua Nguyen Nhat Anh', 'hybrid'),
    ('tieu thuyet chien tranh Viet Nam', 'hybrid'),
    ('Nam Cao Chi Pheo', 'bm25'),
    ('chuyen tinh yeu lang man', 'vector'),
]

for query, mode in TEST_QUERIES:
    results = pipeline.search(query, top_k=3, use_reranker=False, mode=mode)
    print(f'\n[{mode.upper()}] {query}')
    for i, r in enumerate(results, 1):
        title = str(r.metadata.get('title', '?'))[:50]
        author = str(r.metadata.get('author', '?'))[:25]
        print(f'  [{i}] {title} | {author} | score={r.score:.4f}')

print('\n--- Pipeline test PASSED ---')
