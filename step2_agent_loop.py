"""Step 2: an agent, written out by hand.

    uv run step2_agent_loop.py "How many active vendors do we have?"
    uv run step2_agent_loop.py "How many active vendors do we have?" --show-messages

The whole agent is run_agent() below. Everything after it only prints things.
"""

import argparse
import json
import time

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_ollama import ChatOllama

import config
from tools import TOOLS

MAX_STEPS = 10  # the most times we'll call the model for one question

SYSTEM_PROMPT = """You are an assistant for the accounts payable team at Summit Ridge Outfitters, an outdoor gear retailer.
You can query the company's purchasing database and look up its purchasing policy. You cannot change anything.
Look things up instead of guessing. Check the table and column names before you write SQL.
If a tool returns an error, read it and try again a different way, or say plainly that you could not find the answer.
Keep your final answer short, and say what data or policy it is based on."""


def make_model() -> ChatOllama:
    return ChatOllama(
        model=config.MODEL,
        base_url=config.OLLAMA_BASE_URL,
        num_ctx=config.NUM_CTX,
        reasoning=True,  # return the model's thinking separately from its answer
    )


def run_agent(question: str) -> list:
    model = make_model().bind_tools(TOOLS)  # every request now includes the tool descriptions
    tools_by_name = {t.name: t for t in TOOLS}
    messages = [SystemMessage(SYSTEM_PROMPT), HumanMessage(question)]
    trace = Trace()

    for step in range(1, MAX_STEPS + 1):
        # 1. Send the whole conversation so far to the model, and add its reply.
        response = model.invoke(messages)
        messages.append(response)
        trace.model_reply(step, response)

        # 2. If the model didn't ask for any tools, its reply is the final answer.
        if not response.tool_calls:
            break

        # 3. Run each tool the model asked for, and add each result to the conversation.
        for call in response.tool_calls:
            tool = tools_by_name.get(call["name"])
            try:
                if tool is None:
                    raise ValueError(f"there is no tool named {call['name']!r}")
                result = tool.invoke(call["args"])
            except Exception as error:
                result = f"ERROR: {error}"  # the model sees the error and can try something else
            messages.append(ToolMessage(content=str(result), tool_call_id=call["id"]))
            trace.tool_result(result)
    else:
        print(f"\nStopped after MAX_STEPS ({MAX_STEPS}) model calls without a final answer.")

    trace.summary()
    return messages


# --- Printing. You don't need to read below this line. ------------------------


class Trace:
    """Prints each step as it happens and adds up the cost."""

    def __init__(self):
        self.start = time.perf_counter()
        self.model_calls = self.tool_calls = self.input_tokens = self.output_tokens = 0

    def model_reply(self, step: int, response: AIMessage) -> None:
        self.model_calls += 1
        usage = response.usage_metadata or {}
        self.input_tokens += usage.get("input_tokens", 0)
        self.output_tokens += usage.get("output_tokens", 0)
        print(f"\n--- step {step} ({usage.get('input_tokens', '?')} tokens in, {usage.get('output_tokens', '?')} out) ---")
        print_reply(response)
        self.tool_calls += len(response.tool_calls)

    def tool_result(self, result) -> None:
        print_tool_result(str(result))

    def summary(self) -> None:
        seconds = time.perf_counter() - self.start
        print(
            f"\n=== {self.model_calls} model calls | {self.tool_calls} tool calls | "
            f"{self.input_tokens:,} input tokens | {self.output_tokens:,} output tokens | {seconds:.1f} s ==="
        )


def print_reply(response: AIMessage) -> None:
    thinking = response.additional_kwargs.get("reasoning_content", "").strip()
    if thinking:
        print(f"[thinking] {thinking}")
    for call in response.tool_calls:
        print(f"[tool call] {call['name']}({json.dumps(call['args'])})")
    if response.content.strip():
        label = "[answer]" if not response.tool_calls else "[says]"
        print(f"{label} {response.content.strip()}")


def print_tool_result(result: str, limit: int = 800) -> None:
    shown = result if len(result) <= limit else result[:limit] + f"\n... ({len(result) - limit} more characters sent to the model)"
    print(f"[tool result] {shown}")


def print_messages(messages: list) -> None:
    """Print the conversation exactly as the model last received it."""
    print("\n" + "=" * 30 + " FULL CONVERSATION " + "=" * 30)
    print("[tools offered on every call]")
    for t in TOOLS:
        print(f"  {t.name}{json.dumps(t.args)}: {t.description}")
    for message in messages:
        role = {"system": "system", "human": "user", "ai": "assistant", "tool": "tool"}[message.type]
        print(f"\n[{role}]")
        if message.type == "ai":
            thinking = message.additional_kwargs.get("reasoning_content", "").strip()
            if thinking:
                print(f"(thinking) {thinking}")
            for call in message.tool_calls:
                print(f"(tool call) {call['name']}({json.dumps(call['args'])})")
        if message.content:
            print(message.content)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ask the accounts payable agent a question.")
    parser.add_argument("question", help='e.g. "How many active vendors do we have?"')
    parser.add_argument("--show-messages", action="store_true", help="print the full conversation at the end")
    args = parser.parse_args()

    print(f"Question: {args.question}")
    final_messages = run_agent(args.question)
    if args.show_messages:
        print_messages(final_messages)
