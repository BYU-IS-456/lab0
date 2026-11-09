"""Step 3: the same agent, built with LangChain.

    uv run step3_langchain_agent.py "Which invoices are for more than their purchase order amount?"

Same model, same tools, same system prompt as step2_agent_loop.py. Compare the two.
"""

import argparse

from langchain.agents import create_agent
from langchain.agents.middleware import ToolRetryMiddleware

from step2_agent_loop import MAX_STEPS, SYSTEM_PROMPT, Trace, make_model
from tools import TOOLS


def main() -> None:
    parser = argparse.ArgumentParser(description="Ask the LangChain version of the agent a question.")
    parser.add_argument("question")
    args = parser.parse_args()
    print(f"Question: {args.question}")

    agent = create_agent(
        make_model(),
        TOOLS,
        system_prompt=SYSTEM_PROMPT,
        # Without this, LangChain stops the whole run when a tool raises an error.
        # With it, the error goes back to the model as a message, in LangChain's own words.
        middleware=[ToolRetryMiddleware(max_retries=0, on_failure="continue")],
    )

    trace = Trace()
    step = 0
    # stream() runs the agent and hands us each new message as it happens.
    for update in agent.stream(
        {"messages": [{"role": "user", "content": args.question}]},
        {"recursion_limit": 2 * MAX_STEPS + 1},
        stream_mode="updates",
    ):
        for node_output in update.values():
            for message in (node_output or {}).get("messages", []):
                if message.type == "ai":
                    step += 1
                    trace.model_reply(step, message)
                elif message.type == "tool":
                    trace.tool_result(message.content)
    trace.summary()


if __name__ == "__main__":
    main()
