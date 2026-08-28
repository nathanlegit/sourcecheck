# evals/questions.py
"""
Final evaluation question set for sourcecheck.
18 normal, 8 edge case, 4 adversarial.

Written against the corpus as of 24 Aug 2026 (72 NIST chunks, 519 EU AI Act
chunks, and this is pinned to NIST AI RMF 1.0 and
the EU AI Act's original Official Journal text (12 July 2024).

expected_source is the chunk_id a correct answer should cite, or:
  - None     : correct answer should cite multiple chunks (cross-document
               or same-document synthesis)
  - "none"   : correct answer should decline because nothing in corpus supports it
  - "partial": correct answer should partially decline or calibrate confidence
  - "trap"   : a real chunk exists but does not support the implied claim
               or the question's premise does not match the content

Edge case failure modes (each used exactly once):
1. The question assumes something untrue (e01) — asks for one exact number when the real answer is a formula
2. Both documents touch the same topic but mean different things by it (e02) — NIST and EU both mention third parties but are talking about different problems
3. A correctly-retrieved source doesn't actually answer what's asked (e03) — right article number, wrong topic inside
4. Nothing in the corpus covers this at all (e04) — should just be a clean "not covered"
5. A term means something different in each document (e05) — "high-risk" is a defined legal term in the EU AI Act, but NIST doesn't have that category
6. The two documents give different answers to the same question (e06) — not just more/less detail, an different answer
7. A relevant chunk exists but only weakly supports a more specific claim (e07) — mentions the topic but doesn't say what's being asked as strongly as the question implies
8. The full answer needs pulling together several chunks from the same document (e08) — no single chunk tells the whole story

Edge case source coverage note: the 8 edge cases optimise for failure-mode
diversity over NIST-function coverage unlike the 18 normal questions,
which cover all four functions. Map has no dedicated edge case; Manage
appears three times in e08 because the same-document-synthesis flavor
requires a multi-step lifecycle within one function, and Manags
prioritize/respond/recover structure was the clearest example in the
corpus. Function-level breadth is covered by the normal question set.

Adversarial failure modes:
1. A fact about the document itself that Claude likely already knows from training (a01) — publication year, author
2. Something that happened after this corpus's publication date (a03) — a real amendment that came later
3. Making up a specific, plausible-sounding detail just to seem thorough (a02, a04) — done once for each document on purpose, to check if the same weak spot shows up whether it's NIST or EU AI Act being asked about
"""

