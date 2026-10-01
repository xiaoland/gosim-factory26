# Static Semantic Lookup Research

## Finding

A static search index can be very small, but an actual vector search also needs a query encoder. Precomputed document vectors alone cannot embed a new query into the same space. Therefore the delivered semantic capability is always at least two artifacts:

```text
canonical SVC corpus
    -> build-time chunking + document embeddings
    -> quantized vector index + metadata

local query encoder
    + query text
    -> query vector
    -> local similarity ranking
```

This is the relevant distinction between static-blog full-text search and local vector search.

## Evidence

- [Pagefind](https://pagefind.app/) demonstrates that a static, chunked full-text index can stay small and operate without hosted infrastructure. It is an excellent model for deterministic keyword lookup, but it is not a vector encoder.
- [USearch](https://github.com/unum-cloud/usearch) can serialize/load a vector index, memory-map it, and store vectors in lower-precision formats. Its own documentation notes that exact search is appropriate for small collections; this makes a separate ANN graph unlikely to earn its complexity for an SVC corpus.
- [Sentence Transformers StaticEmbedding](https://www.sbert.net/docs/package_reference/sentence_transformer/modules.html) uses a mean of precomputed token embeddings. It is CPU-friendly but its documentation explicitly notes that static embeddings cannot capture all contextual semantics because token vectors are computed independently.
- [Model2Vec](https://github.com/MinishLab/model2vec) is a candidate for static, local embeddings; it advertises smaller quantized models and multilingual support. The actual quality, license, model size, and Chinese-to-English retrieval behavior must be measured rather than assumed.

## Candidate Designs

| Design | Runtime artifacts | Strength | Cost / risk |
| --- | --- | --- | --- |
| Static full-text only | Catalog + inverted index | Very small, deterministic, no model | Not semantic vector retrieval |
| Static embeddings + exact cosine | Static query model + quantized corpus vectors + metadata | Fully local; simple for small corpus; no vector DB | Model footprint and contextual quality require evaluation |
| Static embeddings + ANN/HNSW | Query model + vectors + graph index | Useful at large corpus scale | Extra native dependency and index complexity; unlikely to pay for SVC's size |
| Local model service | Corpus vectors + local provider adapter | May use a user's existing embedding model | Service availability and provider boundary become a dependency |
| Remote embedding API | Corpus vectors + API credential | Small wheel | Violates default-local/privacy posture unless separately authorized |

## Recommended Prototype

1. Define a fixed bilingual evaluation set: English and Chinese queries against expected SVC path/section results.
2. Segment the current corpus by heading rather than whole document, preserving the source path and anchor as result identity.
3. Build a static-embedding candidate at release build time, quantize corpus vectors, and use exact cosine ranking in Python.
4. Measure wheel/semantic-pack bytes, cold and warm query latency, memory, result recall@k, and cross-language failures against keyword search.
5. Select main-wheel bundle, explicit semantic pack, or optional extra only from those measurements.

## Non-negotiable Contract

`svc lookup --semantic` never silently downloads a model, starts a service, or transmits a query. If the approved local semantic artifacts are absent, it emits a stable `semantic-capability-unavailable` result that directs the user to explicit installation or to `--keyword`.
