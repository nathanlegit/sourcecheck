# Corpus provenance

The ource documents are not redistributed in this repository. Run `uv run python scripts/fetch.py` to download them.

Checksums below pin the exact versions that the published results were produced with. A mismatch means that the source document has changed.

| File | URL | Retrieved | SHA-256 |
|---|---|---|---|
| nist_core.html | https://airc.nist.gov/airmf-resources/airmf/5-sec-core/ | 2026-08-18 | e9584fce14dffc5d8246bc5de457a7edfe011448999587892dec76ee4a2dd76a |
| eu_ai_act_article_{n}.html | https://artificialintelligenceact.eu/article/{n}/ (n = 1 to 113) | 2026-08-22 | see corpus/raw/eu_checksums.txt |

## Notes

**NIST AI RMF 1.0**  The AIRC site carries a notice
that a revision is in progress. All results in this repository were made with version 1.0 as retrieved on the date above.

**EU AI Act (2024/1689)** — primary source (EUR-Lex,
https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689) is
protected by AWS WAF bot-detection requiring JavaScript execution, and is hence not  accessible via plain HTTP requests. Realised on 22 Aug 2026.

Substituted source: artificialintelligenceact.eu (maintained by the Future of Life Institute), hosting the same 12 June 2024 version of the EU AI Act, formatted as one page per article at /article/{n}/. Article 1's  text
was verified against an independent EUR-Lex search snippet obtained separately. An exact word-for-word match was confirmed.

Each article page also includes an AI-generated "Summary" block (credited to CLaiRK). This is explicitly excluded from ingestion as we are stictly restricting it to official documentation: only the numbered legal text following it is parsed.

This repo is pinned to the original Official Journal text (12 July 2024) rather than the current consolidated version, since a further amending regulation (the "Digital Omnibus on AI") was in provisional agreement as of 22 August. This keeps the corpus a fixed, reproducible snapshot rather than
a dynamic one. This is consistent with the NIST AI RMF 1.0 pin above.