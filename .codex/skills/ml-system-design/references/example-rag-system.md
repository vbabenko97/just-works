> Source: [ML-SystemDesign/MLSystemDesign](https://github.com/ML-SystemDesign/MLSystemDesign), MIT License. Distilled and rewritten, not verbatim. Content follows the source design doc; sections are rearranged to `genai-template.md`, and notes mark what the source does not cover.

# Worked Example: RAG Chat With Document Versions
Q&A system over versioned documents (Markdown and scanned images) on a collaborative platform,
supporting content queries, version-diff questions, and multi-document retrieval.
Maturity: POC
Template: GenAI. Critical components: OCR, embeddings, retrieval, and LLM generation; OCR, embeddings,
and the LLM are vendor services, and no model is trained in this POC.

## I. Problem Definition

MagicSharepoint is a collaborative document platform with ~1000 unique users per month, ~500 document
versions assigned per month, and documents up to 500 pages (Markdown or scanned images). Current flow:
clients must read through documents or use full-text search to answer questions; domain expertise is
required; answers are not reused across users. Previous work: BM25-based smart full-text search and a
Mechanical Turk answer catalog for frequent questions. Goal: chat interface that answers questions about
document content and version changes faster than manual proofreading. Addressable use cases: specific
content questions, version-change questions, multi-document and multi-version comparisons.
Non-addressable (must decline): irrelevant questions and questions about content not in the documents.
Unacceptable failures: level-1 mismatching (fact not present in the documents) and level-2 mismatching
(fact present but miscontextualized); incorrect answers that look confident are worse than explicit
refusals. Human in the loop: the system asks the user to clarify when it is uncertain and answers "I
cannot answer from the given documents" for out-of-scope questions.

## II. Metrics and Acceptance Criteria

Acceptance criteria from the client: first token within 1 minute; at least 95% of answers free of
level-1 and level-2 mismatching. The pipeline decomposes into independent subtasks — OCR, intent
classification, retrieval, and generation — each evaluated separately to isolate error sources. OCR
metrics: Word Error Rate (WER, lower is better), Formula Error Rate (percentage of incorrectly OCR'd
formulas), and Cell Error Rate (percentage of incorrectly detected table cells). Intent classification
metrics: Precision, Recall, and F1 (macro and per-class) over all intent labels. Retrieval metrics:
Recall@k (fraction of relevant chunks returned in the top k) and NDCG (normalized discounted cumulative
gain). Generation metrics: Average
Relevance Score (automated via RAGAS or LLM-as-judge, or via crowdsourcing), Hallucination Rate
(percentage of answers containing fabricated content), and Clarification Capability (average follow-up
questions needed per query). Online metrics: Average Relevance Score, average number of clarification
questions, and average dialogue duration. Evaluation approach: start from top-level quality metrics and
drill into component metrics only when needed to explain drops.
Note: the source sets no cost-per-request target; a production doc adds one.

## III. Data and Knowledge Sources

The vendor LLM's training data is not controlled. The RAG corpus is the platform's documents. Permission
model: all clients share one document namespace with no per-role access restrictions, so retrieval needs
no per-user filter; a deployment with restricted documents would need permission filtering at query time.
Documents are either Markdown (up to 500 pages, with tables, formulas, headings) or scanned images. Each
document may have multiple versions (v1, v2, …). Version metadata per document: version number, editor,
change date, and diff if available. For documents edited on-platform, both the diff and the new version
are known. For uploaded documents, only the new version is available — a diff-generation step is required
and diffs are treated as first-class documents. Cleaning is automated and run once per upload or version
change, with outputs stored in a separate cleaned_data directory to preserve originals. OCR is applied to
image-format documents; both the original scan and extracted text are stored. Chunking: four levels
(document, article, paragraph, sentence); oversized chunks split into overlapping sub-chunks (20% overlap)
or replaced by generated summaries. Enrichment: embeddings, inter-document link resolution to section
names, table-of-contents extraction, named entity recognition, and per-level summaries stored as metadata.
Note: the source does not state how deleted documents leave the index or what the LLM vendor retains.

## IV. Evaluation Set and Validation Schema

Validation dataset generated using RAGAS from actual platform documents. Each sample contains: a question,
the relevant context chunk(s), and an expected answer. Multi-faceted question generation: automated NLP
(T5 or BART fine-tuned for question generation), human SME curation of auto-generated questions and
creation of edge cases, and mining of anonymized real user queries from logs. Question types: factual,
inferential, comparative (version-to-version), multi-document, and version-specific. Negative examples
(unanswerable questions) are deliberately included to test refusal capability. Stratified sampling by
document length (short/medium/long), document type (text vs scan), topic area, and query complexity.
Validation set is updated monthly or when a significant influx of new documents occurs. Retrieval is
scored with its own metrics (Recall@k, NDCG) before generation. Leakage prevention: validation questions
are drawn from documents already in the corpus at validation time; no future-document content bleeds into
the validation set. A single offline evaluation pass is sufficient for POC.
Note: the source has no prompt-injection cases (instructions planted in a document) and no repeated
runs; a production doc adds both.

## V. Baseline and Adaptation Path

Document extraction baseline: supports .txt/.doc/.pdf only (no OCR) to limit first-iteration scope;
includes format reader, Markdown formatting normalization, and error/spell-check logging. Retrieval
baseline (sparse, no LLM): BM25 with preprocessing (tokenize, filter irrelevant content, stem/lemmatize),
TF-IDF index with parallelized scoring, and a top-k result display with explicit user feedback ("Have you
found what you were looking for?"). This baseline handles the source's addressable use case 1a and
explicitly rejects non-addressable use cases 1na and 2na. Escalation path: (1) Basic — raw LLM generation from
retrieved context; (2) Reliable — adds input, dialogue, retrieval, and output guardrails with retry logic
and a fallback to a secondary LLM; (3) Reliable + Interactive — adds dialogue context management and
automatic clarification requests when context is insufficient. LlamaIndex chosen over LangChain:
retrieval-first design, easier setup and maintenance, built-in indexing, and support for both local and
vendor-based LLMs. Embedding baseline starts at paragraph level since most answers are answerable within
a single paragraph. Model training: none; OCR (AWS Textract), embeddings (BERT-based model via vendor API),
and the LLM (OpenAI or Azure OpenAI) are vendor services. Revisit if vendor capabilities prove
insufficient or customised or on-premise models are required.

## VI. Error Analysis

Error sources per pipeline stage. Intent classification: under-filtering runs the full pipeline on
irrelevant queries wastefully; over-filtering blocks valid queries with no response. Embeddings: poor
embedding quality caused by domain-specific vocabulary not in pretraining data; embedding drift as
domain-specific documents accumulate over time. Retrieval: irrelevant chunks returned despite good
embeddings; stale index when new document versions are not re-embedded promptly. Generation: model
hallucinations (fabricated plausible-looking content) and failure to recognize when context does not
contain sufficient information. Guardrails: under-filtering allows harmful or out-of-scope output
through; over-filtering blocks correct, useful answers. Diagnostic approach: isolate and test each
component independently before end-to-end evaluation; trace a query step-by-step through the pipeline
to identify the first stage where behavior deviates from expected. Corner cases from the validation
schema include: questions about rare document types, documents near the 500-page limit, questions
spanning many versions, and explicitly unanswerable questions.

## VII. Development and Release Pipeline

The pipeline keeps document preprocessing stable on every submission and context selection stable for
prompt construction. Tools: Python, cloud vector DB (Pinecone or Azure AI Search), cloud OCR service,
Docker, and a cloud LLM service. Preprocessing steps: OCR for image documents, text metadata extraction,
enrichment at chunk levels, preprocessing metadata storage (script versions, timing), and storage of
enrichment results in the vector DB. SLA for preprocessing: a document is fully processed within 1–2 hours
of upload. Evaluations use RAGAS for context, prompt, and end-to-end quality. CI/CD runs the evaluation
on each release and pulls the latest documents first.
Note: the source records preprocessing script versions but not prompt or model versions, and it sets no
evaluation threshold that blocks a release.

## VIII. Context, Retrieval, and Tools

Context assembly: intent classification labels the query, vector search retrieves chunks with metadata
filtering (embeddings database requirements are in X), and the prompt template for that intent assembles
the prompt.
Criteria for context features: flexibility (support varied question types), relevance (selected context
must match the question), and computational time (enrichment may lag by several hours, but 500-page
documents make some of it expensive). New context features are proposed as hypotheses tied to specific
corner cases or metric deficits — no automated selection (no RFE). Four levels: (1) Document-level — metadata
(title, author, creation date, version history) used for document filtering and implicit document
identification in chat; (2) Text-level — metadata statistics, enrichment (NER, entity extraction,
inter-document link resolution, table of contents), and embeddings for vector retrieval; (3) Token-level
— further context narrowing and domain-specific entity tagging; (4) Prompt templates — components for
agent role and knowledge, task, output format, output restrictions, input metadata context, input
document context, inter-document relations, and optional few-shot examples. Prompt templates cover all
intent types: general domain, addressable, non-addressable, single document, multiple documents, single
document across versions, and multiple documents across versions. From the Reliable level in V,
guardrails run on input, dialogue, retrieval, and output. Tools: none — the system only reads the corpus
and changes no state.

## IX. Measuring and Reporting

Note: the source plans a full A/B test despite POC maturity; under this skill's POC rule this subsection
would read "Deferred until production."

Offline evaluation uses crowdsourcing (Yandex Toloka or Mechanical Turk): 100 assessors, 1000 query-
answer pairs (500 direct questions, 500 follow-up questions), overlap of 5 assessors per task, cost
approximately $50. Assessors score on a 5-point relevance scale and provide a binary hallucination flag
(Yes/No). Metrics collected: Average Relevance Score for direct questions, Average Relevance Score for
follow-up questions, and Hallucination Rate. A/B test primary hypothesis: system enhancements increase
user retention rate. Secondary hypothesis: enhancements increase subscription conversion rate. Termination
criteria: pause if average response time exceeds 1.5 minutes or offensive response rate exceeds 1%.
Key A/B metrics: User Retention Rate and Subscription Conversion Rate. Control metrics: positive and
negative feedback rates, reading efficiency differential (RAG time vs traditional retrieval time), TTR,
correction attempts rate, and graceful exits rate. Split strategy: by user ID. Duration: 4 months with
group swap at 2 months to mitigate bias from variable user experience. Statistical test: Welch's t-test,
5% significance, 10% type II error.

## X. Integration

The full pipeline architecture (user query through intent classification, vector search, prompt assembly,
LLM generation, guardrail evaluation, and response delivery) is the target integration design. Embeddings
database: cloud vector DB (e.g., Pinecone) storing vector representations of all document versions plus
chat history; must return top-10 nearest neighbors within 100ms for up to 1M vectors, support 1000 QPS,
cosine/Euclidean similarity, and metadata filtering; embeddings and metadata are encrypted. Document
storage: cloud object store (e.g., AWS S3), stores original files and OCR-extracted text, returns URL
used as document ID. Chat UI: React.js frontend, Socket.io for real-time streaming, positive/negative
feedback collection, abuse reporting, and chat history persistence. OCR: AWS Textract, triggered
automatically for image uploads, multi-language support, both original scan and extracted text stored.
Backend API groups: document management (upload, delete, retrieve versions), query management (retrieve
result, rate, report), embedding management (generate/update on version change), and chat session
management (start, end, save history). Async task queue (Celery + RabbitMQ) for embedding generation;
reserved workers for real-time chat sessions. Primary fallback: vendor LLM; secondary fallback: local
Hugging Face model, activated on latency violation or negative feedback threshold.

## XI. Monitoring

Engineering monitoring: Prometheus + Grafana for system health metrics, alerting, and ingestion-layer
timings; Langfuse callback (integrated with LlamaIndex) for LLM cost, latency, token volume, and user
feedback (explicit ratings and implicit signals); Sentry for code error tracking. Ingestion layer: log
process and I/O timings, code errors, and document statistics (word count, character distribution,
paragraph length, detected languages, table/image percentage); OCR pipeline logged separately. Retrieval:
log query details (tokenizer used, document context and version found, metadata), similarity scores,
and index IDs returned. Chat history: all sessions stored for analysis and debugging. Generation: quality
tracked via user feedback ratings. Alerting on anomalies or threshold breaches across all layers.
Note: the source contains TODO markers: per-system metric thresholds and main metrics for each component
are not yet finalized at POC stage, and no owners are named.

## XII. Serving and Inference

Note: optimization details below are illustrative; a POC doc under this skill's rule defers them until production.

Three on-premise services communicating with external cloud services: Embedding service, OCR service, and
Chat service on-premise, with Vector DB (Pinecone), Document Storage (S3), Metadata DB, and LLM as
external cloud dependencies. Embedding service: Docker container on GPU node, triggered on each new
document version; invokes OCR service if image-based, pulls text from Document Storage, generates
embeddings at multiple chunk levels (document to sentence), imports embeddings and metadata to Vector DB.
OCR service: Docker container on GPU node, invoked by Embedding service; runs AWS Textract, imports
extracted text to Document Storage. Chat service: Docker container on non-GPU node (RAM-intensive,
minimum 4 GB RAM); handles intent classification, vector context search, prompt assembly, LLM invocation,
guardrail evaluation, Redis-based caching for identical scope+history+question combinations, and chat
history persistence. Load balancer routes requests and starts/stops Embedding and OCR services on demand;
services stop after 30 minutes idle. Embedding and OCR services run on spot instances given ~500
versions/month volume. Inference monitoring: time to full response, cache hit rate, guardrail rejection
rate, clarification request rate, empty context rate, explicit "cannot answer" rate, and average chat
history length.
