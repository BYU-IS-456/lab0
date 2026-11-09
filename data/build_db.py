"""Build the Summit Ridge Outfitters purchasing database (data/summit_ridge.db).

The agent's tools build it automatically the first time they need it. Run this
yourself only if you want a fresh copy:

    uv run data/build_db.py

The data is fictional, and it's the same on every laptop: a fixed random seed
plus a handful of hand-placed problems for the agent to find.
"""

import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path

DB_PATH = Path(__file__).parent / "summit_ridge.db"

SCHEMA = """
CREATE TABLE vendors (
    vendor_id      TEXT PRIMARY KEY,   -- e.g. V007
    name           TEXT NOT NULL,
    status         TEXT NOT NULL,      -- active | inactive | pending_approval
    payment_terms  TEXT NOT NULL,      -- e.g. Net 30, 2/10 Net 30
    onboarded_date TEXT,               -- YYYY-MM-DD; NULL if not yet approved
    contact_email  TEXT
);

CREATE TABLE purchase_orders (
    po_number   TEXT PRIMARY KEY,      -- e.g. PO-2031
    vendor_id   TEXT NOT NULL REFERENCES vendors(vendor_id),
    order_date  TEXT NOT NULL,
    description TEXT NOT NULL,
    amount      REAL NOT NULL,         -- total approved amount in USD
    approved_by TEXT NOT NULL,
    status      TEXT NOT NULL          -- open | closed
);

CREATE TABLE receipts (
    receipt_id      TEXT PRIMARY KEY,  -- e.g. RCV-3012
    po_number       TEXT NOT NULL REFERENCES purchase_orders(po_number),
    received_date   TEXT NOT NULL,
    amount_received REAL NOT NULL,     -- value of the goods received in USD
    received_by     TEXT NOT NULL
);

CREATE TABLE invoices (
    invoice_number     TEXT PRIMARY KEY,  -- our ID, e.g. INV-1045
    vendor_id          TEXT NOT NULL REFERENCES vendors(vendor_id),
    vendor_invoice_ref TEXT NOT NULL,     -- the number printed on the vendor's invoice
    po_number          TEXT REFERENCES purchase_orders(po_number),  -- NULL if no PO
    invoice_date       TEXT NOT NULL,
    due_date           TEXT NOT NULL,
    amount             REAL NOT NULL,     -- USD
    status             TEXT NOT NULL      -- pending | approved | paid | on_hold
);
"""

# (vendor_id, name, status, payment_terms, invoice prefix, what they sell)
VENDORS = [
    ("V001", "Alpine Textile Mills", "active", "Net 30", "ATM", "Ripstop nylon fabric"),
    ("V002", "Granite Peak Apparel", "active", "Net 45", "GPA", "Insulated jackets"),
    ("V003", "Cascade Buckle & Hardware", "active", "2/10 Net 30", "CBH", "Buckles and zippers"),
    ("V004", "Bonneville Freight", "active", "Net 15", "BF", "Inbound freight"),
    ("V005", "Wasatch Packaging Co.", "active", "Net 30", "WP", "Shipping boxes and mailers"),
    ("V006", "Treeline Down Supply", "active", "Net 30", "TR", "Goose down fill"),
    ("V007", "Red Rock Footwear", "active", "Net 60", "RRF", "Hiking boots"),
    ("V008", "Basin Carabiner Works", "active", "2/10 Net 30", "BC", "Carabiners and hardware"),
    ("V009", "Sawtooth Signage", "active", "Net 30", "SS", "Store signage"),
    ("V010", "High Desert Optics", "active", "Net 45", "HDO", "Binoculars and headlamps"),
    ("V011", "Kings Peak Tent Co.", "active", "Net 45", "KPT", "Tents and shelters"),
    ("V012", "Provo Canyon Printing", "active", "Net 30", "PCP", "Catalogs and hang tags"),
    ("V013", "Lone Cone Logistics", "active", "Net 15", "LCL", "Warehouse labor"),
    ("V014", "Saltflat Solar", "active", "Net 30", "SFS", "Solar chargers"),
    ("V015", "Bear River Wool", "active", "Net 30", "BRW", "Merino base layers"),
    ("V016", "Mesa Verde Ceramics", "active", "Net 30", "MVC", "Camp mugs"),
    ("V017", "Echo Ridge Properties", "active", "Net 30", "ERP", "Warehouse rent"),
    ("V018", "Silver Fork Cutlery", "active", "Net 30", "SFC", "Pocket knives and camp utensils"),
    ("V019", "Teton Trail Foods", "active", "Net 30", "TTF", "Trail mix and freeze-dried meals"),
    ("V020", "Pinecrest Plastics", "inactive", "Net 30", "PP", "Water bottles"),
    ("V021", "Ogden Office Supply", "inactive", "Net 30", "OOS", "Office supplies"),
    ("V022", "Timpanogos Tech Services", "inactive", "Net 30", "TTS", "Point-of-sale support"),
    ("V023", "Snowbasin Strap Co.", "pending_approval", "Net 30", "SBS", "Webbing and straps"),
    ("V024", "Gila Gear Repair", "pending_approval", "Net 30", "GGR", "Gear repair services"),
]

