## Corpus Validation, 18 August 2026

NIST AI RMF 1.0 Core: 72/72 subcategories has been parsed and structurally validated matching the expected counts of the subcatgeories. 10 -record random sample has also been manually taken and checked against the document, no discrepancies found. 

## Embedding strategy for NIST: category-prepending experiment, 19 Aug 2026

Context: we originally build the parser to have two different content texts: embed_text and text. The original thought process was that prepending the subcategory with the category would give the embedding model more to work with, resulting in a more contextually accurate embedding and improve retrieval. However, preliminary tests on query_nist proved otehrwise. I then decided to do a test to decide if we should still go with this modality. 

Test: embedded once with `embed_text` (category + statement),
queried with the paraphrased question "What does NIST say about legal and regulatory requirements?" against a corpus where Govern 1.1 is the correct answer.

Result: Govern 1.1 ranked 2nd, distance 1.1609, which was essentially tied with an unrelated chunk (Govern 6.1, distance 1.1601). A sanity check querying with Govern 1.1's own exact text returned distance 0.5361 against itself, not near 0, indicating the shared category preamble was diluting every chunk under Govern 1 toward its siblings rather
than sharpening individual matches.

Reversed: re-embedded using bare `text` (statement only, no
prepended category). Re-ran the same paraphrased question:
Govern 1.1 now ranks 1st, distance 0.8206, with clear separation from the next result (Map 1.6, distance 1.1958, a gap of 0.375). Extra sanity check questions were run, all with the same result. 

Conclusion: for chunks this short and already well-defined (single sentence per subcategory), category-prepending hurt precision more than it helped recall.  `embed_text`
field will be kept in the parsed corpus as a record of the design tried, but will not be used for embedding.

## Answerer prompt validation, 20 Aug 2026

I tested the answerer's grounding constraint with 4 questions:
1. Direct question with a clear answer in the corpus
2. Near-duplicate of the few-shot example in the prompt (outside-knowledge trap)
3. Differently-framed (phrasing) outside-knowledge question (year of publication + signatory)
4. Compound question where one half is answerable and one half is not

All 4 were handled correctly: citations in [Display ID] format matching retrieved chunks, correct refusal on both outside-knowledge traps, and correct partial-answer splitting on the compound question. The result from last 2 questions were the most informative, as it taught us the rule actually generalised rather than the model simply pattern matching the prompts worked examples back. 

This is however a small test with sample size of 4. more testing will defintely have to be done, but this is just a preliminary test. 

## EU AI Act chunking strategy, 22 Aug 2026

Inspected Articles 1, 2, and 14 to determine chunk granularity before parsing. Confirmed structure is consistent across all three: every numbered clause (1., 2., 3. ...) and every lettered sub-point ((a), (b) ...)
renders as a separate <p> tag, with sub-points always nested directly under their parent numbered clause.

Considered three granularities:
- Article-level (one chunk per Article): rejected due to  insufficient precision. E.g. Article 2 alone has 12 numbered clauses, and citing "Article 2" would give no way to verify a specific claim against the correct sub-text.
- Sub-point-level (separate chunks for each numbered clause AND each lettered sub-point): rejected as it adds uneccessary complexity for citation granularity that is rare in reality, as most citations reference a numbered clause ("Article 14(3)"), not to the sub-point level
- *Numbered-clause-level* (one chunk per numbered clause): this was chosen. It Matches typical real-world citation granularity and keeps the parser's complexity proportionate to the time available.

## EU AI Act parsing, 24 August

Parsed 113 articles into 519 numbered clauses, with letter sub points folded into parent clause

Initial parse poduced 500 records but validation caught 19 articles contirubuting 0 records. Found out that the cause is these articles contained no numbered clauses at all, as the parse we designed parsed based on these numbers. Fix: added a fallback so that if a article paragraphs do not match the numbered clauses format, we treat the whole article as a single chunk and parse it successfully. After the fix, records increased to 519, and validation passed. 

## Cross-corpus retrieval validation, 24 Aug 2026

Merged NIST (72 chunks) and EU AI Act (519 chunks) into a single Chroma collection. We confirmed cross-document retrieval works: a
question specifically about EU AI Act human oversight correctly surfaced Article 14(2), the Human Oversight provision, at rank 2 (distance 0.5105), alongside Article 26(11) on related deployer obligations at rank 1. We also confirmed that the retrieval of NIST data is unaffected by the merge: the NIST legal-requirements question still returns Govern 1.1 at rank 1, distance 0.8206, identical to the single-corpus result from 19 Aug. 
