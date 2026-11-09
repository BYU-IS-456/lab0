"""The tools the agent can use.

Each tool is an ordinary Python function. The @tool decorator turns it into
something a model can ask for: it reads the function's name, its parameters
and its docstring, and sends them to the model as the tool's description.
The model never runs these functions. It asks for one, and your code runs it.
"""

import sqlite3
from contextlib import closing
from pathlib import Path

from langchain_core.tools import tool

DATA_DIR = Path(__file__).parent / "data"
DB_PATH = DATA_DIR / "summit_ridge.db"
POLICY_PATH = DATA_DIR / "policy.md"
MAX_ROWS = 50  # never send the model more rows than this


def connect() -> sqlite3.Connection:
    """Open the purchasing database read-only, building it first if needed."""
    if not DB_PATH.exists():
        from data.build_db import build

        build(DB_PATH)
    return sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)


@tool
def list_tables() -> str:
    """List every table in the purchasing database, with its columns and row count. Call this before writing SQL so you know the exact table and column names."""
    with closing(connect()) as conn:
        names = [row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name")]
        lines = []
        for name in names:
            columns = [f"{col[1]} {col[2]}" for col in conn.execute(f"PRAGMA table_info({name})")]
            count = conn.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
            lines.append(f"{name} ({count} rows): {', '.join(columns)}")
    return "\n".join(lines)


@tool
def run_sql(query: str) -> str:
    """Run one SQLite SELECT query against the purchasing database (vendors, purchase orders, receipts, invoices) and return the matching rows. The database is read-only. Amounts are in US dollars; dates are text in YYYY-MM-DD format."""
    with closing(connect()) as conn:
        cursor = conn.execute(query)  # errors are raised to whoever called the tool
        rows = cursor.fetchmany(MAX_ROWS + 1)
        if cursor.description is None:
            return "The query ran but returned no rows or columns."
        header = [col[0] for col in cursor.description]

    if not rows:
        return f"{' | '.join(header)}\n(0 rows)"
    lines = [" | ".join(header)]
    lines += [" | ".join("NULL" if value is None else str(value) for value in row) for row in rows[:MAX_ROWS]]
    if len(rows) > MAX_ROWS:
        lines.append(f"(only the first {MAX_ROWS} rows are shown; add a WHERE clause or LIMIT to narrow it down)")
    else:
        lines.append(f"({len(rows)} rows)")
    return "\n".join(lines)


def load_policy_sections() -> list[dict]:
    """Read data/policy.md and split it into sections at each '## ' heading.

    Returns a list like [{"heading": "Three-way match", "text": "Before an invoice ..."}, ...].
    """
    sections = []
    for chunk in POLICY_PATH.read_text(encoding="utf-8").split("\n## ")[1:]:
        heading, _, text = chunk.partition("\n")
        sections.append({"heading": heading.strip(), "text": text.strip()})
    return sections


@tool
def lookup_policy(topic: str) -> str:
    """Look up the company's purchasing and accounts payable policy on a topic, e.g. 'three-way match', 'duplicate invoices', 'new vendors'."""
    # TODO (Part 4): replace the line below with a real implementation.
    #
    #   1. sections = load_policy_sections()
    #   2. Split `topic` into lowercase words.
    #   3. Keep every section whose heading or text contains any of those words.
    #   4. Return the matching sections as "## heading\n\ntext", joined by blank
    #      lines. If nothing matches, return a message that says so AND lists
    #      the available section headings, so the model can try again.
    return "ERROR: lookup_policy is not implemented yet."


TOOLS = [list_tables, run_sql, lookup_policy]