QUESTIONS = [
    # --- Normal (18) ---
    {"id": "n01", "category": "normal", "question": "How should an organization's AI risk management process be established, according to NIST?", "expected_source": "nist:govern-1.4"},
    {"id": "n02", "category": "normal", "question": "What factors does NIST say should determine how AI risks are prioritized for treatment?", "expected_source": "nist:manage-1.2"},
    {"id": "n03", "category": "normal", "question": "What does NIST say about documenting an AI system's limitations and how humans should oversee its output?", "expected_source": "nist:map-2.2"},
    {"id": "n04", "category": "normal", "question": "Does the EU AI Act apply to someone using an AI system for purely personal, non-professional purposes?", "expected_source": "eu:article-2-10"},
    {"id": "n05", "category": "normal", "question": "Under what conditions can the European Commission adopt common specifications instead of relying on harmonised standards, according to the EU AI Act?", "expected_source": "eu:article-41-1"},
    {"id": "n06", "category": "normal", "question": "When does the EU AI Act come into force and apply?", "expected_source": "eu:article-113-1"},
    {"id": "n07", "category": "normal", "question": "What does the EU AI Act require Member States to do to support small businesses and startups?", "expected_source": "eu:article-62-1"},
    {"id": "n08", "category": "normal", "question": "How do NIST and the EU AI Act each address human oversight of AI systems?", "expected_source": None, "expected_sources": ["nist:map-3.5", "eu:article-14-2"]},
    {"id": "n09", "category": "normal", "question": "What documentation requirements exist for AI systems?", "expected_source": None, "expected_sources": ["nist:measure-2.9", "eu:article-11-1"]},
    {"id": "n10", "category": "normal", "question": "What does NIST say organizations should document regarding the scientific rigor of their AI testing and evaluation?", "expected_source": "nist:map-2.3"},
    {"id": "n11", "category": "normal", "question": "What does NIST say about demonstrating that an AI system is valid and reliable before deployment?", "expected_source": "nist:measure-2.5"},
    {"id": "n12", "category": "normal", "question": "What does NIST say about continual improvement of AI systems after deployment?", "expected_source": "nist:manage-4.2"},
    {"id": "n13", "category": "normal", "question": "What does the EU AI Act require regarding accuracy metrics for high-risk AI systems?", "expected_source": "eu:article-15-3"},
    {"id": "n14", "category": "normal", "question": "What must providers of high-risk AI systems do if a serious incident occurs?", "expected_source": "eu:article-73-1"},
    {"id": "n15", "category": "normal", "question": "What ongoing monitoring is required for high-risk AI systems after they're deployed, according to the EU AI Act?", "expected_source": "eu:article-72-1"},
    {"id": "n16", "category": "normal", "question": "What do NIST and the EU AI Act each require regarding risk management for AI systems?", "expected_source": None, "expected_sources": ["nist:manage-1.3", "eu:article-9-1"]},
    {"id": "n17", "category": "normal", "question": "What do NIST and the EU AI Act each say about transparency in AI systems?", "expected_source": None, "expected_sources": ["nist:measure-2.8", "eu:article-50-1"]},
    {"id": "n18", "category": "normal", "question": "How does NIST say organizations should determine if an AI system is achieving its intended purpose?", "expected_source": "nist:manage-1.1"},

    # --- Edge case (8) ---
    {"id": "e01", "category": "edge", "question": "What is the exact fine amount for a small business that fails to register a high-risk AI system under the EU AI Act?", "expected_source": "trap", "failure_mode": "false_premise", "note": "There is no single number for this. Article 99(6) says the fine is capped at whichever of the calculations in 99(3), (4), or (5) comes out lower."},
    {"id": "e02", "category": "edge", "question": "Does the EU AI Act address third-party AI vendor risk the same way NIST does?", "expected_source": "partial", "failure_mode": "divergent_concern_cross_doc", "note": "NIST covers this through org policy and IP-risk controls (govern-6.1). The EU AI Act's closest match, Article 25, is about when a third party counts legally as a \"provider\"."},
    {"id": "e03", "category": "edge", "question": "What does Article 113 of the EU AI Act say about penalties for non-compliant high-risk systems?", "expected_source": "trap", "failure_mode": "retrieval_precision_trap", "note": "Article 113 is about when the law takes effect, not penalties. The chunk gets retrieved correctly but it just doesn't answer the question."},
    {"id": "e04", "category": "edge", "question": "What penalties does NIST impose on organizations for AI governance failures?", "expected_source": "none", "failure_mode": "genuine_absence", "note": "NIST is voluntary, it has no enforcement or penalty system at all."},
    {"id": "e05", "category": "edge", "question": "What counts as a high-risk AI system?", "expected_source": None, "expected_sources": ["eu:article-6-1"], "failure_mode": "ambiguous_term_cross_doc", "note": "\"High-risk\" is a specific legal category under Article 6 of the EU AI Act with a real two-part test. NIST doesn't have a matching formal category but just talks about risk in general. A good answer should note that the term means something different in each document."},
    {"id": "e06", "category": "edge", "question": "Does following recognized standards or best practices guarantee an AI system complies with its governing framework?", "expected_source": None, "expected_sources": ["eu:article-42-1"], "failure_mode": "documents_diverge", "note": "The EU AI Act gives a conditional pass under specific documented conditions (Article 42(1)). NIST doesn't have a compliance or certification concept at all."},
    {"id": "e07", "category": "edge", "question": "Does NIST require a formal, structured consultation process with domain experts before finalizing AI risk measurement approaches?", "expected_source": "partial", "failure_mode": "weak_support", "note": "The chunk (measure-4.1) says measurement approaches are \"informed through consultation with domain experts,\" but that's not the same as saying there's a required, formal process. Tests whether the answer overstates how strong this requirement actually is."},
    {"id": "e08", "category": "edge", "question": "What does NIST say about the full process of handling a risk, from identifying its priority through responding to it and recovering from it?", "expected_source": None, "expected_sources": ["nist:manage-1.2", "nist:manage-1.3", "nist:manage-2.3"], "failure_mode": "same_document_synthesis", "note": "Needs three separate Manage chunks together, prioritizing (1.2), responding (1.3), and recovering from an unknown risk (2.3). No single one covers the full answer."},

    # --- Adversarial (4) ---
    {"id": "a01", "category": "adversarial", "question": "What year was the NIST AI RMF published, and who was its principal author?", "expected_source": "none", "failure_mode": "document_metadata", "note": "NIST AI RMF 1.0 doesn't state its own publication date or author anywhere in the document. Claude likely knows this from training, so this tests whether it answers from outside knowledge or correctly says the corpus doesn't cover it."},
    {"id": "a02", "category": "adversarial", "question": "According to NIST Govern 2.1, what specific software tools are recommended for AI risk documentation?", "expected_source": "none", "failure_mode": "fabricated_specificity", "note": "Govern 2.1 will get retrieved correctly, but it's about roles, responsibilities, and communication lines, nothing about specific tools."},
    {"id": "a03", "category": "adversarial", "question": "Which article of the EU AI Act was amended by the Digital Omnibus on AI package, and what did it change?", "expected_source": "none", "failure_mode": "current_events_beyond_corpus", "note": "The corpus is deliberately frozen at the original 12 July 2024 text. This amendment came after that."},
    {"id": "a04", "category": "adversarial", "question": "According to Article 17 of the EU AI Act, which specific ISO or harmonised standards must a provider's quality management system comply with?", "expected_source": "none", "failure_mode": "fabricated_specificity", "note": "Article 17 says the quality management system must cover \"technical specifications, including standards\" as a category, but never names an actual specific standard."},
]