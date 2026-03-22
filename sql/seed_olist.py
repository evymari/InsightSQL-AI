import psycopg2
import csv
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

DATA_DIR = Path(__file__).parent / "data" / "olist"

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:<PASSWORD>@localhost:5432/insightsql"
)

TABLE_CSV_MAPPING = {
    "olist_customers_dataset": "customers",
    "olist_sellers_dataset": "sellers",
    "olist_products_dataset": "products",
    "olist_orders_dataset": "orders",
    "olist_order_items_dataset": "order_items",
    "olist_order_payments_dataset": "order_payments",
    "olist_order_reviews_dataset": "order_reviews",
}

EXPECTED_COUNTS = {
    "customers": 99_441,
    "sellers": 3_095,
    "products": 32_951,
    "orders": 99_441,
    "order_items": 112_650,
    "order_payments": 103_886,
    "order_reviews": 99_224,
}


def get_connection():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print(f"  ✗ Error conectando a PostgreSQL: {e}")
        raise


def truncate_table(conn, table: str) -> None:
    with conn.cursor() as cur:
        cur.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE")
    conn.commit()


def import_csv(csv_filename: str, table_name: str) -> int:
    csv_path = DATA_DIR / csv_filename

    if not csv_path.exists():
        print(f"  ⚠ Archivo no encontrado: {csv_path}")
        return 0

    conn = get_connection()

    try:
        truncate_table(conn, table_name)

        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            columns = reader.fieldnames
            placeholders = ",".join(["%s"] * len(columns))
            column_names = ",".join(columns)

            rows = list(reader)

            batch_size = 1000
            total_inserted = 0

            for i in range(0, len(rows), batch_size):
                batch = rows[i : i + batch_size]
                values = []
                for row in batch:
                    row_values = [None if val == "" else val for val in row.values()]
                    values.append(row_values)

                with conn.cursor() as cur:
                    cur.executemany(
                        f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders}) ON CONFLICT DO NOTHING",
                        values,
                    )
                conn.commit()
                total_inserted += len(batch)
                print(f"    {table_name}: {total_inserted}/{len(rows)}")

        print(f"  ✓ {table_name}: {total_inserted:,} filas importadas")
        return total_inserted

    except Exception as e:
        conn.rollback()
        print(f"  ✗ Error en {table_name}: {e}")
        raise
    finally:
        conn.close()


def verify_counts() -> dict:
    conn = get_connection()
    counts = {}
    try:
        with conn.cursor() as cur:
            for table in EXPECTED_COUNTS:
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                result = cur.fetchone()
                counts[table] = result[0] if result else 0
    finally:
        conn.close()
    return counts


def main():
    print("=" * 50)
    print("InsightSQL - Importando dataset Olist")
    print("=" * 50)
    print()

    print(f"Conectando a PostgreSQL...")
    parts = DATABASE_URL.rsplit("/", 1)
    db_name = parts[-1].split("?")[0] if len(parts) > 1 else "unknown"
    print(f"  Base de datos: {db_name}")
    print()

    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT version()")
            result = cur.fetchone()
            version = result[0] if result else "Unknown"
        conn.close()
        print(f"  ✓ PostgreSQL conectado")
        print(f"    {version.split(',')[0] if version else 'Unknown'}")
    except Exception as e:
        print(f"  ✗ No se pudo conectar a PostgreSQL")
        print(f"  Error: {e}")
        print()
        print("Verifica que:")
        print("  1. PostgreSQL esté corriendo")
        print("  2. La base de datos 'insightsql' exista")
        print("  3. El schema.sql haya sido ejecutado")
        print()
        print("Comandos de verificación:")
        print("  psql -d insightsql -c '\\dt'")
        sys.exit(1)

    print()
    print("Importando datos...")
    print()

    for csv_name, table_name in TABLE_CSV_MAPPING.items():
        print(f"→ {table_name}")
        try:
            import_csv(f"{csv_name}.csv", table_name)
        except Exception:
            print(f"  ✗ Falló la importación de {table_name}")
            sys.exit(1)

    print()
    print("=" * 50)
    print("Verificando conteos...")
    print("=" * 50)
    print()

    try:
        counts = verify_counts()
        all_ok = True

        for table, expected in EXPECTED_COUNTS.items():
            actual = counts.get(table, 0)
            status = "✓" if actual >= expected * 0.95 else "✗"
            if actual < expected * 0.95:
                all_ok = False
            print(f"  {status} {table}: {actual:,} (esperado ~{expected:,})")

        print()

        if all_ok:
            print("=" * 50)
            print("✓ Importación completada exitosamente!")
            print("=" * 50)
        else:
            print("=" * 50)
            print("⚠ Algunas tablas no tienen la cantidad esperada")
            print("=" * 50)
            sys.exit(1)
    except Exception as e:
        print(f"  ✗ Error verificando: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
