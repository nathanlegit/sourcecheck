## Corpus Validation, 18 August 2026

NIST AI RMF 1.0 Core: 72/72 subcategories has been parsed and structurally validated matching the expected counts of the subcatgeories. 10 -record random sample has also been manually taken and checked against the document, no discrepancies found. 

## Embedding strategy: category-prepending experiment, 19 Aug 2026

Context: we originally build the parser to have two different content texts: embed_text and text. The original thought process was that prepending the subcategory with the category would give the embedding model more to work with, resulting in a more contextually accurate embedding and improve retrieval. However, preliminary tests on query_nist proved otehrwise. I then decided to do a test to decide if we should still go with this modality. 

Test: embedded once with `embed_text` (category + statement),
queried with the paraphrased question "What does NIST say about legal and regulatory requirements?" against a corpus where Govern 1.1 is the correct answer.

Result: Govern 1.1 ranked 2nd, distance 1.1609, whih was essentially tied with an unrelated chunk (Govern 6.1, distance 1.1601). A sanity check querying with Govern 1.1's own exact text returned distance 0.5361 against itself, not near 0, indicating the shared category preamble was diluting every chunk under Govern 1 toward its siblings rather
than sharpening individual matches.

Reversed: re-embedded using bare `text` (statement only, no
prepended category). Re-ran the same paraphrased question:
Govern 1.1 now ranks 1st, distance 0.8206, with clear separation from the next result (Map 1.6, distance 1.1958, a gap of 0.375). 

Conclusion: for chunks this short and already well-defined (single sentence per subcategory), category-prepending hurt precision more than it helped recall.  `embed_text`
field will be kept in the parsed corpus as a record of the design tried, but will not be used for embedding.