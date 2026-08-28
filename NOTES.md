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

## Sat 22 Aug - Mon 24 Aug

### What got done
This was a long session. We started out with the parsing of the EU AI Act, which was a data source that I wanted to add to diversify the use case of sourcecheck. We quickly ran into a wall, as bot-detection on the html site of the original EU AI Act (EUR-Lex) blocked us from directly downloading the content like I did for the NIST data. I chose to then go for another site (artificialintelligenceact.eu) to pull the data from after doing a check that the data on this site matched the 2024 version of the EU AI Act. (through a verification of the operative text on the site against an independent EUR/Lex snippet obtained seperately)

The problem was, that the data on this site was split into articles, which each article having its own distinct url. The fetch script had to be rebuilt to account for this (fetch_eu.py). We also added headers to prevent detection from any anti-bot protocols the site may have

After downloading all 113 articles from the site, we had to inspect the html, like what we did for the NIST data. We found that every page followed a similar layout (Top bar, Summary (with an AI generated summary), Suitable Recitals, and the footer). The actual legal text lived between the summary header and the suitable recitals header. This was done through inspect_eu_macro.py.

We realised we had to go one step deeper and find out what exactly lived between these headers. That was why we wrote inspect_eu_micro.py, and found out the legal text has a constant tag, and each point (regardless of whether it is a numbered point or a sub point) was wrapped in a distinct <p>
tag. 

We then finalised the chunking strategy to chunk based on numbered points, as we believed this is the sweet spot between too little granularity (chunking based on articles) and uneccessary granularity (chunking based on sub-points) which was not practiced in real-life. 

### Main Learnings

Do not assume every data source you try to access is nice to you. Some sites have anti-bot protocols that you will have to find alternatives to still get the data you require. This was a real blocker for us, as we spent a lot of time reconsidering how to retrive the data, and had to do a more detailed inspection (2 python scripts) to get to writing the parser. 


## Mon 24 Aug - EU AI Act parser and validation

### What got done

We built the parser for the EU AI Act based on the findings that we got from the inspection. The parser was that was built had to be different from the one for NIST, due to the different in modality and format that the EU AI Act data was in. This resulted in an interesting way to write the parser function, which included a flush function inside the main parser function that appended a clause to the list of record once all the sub points has been appended to the main clause. (parse_eu.py)

We then built a validator (validate_eu.py) based on the same principles that we used to validate the NIST data. However, once we ran the validation, we realised that there were 13 articles that did no have any clauses parsed out of them. Upon further inspection, we realised that the content in these articles did not have the numbered clauses, which was what we were parsing for in the original version of the parser. We were hence unable to retrieve any content from these articles.

We edited the parser to include a fallback if no numbered clauses was found, to append the content directly into the list of records. After the fix and running the validation script, all checks passed without any issues.

Using the same embedding script with minimal changes, we embedded the EU AI Act data and tested the retrieval system to see if the EU AI Act data was embedded properly. The test results were positive (see ## Cross-corpus retrieval validation, 24 Aug 2026 in RESULTS.md). we also edited the buil_user_prompt function in the answerer agent script to include the document the data was taken from to reduce ambuigity. 

### Main learnings

Nothing much from this excercise. The way we write the parser function was interesting though, and logic is something to keep in mind as we proceed further on. 

## Tues 25 Aug - 30 test questions

### What got done

We have built out the RAG system. Now, we move on to the 30 test question suite that we will be consistently testing the system on, so this grows into the foundation of the project. 

The split that we decided for the 30 questions is as such: 18 normal, 8 edge case, and 4 adversarial. Normal questions refer to actual questions that a query will be be, refering real information in different articles/statements and asking direct questions from it. Edge case tets the judgement of the model via expliting ambuigity or gaps. Adverserial are questions that a deisgned traps. The split was decided because: normal is of the highest, because they are the bread and butter of the testing of the system, and they are also the denominator for your false positive rate. Edge cases are 8, as this is enough to cover the real categories of ambuigity. And adversarial is the lowest, as we didnt want to give redundant bait to the system. 

We first work on the 18 normal questions. We decided to go with a stratified random sampling of articles/statements from EU AI act and NIST, of which we will read through and decide which ones are suitable to generate the questions from. The stratified random sampling script is at evals/stratify_testqns.py. We made sure to ensure coverage of the whole corpus and a range of question from direct ones (specifying the source) to open ones (where the model has to reference both sources and generate an answer from there)

We then moved on to the adversarial questions, which were meant to bait the system. I eventually settles on 3 failure modes: Document metadata Claude plausibly knows, Current-events knowledge that postdates/exceeds the pinned corpus, and Fabricating specificity (invents a plausible number/detail with no real training-knowledge basis, just pattern-completion pressure), and mapped the differect question to these evenly with the diversity of sources in mind as well. 

Same was done for edge cases, you can see the full failure modes in the questions.py file. 

### Main Learnings

This was a long one, especially since this was my first time doing a evaluation question set. We spent a long time trying to figure out and architect what the various failure modes are, searching for relevant conetent in the corpus that allowed me to test this fialure mode then crafting the questions in a way that tested the failure modes. mapping the questions to not only failure modes but also corpus sources to ensure coverage of both the NIST framework and the EU AI Act was something that was challenging as well. 

However, this is the foundation of the entire project, so it had to be done correctly. 


