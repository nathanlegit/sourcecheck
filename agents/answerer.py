"""Answerer Agent: takes the plain-english question and retrieved chunks from the retriever, and outputs a cited answer based only on the retrieved chunks"""

from pathlib import Path

from anthropic import Anthropic #Using Claude Sonnet
from dotenv import load_dotenv

load_dotenv() #reads .env and populated os.environ
client = Anthropic() #looks for the anthropic api key in the environment on its own

MODEL = "claude-sonnet-4-5" 
SYSTEM_PROMPT = Path("prompts/answerer_system.md").read_text(encoding="utf-8")

def build_user_prompt(question: str, chunks: list[dict]) -> str:
    """Concatenates the chunks into the message itself, in a nice format"""
    excerpts = "\n\n".join(
        f"[{c['display_id']}, {c['document']}] {c['text']}" for c in chunks
    )
    return f"Source excerpts:\n\n{excerpts}\n\nQuestion: {question}"

def answer(question: str, chunks: list[dict]) -> str:
    """Calls the Anthropic Client using the user prompt and generates an output"""
    user_prompt = build_user_prompt(question, chunks)

    response = client.messages.create( #Anthropic's Messages API documentation
        model = MODEL,
        max_tokens = 1024,
        system = SYSTEM_PROMPT,
        messages = [{"role": "user", "content": user_prompt}],
    )

    return response.content[0].text #Claude's response comes back as a list of content blocks, so we need to refernece index 0 to and .text to pull the actual string out of the list

if __name__ == "__main__":
    from retriever import retrieve

    test_questions = [
        "What does NIST say about legal and regulatory requirements?",
        "Who was the principal author of the NIST AI RMF?",
        "What year was the NIST AI RMF published, and who signed off on it?",
        "Does NIST require third-party AI vendors to be regularly monitored, and what happens if they fail an audit?",
    ]

    for question in test_questions:
        chunks = retrieve(question)
        result = answer(question, chunks)
        print(f"{'='*70}")
        print(f"Q: {question}\n")
        print(result)
        print()