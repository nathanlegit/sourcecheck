# Timeline and Notes

## Friday 14 August

### What got done

**Project scoping.** An evaluation harness measuring the groundedness of a RAG chatbot answering questions on international AI governance documents.

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

## Wednesday 19 August (Ingestion)

### Change of note format

I will be changing the format that I will be taking notes for this project into a prose format. I do think it is easier for me to write my thoughts down this way

### What got done 

Today we mainly focused on the ingestion of the NIST AI RMF framework. The framework has split into 4 main functions (Govern, Map, Measure and Manage), each with its own categories (Govern 1.1, Map 2.3 etc.). The goal is as such, to parse the document and store the data in a structured JSONL format with the statements, categories and metadata. 

We first built scripts/fetch.py. This serves as a simple script to call the HTTP protocol and retrieve the html data from the official NIST website. We use SHA256 hashing as a checksum to ensure that whichever document other users download from the site can be verified to be the same one that I am using for this project. 

The next logical step would be then to go on to build the parser. However, I chose to go for an inspection step first (script/inspect_nist.py), to see how the html was actually like before parsing. This was a good idea. There were many findings from the inpection (all data was stored in "th" headers and not "td" data, category cells use rowspan to span multiple rows) which guided the building of the parser. (carry the last seen category forward across rows, etc)

We then moved on to the actual parser (ingest/parse_nist.py). Had some help from Claude here as it was the first time I wrote parsing algorithm. My first attempt without Claude has a few real bugs such as a return statement sitting inside a loop. We took the learnings from the inspection as a guide when building the parser, and stored the data in a structured JSONL file. We chose JSONL as it allows for streaming without loding the whole file into memory, alongside other advantages. We also chose to have 2 different ids per record - a display id which retains what has been printed from the actual NIST document, and a chunk id, which is a normalised and standardised id version which makes storing of the data more systematic and prevents clashes, and prevents the issue of false positives due to formatting differences. We chose to differentiate embed_text from text, where embed_text has its parent category prepended to give the embedding model more to work with. We do not display this richer version as it creates noise that confuses the scorer. Chunking naturally was by subcategory, as this is NIST's citable unit.  

We then wrote a validation step (ingest//validate_nist.py). This acts as a holistic check for the data (normalisation, function numbers, total record numbers, leaked html), and we validated the parsed data with this, returning no failures. We ended the session off with a manual check of 10 random samples to ensure the parsing was accurate. 

### Main learnings

I think the main lesson for me this session was to always inspect the data before building any parser. Different data structures and formats require differents kinds of considerations being taken into account when building a parser, and if you parse data without inspecting it you might waste time and effort having to rebuild one. Also to always validate the data after your parse it. The last thing you want is for the RAG chatbot to fail because of something wrong with the first step of ingestion. Getting ingestion right builds a strong foundation for the entire application. 

## Wednesday 19 August (Retrieval)

### What got done

As a follow up on the previous session having parsed the NIST data, I focused on embedding the data, and querying the data to ensure that the retrieval pipeline was working well. I chose to do this first over parsing the EU AI Act as I wanted to focus on getting the whole pipeline working before confusing myself with more data. 

Building the embedding script (ingest/embed_nist), I chose to go with ChromaDB as the vector database, and using Chroma's default embedding model, MiniLM, which converts each chunk in the data into a 384-dimension vector which is stored in the collection "governance docs" Today was also spent mostly understanding how embedding and retrieval actually works (i.e. the math behind it). A decision to use Chroma's persistent mode was made, the obvious choice as we would need persistent storage of the vectors across sessions. Metadata was also stored with the vectors to be retrieved for scoring and display. 

I then moved on to the query script (ingest/query_nist) which main function was to take a plain-english question and use the same embedding model to convert that plan english query into embeddings, to make retrival through cosine similarity possible. (Chroma's distance field displays distance = 1 - cosine_similarity, so lower distance is more similar) I then tested the retrival pipeline, and discovered a siginificant issue. (read more in RESULTS.MD Embedding strategy: category-prepending experiment, 19 Aug 2026). The short of it is that the original decision I made to prepend every subcategory with the parent categroy turned out to backfire, as it introduced noise which affected the precision of retrival. After doing a simple experiment, I decided to remove the prepending, and embed 'text' instead of 'embed_text" in the embed_nist. (A quick look at the results: before: 1.16, essentially tied for rank 1; after: 0.82, clear rank 1 with 0.4 separation.) Evidence can still be seen where I parse out the category 'embed_text' in the parser, so that readrs know this experiement was real.

### Main Learnings

Design decisions can be wrong. And thats why, every decision will have to be tested. In theory, prepending the category to each subcategory sounded good, giving the embedding model more to work with which can result in better retrieval, but it turns out to be wrong, and as such, developers will need to be adaptable, and always willing to run these small experiements to ensure desicions made has been backed by real-life evidence. And to always be open to admitting ones deicions was wrong, and pivoting because of it. 

Apart from that, many learnings on how embeddings actually works under the hood. 

## Thursday 20 August

#### What got done. 

Today, we focused on building the foundations for the two agent architecture (agents/retriever and agents/answerer)

After setting up a claude console account, we built the retriever.py script, which was essentially the query_nist.py script we wrote yesterday, but instead of printing out the chunk, we save the chunks into a list and return these chunks. This is neccessary to allow us to pass these chunks onto the answerer agent which can then use the chunks to generate a grounded response. 

We then moved on to the answerer agent. The script was simple, just a few functions to concantenate the question and retrieved chunks, and the call the Anthropic client to generate an output with the Claude Sonnet model. We went with sonnet as a reasonable default.  

The main part of today was engineering the prompt. The main consideration that we built this prompt with was to ensure that hthe answerer was generating responses that were fully grounded in the retrieved chunks, and not from its own knowledge that it gained from its training. We also wanted to ensure that the answere cited the sources in a specific format. We first engineered the structure of the prompt (Role, Task, What not to do, and examples), and used negative prompting as a technique to reinforce what the model cannot do. We also used the technique of few-shot promting, giving the model 3 examples (one covering outside knowledge leakage, one on missing citations, and the last on partial-information questions) and the correct answer for each example. 

We ended the day off with a small experiment on the answerer agent. (See RESULTS.MD Answerer prompt validation, 20 Aug 2026 for more details). In a nutshell, we gave the answerer 4 prompts, increasing in difficulty, (a straightforward grounded question, a near-duplicate of the prompt's own outside knowledge example, a differently-framed outside knowledge trap not modelled in any example, and a compound question where only half was answerable from the corpus.) and we observed that the answerer passed all 4 tests. 

### Main Learnings

Prompt. Prompt. Prompt. It is arguably one of the most important things in an Agent. Writing a well structured prompt utilising good prompt engineering techniques will save you alot of time debugging down the line and help guide the model towards the desired behaviour. A bad prompt, no matter how complex, or powerful the model is, will cause results to be suboptimal, as the bullseye for the model is misaligned with that of your use case in the first place. 











