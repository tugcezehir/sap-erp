from .db import connect


def main() -> None:
    with connect() as con:
        tables = [
            r[0]
            for r in con.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
        ]
        for t in tables:
            n = con.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
            print(f"\n=== {t} ({n} satır) ===")
            for _, name, ctype, _, _, pk in con.execute(f'PRAGMA table_info("{t}")'):
                print(f"  {name:<32} {ctype:<12} {'PK' if pk else ''}")
            print("  -- örnek satırlar --")
            for row in con.execute(f'SELECT * FROM "{t}" LIMIT 3'):
                print("  ", row)


if __name__ == "__main__":
    main()