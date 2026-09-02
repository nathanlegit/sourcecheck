"""
    Citation Existence scorer.

    Checks whether a citation string produced by the answerer refers to an actual chunk_id in the corpus.
    Pure lookup, nothing more, checks that the ID being pointed to is a real chunk_id.
"""

import json
import re #for regex

def load_valid_ids(nist_path, eu_path):
    """Reads both corpus JSONL files and return a set of all chunk_ids."""
    valid_ids = set() #use set because we want unique ids

    for path in (nist_path, eu_path):
        with open(path, "r", encoding = "utf-8") as f:
            for line in f: #have to go line by line because the file as a whole is not one JSON document
                line = line.strip()
                if not line:
                    continue #error-handling
                chunk = json.loads(line)
                valid_ids.add(chunk["chunk_id"])

    return valid_ids

NIST_FUNCTIONS = ("govern", "map", "measure", "manage") #need to add the function to the regex pattern

EU_CLAUSE_PATTERN = re.compile(r"article\s+(\d+)\s*\(\s*(\d+)\s*\)", re.IGNORECASE) #Pattern for "Article 14(2)", "article 14 (2)", or "ARTICLE 14(2) - number"

EU_BARE_ARTICLE_PATTERN = re.compile(r"article\s+(\d+)\b", re.IGNORECASE) #Pattern for a bare "Article 14", for those with only one clause. Resolved with corpus context (resolve_bare_article) as it is too ambiguous

NIST_PATTERN = re.compile(
    r"(" + "|".join(NIST_FUNCTIONS) + r")\s*-?\s*(\d+)\.(\d+)", 
    re.IGNORECASE,
) #Pattern for "Govern 3.2", "GOVERN-3.2", or "govern3.2"

def resolve_bare_article(article_num, valid_ids):
    """Try to resolve a bare article number (Article 113) to a real chunk_id, by scanning valid_ids for that article and checking that there is only one chunk associated with it. This is the reason why we have the bare articles in the first place"""
    prefix = f"eu:article-{article_num}-"
    candidates = []
    for chunk_id in valid_ids:
        if chunk_id.startswith(prefix):
            candidates.append(chunk_id)

    if len(candidates) == 1: #checks if there is only one chunk associated with the article
        return candidates[0]
    return None

def normalise_citation(raw, valid_ids = None):
    """
    Converts a raw citation string from the answerer into canonical chunk_id form, or return None if it cannot be resolved.
    Clause-level EU citations and NIST citations normalise on regex, article only ey citations needs resultion with corpus data
    """
    eu_match = EU_CLAUSE_PATTERN.search(raw)
    if eu_match:
        article_num, clause_num = eu_match.groups()
        return f"eu:article-{article_num}-{clause_num}"

    nist_match = NIST_PATTERN.search(raw)
    if nist_match:
        function, major, minor = nist_match.groups()
        return f"nist:{function.lower()}-{major}.{minor}"

    bare_match = EU_BARE_ARTICLE_PATTERN.search(raw)
    if bare_match and valid_ids is not None:
        article_num = bare_match.group(1)
        return resolve_bare_article(article_num, valid_ids)

    return None

def check_citation_exists(raw_citation, valid_ids):
    """Checker: returns True if raw_citations normalises to an actual chunk_id, else False"""
    normalised = normalise_citation(raw_citation, valid_ids = valid_ids)
    if normalised is None:
        return False
    return normalised in valid_ids

if __name__ == "__main__":
    # --- test harness ---
    # Real IDs below are pulled verbatim from random corpus lines. Fake IDs are deliberately-wrong variants of those
    # same real ones, to confirm the checker discriminates rather
    # than matching the regex and returning True for anything shaped
    # right.

    valid_ids = load_valid_ids("corpus/parsed/nist.jsonl", "corpus/parsed/eu_ai_act.jsonl")

    test_cases = [
        # (raw citation, expected chunk_id or None, expected exists boolean)
        ("Article 2(9)", "eu:article-2-9", True),
        ("Article 2 (12)", "eu:article-2-12", True),        # space before paren
        ("article 2(11)", "eu:article-2-11", True),         # lowercase
        ("Govern 3.2", "nist:govern-3.2", True),
        ("GOVERN-4.1", "nist:govern-4.1", True),             # hyphen, uppercase
        ("Article 2(99)", "eu:article-2-99", False),         # real article, fake clause
        ("Article 500(1)", "eu:article-500-1", False),       # article doesn't exist
        ("Govern 99.9", "nist:govern-99.9", False),          # fake subcategory
        ("Map 99.9", "nist:map-99.9", False),                  # real-shaped, wrong function
        ("Article 2", None, False),                          # bare, ambiguous (12 real clauses) - stays unresolved
        ("Article 113", "eu:article-113-1", True),           # bare, but only 1 real clause - resolves
        ("Article 999", None, False),                        # bare, article doesn't exist at all - 0 candidates
        ("something unrelated", None, False),                # no match at all
    ]

    passed = 0
    for raw, expected_norm, expected_exists in test_cases:
        # normalise_citation is called with valid_ids here to match how
        # check_citation_exists calls it - without valid_ids, bare article
        # citations would never resolve even in the single-clause case.
        actual_norm = normalise_citation(raw, valid_ids=valid_ids)
        actual_exists = check_citation_exists(raw, valid_ids)

        ok = (actual_norm == expected_norm) and (actual_exists == expected_exists)
        status = "PASS" if ok else "FAIL"
        if ok:
            passed += 1

        print(f"{status}  raw={raw!r:22} -> normalised={actual_norm!r:22} exists={actual_exists}")

    print(f"\n{passed}/{len(test_cases)} passed")