# Timeline and Notes

## Friday 14 August

### What got done

**Project scoping.** An evaluation harness measuring the groundedness of a
RAG chatbot answering questions on international AI governance documents.

Architecture: I decided to go with a 2 agent architecture: A retriever searches the vector store and returns
top-k chunks with source metadata, and the answerer takes the question and chunks, producing an answer with inline citations, explicitly barred
from answering from parametric memory. I decided to split them so that retrieval failure
and generation failure are separately diagnosable.

Evaluation layers:
1. Deterministic scorers. Citation existence (does the cited ID exist in the
   corpus?) and citation groundedness (does the chunk contain what the answer
   claims?).
2. LLM judges. A groundedness judge and a quality judge for the paraphrasing that the deterministic matching cannot capture.
3. Judge validation. 50 system-generated answers hand-labelled by me run on the judge. The agreement is reported per judge as Cohen's kappa plus raw percentage. 
4. Variance. Every test case run 3 to 5 times and the mean and standard deviation
   reported.

Deployment layers: a runtime guardrail blocking or flagging answers that cite
nonexistent IDs with both catch rate and false-positive rate reported, and a
CI gate running the deterministic suite on every push which failing the build if
groundedness drops past a threshold from a committed baseline.

**Repo setup.** Public repo `sourcecheck`, 
uv with Python 3.12, chromadb for local vector storage, anthropic for
generation, pypdf and lxml for parsing, pytest and ruff for development. 

**First read of the corpus.**

| Document | Force | Structure | Role |
|---|---|---|---|
| NIST AI RMF 1.0 (US, 2023) | Voluntary | 4 functions, categories, 72 subcategories | Primary, fully scored |
| EU AI Act 2024/1689 (EU, 2024) | Binding, extraterritorial | Articles, Annexes, Recitals | Secondary, scored to article level |
| Singapore MAGF 2nd ed (2020) | Voluntary | Prose sections, no enumerable IDs | Retrieval only, unscored |

The three frameworks have different philosophies: outcome-based,
rule-based risk-tiered, and practice-based. This will defintely make the
harder eval questions interesting.

### Decisions made

1. **Singapore excluded from the scored set.** Its prose structure has no
   official enumerable IDs and inventing IDs to score against would mean
   fabricating the ground truth. Will be kept in
   retrieval for coverage.
2. **Second judge on a different model family (OpenAI).** Claude judging Claude produces correlated
   blind spots. Using GPT will decorrelate the failures. GPT will remain a groundedness judge only;
   the quality judge stays single-model, since cross-model disagreement on a
   subjective dimension mostly measures stylistic preference. 
3. **Corpus pinned to current versions as retrieved 14 Aug 2026.** The AIRC
   site carries a notice that AI RMF 1.0 is under revision. Pinning will keep
   published numbers reproducible if 2.0 ships mid-build.
4. **Local embeddings by default.** I have decided to use Chroma's built-in model rather than an
   OpenAI embedding key, so the repo runs on only one API key. 

### Findings

- NIST publishes all four Core tables as HTML on a single AIRC page:
  `https://airc.nist.gov/airmf-resources/airmf/5-sec-core/`. No PDF table
  extraction is needed for the Core. 
- NIST ID format is `Govern 1.1`.
  Ingest needs a normalisation rule and the matcher needs to be
  case-insensitive and hyphen-tolerant.
- Subcategory counts: Govern 19, Map 18, Measure 22, Manage 13. Total 72.
  This is small enough to eyeball every parsed chunk for correctness.
- Statement lengths vary considerably. Govern 1.1 is one short sentence, while
  Map 1.1 runs several clauses with an embedded list. Chunk sizes will be
  uneven, and this will affect decisions like prepending along the way. 

  


