"""Step 1b: one raw model call, no tools, no agent.

    uv run step1_chat.py                   # the same prompt, three times
    uv run step1_chat.py --temperature 0   # randomness turned down

This talks to Ollama directly, so you can see the entire request: a model
name, a list of messages, and some options. That's all a model ever gets.
"""

import argparse
import json

import ollama

import config

PROMPT = (
    "Should Summit Ridge Outfitters pay invoice INV-1045 for $20,440.00? "
    "Answer yes or no, then give your reason in one sentence."
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Send the same prompt to the model three times.")
    parser.add_argument("--temperature", type=float, help="0 = least random; leave it out to use the model's default")
    parser.add_argument("--times", type=int, default=3, help="how many times to ask (default 3)")
    args = parser.parse_args()

    options = {"num_ctx": config.NUM_CTX}
    if args.temperature is not None:
        options["temperature"] = args.temperature

    request = {
        "model": config.MODEL,
        "messages": [{"role": "user", "content": PROMPT}],
        "options": options,
        "think": False,  # skip the model's thinking to keep this quick
    }
    print("The entire request sent to the model:")
    print(json.dumps(request, indent=2))

    client = ollama.Client(host=config.OLLAMA_BASE_URL)
    for i in range(1, args.times + 1):
        response = client.chat(**request)
        print(f"\n--- answer {i} ({response.prompt_eval_count} tokens in, {response.eval_count} out) ---")
        print(response.message.content.strip())


if __name__ == "__main__":
    main()
