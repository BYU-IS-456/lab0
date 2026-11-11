"""Step 2: an agent, written out by hand.

    uv run step2_agent_loop.py "How many active vendors do we have?"
    uv run step2_agent_loop.py "How many active vendors do we have?" --show-messages

The whole agent is run_agent() below. Everything after it only prints things.
"""

import argparse
import json
import os
import sys
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

# Color the labels when printing to a terminal, but not when output goes to a file.
# Set the environment variable NO_COLOR=1 to turn color off.
USE_COLOR = sys.stdout.isatty() and not os.environ.get("NO_COLOR")
if USE_COLOR and os.name == "nt":
    os.system("")  # odd but standard: switches older Windows consoles into color mode

STYLES = {"bold": "1", "dim": "2", "cyan": "36", "yellow": "33", "green": "32", "magenta": "35"}


def paint(text: str, *styles: str) -> str:
    if not USE_COLOR:
        return text
    codes = ";".join(STYLES[s] for s in styles)
    return f"\033[{codes}m{text}\033[0m"


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
        print("\n" + paint(f"--- step {step} ({usage.get('input_tokens', '?')} tokens in, {usage.get('output_tokens', '?')} out) ---", "dim"))
        print_reply(response)
        self.tool_calls += len(response.tool_calls)

    def tool_result(self, result) -> None:
        print_tool_result(str(result))

    def summary(self) -> None:
        seconds = time.perf_counter() - self.start
        print("\n" + paint(
            f"=== {self.model_calls} model calls | {self.tool_calls} tool calls | "
            f"{self.input_tokens:,} input tokens | {self.output_tokens:,} output tokens | {seconds:.1f} s ===",
            "bold",
        ))


def print_reply(response: AIMessage) -> None:
    thinking = response.additional_kwargs.get("reasoning_content", "").strip()
    if thinking:
        print(paint(f"[thinking] {thinking}", "dim"))
    for call in response.tool_calls:
        print(paint(f"[tool call] {call['name']}({json.dumps(call['args'])})", "cyan"))
    if response.content.strip():
        label = paint("[answer]", "bold", "green") if not response.tool_calls else paint("[says]", "green")
        print(f"{label} {response.content.strip()}")


def print_tool_result(result: str, limit: int = 800) -> None:
    shown = result if len(result) <= limit else result[:limit] + f"\n... ({len(result) - limit} more characters sent to the model)"
    print(f"{paint('[tool result]', 'yellow')} {shown}")


def print_messages(messages: list) -> None:
    """Print the conversation exactly as the model last received it."""
    print("\n" + paint("=" * 30 + " FULL CONVERSATION " + "=" * 30, "bold"))
    print(paint("[tools offered on every call]", "magenta"))
    for t in TOOLS:
        print(f"  {t.name}{json.dumps(t.args)}: {t.description}")
    for message in messages:
        role = {"system": "system", "human": "user", "ai": "assistant", "tool": "tool"}[message.type]
        print("\n" + paint(f"[{role}]", "magenta"))
        if message.type == "ai":
            thinking = message.additional_kwargs.get("reasoning_content", "").strip()
            if thinking:
                print(paint(f"(thinking) {thinking}", "dim"))
            for call in message.tool_calls:
                print(paint(f"(tool call) {call['name']}({json.dumps(call['args'])})", "cyan"))
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
