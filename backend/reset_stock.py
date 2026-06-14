"""Zet de voorraad van ALLE pods op een vaste waarde (default 0).

    python3 reset_stock.py        # alles op 0
    python3 reset_stock.py 3      # alles op 3
"""
import sys

from db import get_db


def main():
    waarde = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    db = get_db()
    n = db.execute("UPDATE pod SET stock = ?", (waarde,)).rowcount
    db.commit()
    db.close()
    print(f"{n} pods op stock {waarde}")


if __name__ == "__main__":
    main()
