"""

Citation-groundedness scorer, determinstic first pass before LLM judge

Due to its deterinistic nature, this scorer has its limitation. It does not judge whether a claim is sematically true to its source (that is for the LLM judge)
it does 2 main things:

1. logs a word overlap score per claim, which is not infromational as a groundeness signal, as we specifically instructed the LLM to paraphrase the information into plain English.
This will only come in useful when were are auditing why the 2 LLM judges disagree with each other or with hand labels, seeing wheher a judge groudedness calls correlate with surface word-matching

2. Hard fails a claim if it states a specific number that does not apear in its cited chunk. This is the real groundedness check.

"""

import re
import json
from citation_existence import normalise_citation

#Common words will be stripped before computing word overlap, as it is too frequent to signal anything about whether content matches source
STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "and", "or", "but", "if", "in", "on", "at", "to", "for", "of", "with",
    "shall", "must", "may", "this", "that", "these", "those", "as", "by",
    "from", "it", "its", "their", "such", 
}

CITATION_BRACKET_PATTERN = re.compile(r"\[([^\]]+)\]")

#Matches with whole or decimal numbers, optionally followed by a percent sign
NUMBER_PATTERN = re.compile(r"\d+(?:\.\d+)?%?")

#for numbers in prose rather than in digits. Starts at 2 because one is used as a pronoun 
WORD_NUMBERS = {
    "two": "2", "three": "3", "four": "4", "five": "5",
    "six": "6", "seven": "7", "eight": "8", "nine": "9", "ten": "10",
    "eleven": "11", "twelve": "12", "thirteen": "13", "fourteen": "14",
    "fifteen": "15", "sixteen": "16", "seventeen": "17", "eighteen": "18",
    "nineteen": "19", "twenty": "20",
}

WORD_NUMBER_PATTERN = re.compile(
    r"\b(" + "|".join(WORD_NUMBERS.keys()) + r")\b", re.IGNORECASE
)

def load_chunk_texts(nist_path, eu_path):
    """
    Read both corpus JSONL files and return {chunk_id: text} for every
    chunk. 
    """
    chunk_texts = {}

    for path in (nist_path, eu_path):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                chunk = json.loads(line)
                chunk_texts[chunk["chunk_id"]] = chunk["text"]

    return chunk_texts

def extract_numbers(text):
    """
    Find every number in a piece of text, whether written as digits
    ("6") or spelled out as a word ("six"), and return them all as
    canonical digit strings.
    """
    digit_numbers = NUMBER_PATTERN.findall(text)
    word_matches = WORD_NUMBER_PATTERN.findall(text)
    word_numbers = [WORD_NUMBERS[w.lower()] for w in word_matches]
    return digit_numbers + word_numbers

def split_into_sentences(text):
    """Splits answer text into sentence on '.', '!', and '?'. simple heuristic, may missplit on abbrevations like art. 5. to be monitored and changed down the line if deemed neccessary"""
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return[s for s in sentences if s]

def extract_claims(answer_text):
    """Breaks an answer into (sentence, chunk_id) pairs. Sentences with no citation brakcet are skipped as a missing citation is different failure mode. sentence with more than one citation produces multiple pairs, one per citation pointed at same sentence text"""
    claims = []

    for sentence in split_into_sentences(answer_text):
        brackets = CITATION_BRACKET_PATTERN.findall(sentence)
        for raw_citation in brackets:
            chunk_id = normalise_citation(raw_citation) #uses function from citation_existence to convert citation into its canonical form
            if chunk_id:
                claims.append((sentence, chunk_id))

    return claims

def strip_citation_brackets(sentence):
    """Strips citation from sentence before checking. if not, it will match trivially"""
    return CITATION_BRACKET_PATTERN.sub("", sentence)

def compute_overlap(sentence, chunk_text):
    """fraction of the sentence's content appear in cited chunk's text. Not used as a gate, for logging in the later audit step"""
    clean_sentence = strip_citation_brackets(sentence)

    sentence_words = set(re.findall(r"[a-z]+", clean_sentence.lower())) - STOPWORDS
    chunk_words = set(re.findall(r"[a-z]+", chunk_text.lower())) - STOPWORDS

    if not sentence_words:
        return None #nothing left to compare

    matched = sentence_words & chunk_words
    return len(matched)/len(sentence_words)

def check_numbers_grounded(sentence, chunk_text):
    """Actual hard check. Pulls every number out of the sentence and confirms each one appears in the cited chunk. Returns (all_grounded: bool, missing_numbers: list of str)"""
    clean_sentence = strip_citation_brackets(sentence)
    sentence_numbers = extract_numbers(clean_sentence)
    chunk_numbers = set(extract_numbers(chunk_text))

    missing = [n for n in sentence_numbers if n not in chunk_numbers] #idomatic, but if you read it out it makes sense
    return (len(missing) == 0, missing)

def score_answer(answer_text, chunk_texts):
    """Actual orchestration, runs both checks across every claim in an answer. Returns a list of per-claim result dicts"""
    results = []

    for sentence, chunk_id in extract_claims(answer_text):
        chunk_text = chunk_texts.get(chunk_id)

        if chunk_text is None: #citation normalised fine but no text. Error handling, fails loudly. 
            results.append({
                "sentence": sentence,
                "chunk_id": chunk_id,
                "overlap" : None, 
                "numbers_grounded": False,
                "missing_numbers": ["<chunk text unavailable"],
            })
            continue

        overlap = compute_overlap(sentence, chunk_text)
        numbers_grounded, missing_numbers = check_numbers_grounded(sentence, chunk_text)

        results.append({
            "sentence": sentence,
            "chunk_id": chunk_id,
            "overlap": overlap,
            "numbers_grounded": numbers_grounded,
            "missing_numbers": missing_numbers
        })

    return results

if __name__ == "__main__":
    #test harness
    chunk_texts = load_chunk_texts("corpus/parsed/nist.jsonl", "corpus/parsed/eu_ai_act.jsonl")

    # A fake answer with three claims: one well-grounded paraphrase, one
    # with a number that matches its source, one with a fabricated number
    # that doesn't appear in its cited chunk.
    answer_text = (
        "Organisations must set clear policies assigning responsibility "
        "for oversight of human-AI systems [Govern 3.2]. "
        "This requirement does not override existing consumer protection "
        "law [Article 2(9)]. "
        "Providers must exercise human oversight within 96 hours of a "
        "high-risk incident [Article 14(2)]."
    )

    results = score_answer(answer_text, chunk_texts)

    for r in results:
        overlap_str = f"{r['overlap']:.2f}" if r["overlap"] is not None else "n/a"
        print(f"chunk={r['chunk_id']}")
        print(f"  sentence: {r['sentence']}")
        print(f"  overlap (informational): {overlap_str}")
        print(f"  numbers grounded: {r['numbers_grounded']}", end="")
        if r["missing_numbers"]:
            print(f"  (missing: {r['missing_numbers']})")
        else:
            print()
        print()


    


