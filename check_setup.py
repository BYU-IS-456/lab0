"""Check that everything for Lab 0 is installed and configured.

    uv run check_setup.py

Fix the first FAIL and run it again until every line says PASS.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
results = []


def check(name: str, hint: str = ""):
    """Run a check function and print PASS, FAIL or SKIP. Returns True if it passed."""

    def decorator(fn):
        if results and results[-1] is False and getattr(fn, "needs_previous", False):
            print(f"SKIP {name}")
            results.append(False)
            return fn
        try:
            detail = fn()
            print(f"PASS {name}" + (f" ({detail})" if detail else ""))
            results.append(True)
        except Exception as error:
            print(f"FAIL {name}: {error}")
            if hint:
                print(f"     -> {hint}")
            results.append(False)
        return fn

    return decorator


def needs_previous(fn):
    fn.needs_previous = True
    return fn


print(f"Python {sys.version.split()[0]} at {sys.executable}\n")

import config  # noqa: E402  (imported after the header so a broken .env still shows Python info)


@check(".env file exists", "Copy .env.example to .env (step 0.4).")
def _():
    if not (ROOT / ".env").is_file():
        raise RuntimeError("no file named .env in " + str(ROOT))


@check(".env is ignored by git", "Don't commit anything. Ask for help.")
def _():
    result = subprocess.run(["git", "check-ignore", "-q", ".env"], cwd=ROOT, capture_output=True)
    if result.returncode == 128:
        raise RuntimeError("this folder isn't a git repository (did you clone it?)")
    if result.returncode != 0:
        raise RuntimeError(".env is NOT ignored and could be committed")


@check("HF_TOKEN is set", "Paste your Hugging Face token after HF_TOKEN= in .env, with no spaces or quotes.")
def _():
    token = config.HF_TOKEN or ""
    if not token or token == "hf_yourTokenHere":
        raise RuntimeError("HF_TOKEN is empty or still the placeholder")
    if not token.startswith("hf_") or " " in token or '"' in token:
        raise RuntimeError("HF_TOKEN should start with hf_ and contain no spaces or quotes")


@check("Hugging Face accepts your token", "The token was copied incompletely or revoked. Make a new one.")
@needs_previous
def _():
    from huggingface_hub import whoami

    return "signed in as " + whoami(token=config.HF_TOKEN)["name"]


@check("Tokenizer downloads", f"Check HF_TOKENIZER in .env; it should be {config.HF_TOKENIZER!r}.")
@needs_previous
def _():
    from tokenizers import Tokenizer

    Tokenizer.from_pretrained(config.HF_TOKENIZER, token=config.HF_TOKEN)
    return config.HF_TOKENIZER


@check("Ollama is running", "Start the Ollama app, or run `ollama serve` in another terminal and leave it open.")
def _():
    import ollama

    ollama.Client(host=config.OLLAMA_BASE_URL, timeout=5).list()
    return config.OLLAMA_BASE_URL


@check(f"Model {config.MODEL} is downloaded", f"Run: ollama pull {config.MODEL}")
@needs_previous
def _():
    import ollama

    names = [m.model for m in ollama.Client(host=config.OLLAMA_BASE_URL).list().models]
    if config.MODEL not in names and f"{config.MODEL}:latest" not in names:
        raise RuntimeError(f"not in `ollama list` (found: {', '.join(names) or 'nothing'})")


@check("Model answers (the first call can take 30 seconds)", "See Troubleshooting on the lab page.")
@needs_previous
def _():
    import ollama

    response = ollama.Client(host=config.OLLAMA_BASE_URL).chat(
        model=config.MODEL,
        messages=[{"role": "user", "content": "Reply with just the word ready."}],
        options={"num_ctx": config.NUM_CTX},
        think=False,
    )
    return repr(response.message.content.strip()[:40])


@check("Purchasing database is ready", "Run: uv run data/build_db.py")
def _():
    from tools import run_sql

    count = run_sql.invoke({"query": "SELECT COUNT(*) FROM vendors"}).splitlines()[1]
    return f"{count} vendors"


print()
if all(results):
    print("Everything passed. You're ready for class.")
else:
    print("Fix the first FAIL above, then run this again.")
    sys.exit(1)