APPROVERS = ["Dana Whitfield", "Marcus Oyelaran", "Priya Raman", "Tom Becker"]
RECEIVERS = ["Luis Ortega", "Hannah Cho", "Brent Sorensen"]

FIRST_INVOICE = 1001
LAST_INVOICE = 1080
START = date(2026, 10, 1)


def invoice_date(n: int) -> date:
    """Invoices arrive about every 1.25 days, starting October 1, 2026."""
    return START + timedelta(days=round((n - FIRST_INVOICE) * 1.25))


def terms_days(terms: str) -> int:
    return int(terms.split("Net ")[1])


def build(path: Path = DB_PATH) -> Path:
    rng = random.Random(456)
    vendors = {v[0]: v for v in VENDORS}
    active = [v[0] for v in VENDORS if v[2] == "active" and v[0] != "V017"]

    if path.exists():
        path.unlink()
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA)

    for vid, name, status, terms, _prefix, _what in VENDORS:
        onboarded = None
        if status != "pending_approval":
            onboarded = str(date(2021, 3, 1) + timedelta(days=rng.randrange(0, 1500)))
        email = "ap@" + "".join(c for c in name.lower() if c.isalnum())[:18] + ".example.com"
        conn.execute(
            "INSERT INTO vendors VALUES (?, ?, ?, ?, ?, ?)",
            (vid, name, status, terms, onboarded, email),
        )

    po_counter = iter(range(2001, 3000))
    receipt_counter = iter(range(3001, 4000))

    def add_po(vendor_id, inv_date, amount, received=True, received_amount=None, closed=False):
        po = f"PO-{next(po_counter)}"
        order_date = inv_date - timedelta(days=rng.randint(12, 28))
        approver = APPROVERS[0] if amount <= 5000 else APPROVERS[1] if amount <= 25000 else APPROVERS[2]
        what = vendors[vendor_id][5]
        conn.execute(
            "INSERT INTO purchase_orders VALUES (?, ?, ?, ?, ?, ?, ?)",
            (po, vendor_id, str(order_date), what, amount, approver, "closed" if closed else "open"),
        )
        if received:
            conn.execute(
                "INSERT INTO receipts VALUES (?, ?, ?, ?, ?)",
                (
                    f"RCV-{next(receipt_counter)}",
                    po,
                    str(order_date + timedelta(days=rng.randint(4, 10))),
                    amount if received_amount is None else received_amount,
                    rng.choice(RECEIVERS),
                ),
            )
        return po

    def add_invoice(n, vendor_id, amount, po, status, ref=None, inv_date=None):
        inv_date = inv_date or invoice_date(n)
        terms = vendors[vendor_id][3]
        ref = ref or f"{vendors[vendor_id][4]}-{rng.randint(10000, 99999)}"
        conn.execute(
            "INSERT INTO invoices VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                f"INV-{n}",
                vendor_id,
                ref,
                po,
                str(inv_date),
                str(inv_date + timedelta(days=terms_days(terms))),
                amount,
                status,
            ),
        )

    def normal_status(n):
        if n <= 1055:
            return "paid"
        if n <= 1066:
            return rng.choice(["approved", "paid", "approved"])
        return rng.choice(["pending", "approved", "pending"])

    # --- Hand-placed problems. Each is something the policy cares about. -------

    def inv_1045():  # Billed well over its PO: $20,440.00 against an $18,000.00 PO.
        d = invoice_date(1045)
        po = add_po("V002", d, 18000.00)
        add_invoice(1045, "V002", 20440.00, po, "pending", ref="GPA-55190")

    def inv_1023():  # Slightly over its PO, but inside the variance tolerance.
        d = invoice_date(1023)
        po = add_po("V011", d, 9850.00, closed=True)
        add_invoice(1023, "V011", 9995.00, po, "paid")

    def inv_1067():  # 20% over its PO.
        d = invoice_date(1067)
        po = add_po("V009", d, 3150.00)
        add_invoice(1067, "V009", 3780.00, po, "pending")

    dup_po = {}

    def inv_1052():  # First copy of an exact duplicate (already paid).
        d = invoice_date(1052)
        dup_po["tr"] = add_po("V006", d, 6725.50)
        add_invoice(1052, "V006", 6725.50, dup_po["tr"], "paid", ref="TR-88213")

    def inv_1058():  # Second copy: same vendor, same vendor invoice number, same amount, same PO.
        add_invoice(1058, "V006", 6725.50, dup_po["tr"], "pending", ref="TR-88213")

    def inv_1031():  # First copy of a near duplicate (already paid).
        d = invoice_date(1031)
        dup_po["bc"] = add_po("V008", d, 2318.40, closed=True)
        add_invoice(1031, "V008", 2318.40, dup_po["bc"], "paid", ref="BC-4471")

    def inv_1074():  # Same vendor and amount, invoice number differs only by punctuation.
        add_invoice(1074, "V008", 2318.40, dup_po["bc"], "pending", ref="BC4471")

    def rent(n, month):  # Monthly rent: same vendor and amount every month. NOT duplicates.
        add_invoice(n, "V017", 4250.00, None, "paid" if n < 1060 else "pending", ref=f"ERP-RENT-{month}")

    def inv_1049():  # Goods not received yet: no receiving record for the PO.
        d = invoice_date(1049)
        po = add_po("V010", d, 7412.75, received=False)
        add_invoice(1049, "V010", 7412.75, po, "pending")

    def inv_1063():  # From an inactive vendor.
        d = invoice_date(1063)
        po = add_po("V020", d, 2985.00)
        add_invoice(1063, "V020", 2985.00, po, "pending")

    def inv_1070():  # $3,900 with no purchase order.
        add_invoice(1070, "V012", 3900.00, None, "pending")

    def inv_1077():  # From a vendor that hasn't been approved yet.
        d = invoice_date(1077)
        po = add_po("V023", d, 1640.00)
        add_invoice(1077, "V023", 1640.00, po, "pending")

    def inv_1061():  # Partial delivery: invoiced in full, but only part received.
        d = invoice_date(1061)
        po = add_po("V007", d, 12600.00, received_amount=8400.00)
        add_invoice(1061, "V007", 12600.00, po, "pending")

    planted = {
        1023: inv_1023,
        1031: inv_1031,
        1045: inv_1045,
        1049: inv_1049,
        1052: inv_1052,
        1058: inv_1058,
        1061: inv_1061,
        1063: inv_1063,
        1067: inv_1067,
        1070: inv_1070,
        1074: inv_1074,
        1077: inv_1077,
        1004: lambda: rent(1004, "2026-10"),
        1029: lambda: rent(1029, "2026-11"),
        1053: lambda: rent(1053, "2026-12"),
        1078: lambda: rent(1078, "2027-01"),
    }

    # --- Everything else: ordinary invoices that match their PO and receipt. ---

    for n in range(FIRST_INVOICE, LAST_INVOICE + 1):
        if n in planted:
            planted[n]()
            continue
        vendor_id = rng.choice(active)
        amount = round(rng.uniform(450, 24000), 2)
        if rng.random() < 0.15:  # a partial bill: invoice for part of the PO
            po_amount = round(amount * rng.uniform(1.2, 1.8), 2)
            po = add_po(vendor_id, invoice_date(n), po_amount, received_amount=amount)
        else:
            po = add_po(vendor_id, invoice_date(n), amount, closed=n <= 1040)
        add_invoice(n, vendor_id, amount, po, normal_status(n))

    # A few purchase orders that haven't been invoiced yet.
    for _ in range(4):
        add_po(rng.choice(active), START + timedelta(days=100), round(rng.uniform(800, 9000), 2), received=False)

    conn.commit()
    conn.close()
    return path


if __name__ == "__main__":
    path = build()
    conn = sqlite3.connect(path)
    for table in ["vendors", "purchase_orders", "receipts", "invoices"]:
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"{table:16} {count:4} rows")
    conn.close()
    print(f"Built {path}")
