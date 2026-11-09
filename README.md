# IS 456 Lab 0: Your first agent

Starter code for Lab 0. The instructions are at **<https://www.is456.com/labs/lab0/>**.

The short version, after you've installed `uv` and Ollama:

```bash
uv sync
cp .env.example .env    # then paste your Hugging Face token into .env
uv run check_setup.py
```

| File | What it is |
|---|---|
| `config.py` | Reads the settings in `.env` |
| `check_setup.py` | Checks your setup |
| `step1_tokens.py` | Part 1a: text as tokens |
| `step1_chat.py` | Part 1b: one raw model call |
| `step2_agent_loop.py` | Part 2: the agent loop, by hand |
| `step3_langchain_agent.py` | Part 3: the same agent in LangChain |
| `tools.py` | The agent's tools. You'll finish `lookup_policy` in Part 4 |
| `observations.md` | Your answers. You submit this and `tools.py` |
| `data/policy.md` | Summit Ridge Outfitters' purchasing policy |
| `data/build_db.py` | Builds the purchasing database (`data/summit_ridge.db`) |

Submit by committing and pushing. Your last push before the deadline is your submission.
