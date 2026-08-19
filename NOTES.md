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

## Wednesday 19 August

### Change of note format

I will be changing the format that I will be taking notes for this project into a prose format. I do think it is easier for me to write my thoughts down this way

### What got done 

Today we mainly focused on the ingestion of the NIST AI RMF framework. The framework has split into 4 main functions (Govern, Map, Measure and Manage), each with its own categories (Govern 1.1, Map 2.3 etc.). The goal is as such, to parse the document and store the data in a structured JSONL format with the statements, categories and metadata. 

We first built scripts/fetch.py. This serves as a simple script to call the HTTP protocol and retrieve the html data from the official NIST website. We use SHA256 hashing as a checksum to ensure that whichever document other users download from the site can be verified to be the same one that I am using for this project. 

The next logical step would be then to go on to build the parser. However, I chose to go for an inspection step first (script/inspect_nist.py), to see how the html was actually like before parsing. This was a good idea. There were many findings from the inpection (all data was stored in "th" headers and not "td" data, category cells use rowspan to span multiple rows) which guided the building of the parser. (carry the last seen category forward across rows, etc)

We then moved on to the actual parser (ingest/parse_nist.py). Had some help from Claude here as it was the first time I wrote parsing algorithm. My first attempt without Claude has a few real bugs such as a return statement sitting inside a loop. We took the learnings from the inspection as a guide when building the parser, and stored the data in a structured JSONL file. We chose JSONL as it allows for streaming without loding the whole file into memory, alongside other advantages. We also chose to have 2 different ids per record - a display id which retains what has been printed from the actual NIST document, and a chunk id, which is a normalised and standardised id version which makes storing of the data more systematic and prevents clashes, and prevents the issue of false positives due to formatting differences. 

We then wrote a validation step (ingest//validate_nist.py). This acts as a holistic check for the data (normalisation, function numbers, total record numbers, leaked html), and we validated the parsed data with this, returning no failures. We ended the session off with a manual check of 10 random samples to ensure the parsing was accurate. 

### Main learnings

I think the main lesson for me this session was to always inspect the data before building any parser. Different data structures and formats require differents kinds of considerations being taken into account when building a parser, and if you parse data without inspecting it you might waste time and effort having to rebuild one. Also to always validate the data after your parse it. The last thing you want is for the RAG chatbot to fail because of something wrong with the first step of ingestion. Getting ingestion right builds a strong foundation for the entire application. 











