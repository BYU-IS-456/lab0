"""Step 1a: see text the way the model sees it.

    uv run step1_tokens.py
    uv run step1_tokens.py "your text here"

Downloads your model's tokenizer from Hugging Face (using HF_TOKEN), splits
text into tokens, and shows what the agent re-sends to the model on every step.
"""

import json
import sys

from langchain_core.utils.function_calling import convert_to_openai_tool
from tokenizers import Tokenizer

import config
from step2_agent_loop import SYSTEM_PROMPT
from tools import TOOLS

EXAMPLES = [
    "Summit Ridge Outfitters",
    "INV-1045 for $20,440.00",
    "How many r's are in strawberry?",
    "SELECT COUNT(*) FROM vendors WHERE status = 'active';",
    "Las facturas duplicadas se ponen en espera.",  # Spanish: "Duplicate invoices are put on hold."
]


def show(tokenizer: Tokenizer, text: str) -> int:
    encoding = tokenizer.encode(text)
    pieces = [text[start:end] for start, end in encoding.offsets]
    print(f"\n{text!r}")
    print(f"  {len(encoding.ids)} tokens: " + " ".join(f"[{piece}]" for piece in pieces))
    print(f"  token IDs: {encoding.ids}")
    return len(encoding.ids)


def count(tokenizer: Tokenizer, text: str) -> int:
    return len(tokenizer.encode(text).ids)


def main() -> None:
    print(f"Downloading the tokenizer for {config.HF_TOKENIZER} ...")
    tokenizer = Tokenizer.from_pretrained(config.HF_TOKENIZER, token=config.HF_TOKEN)
    print(f"Its vocabulary has {tokenizer.get_vocab_size():,} different tokens.")

    for text in sys.argv[1:] or EXAMPLES:
        show(tokenizer, text)

    # What the agent sends before the conversation even starts.
    print("\n--- The fixed cost of every agent step ---")
    print("Each time the agent calls the model, it sends the system prompt and a description of every tool:")
    prompt_tokens = count(tokenizer, SYSTEM_PROMPT)
    print(f"  {'system prompt:':20} {prompt_tokens:4} tokens")
    tool_tokens = 0
    for tool in TOOLS:
        n = count(tokenizer, json.dumps(convert_to_openai_tool(tool)))
        tool_tokens += n
        print(f"  {tool.name + ' tool:':20} {n:4} tokens")
    print(f"  {'total:':20} {prompt_tokens + tool_tokens:4} tokens, plus the question, every time")
    print("(The real number is a bit higher: the model's chat template wraps each part in formatting tokens.)")


if __name__ == "__main__":
    main()
