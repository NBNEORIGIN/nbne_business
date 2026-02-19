"""Clean up all non-NBNE demo tenant data from the production database.

Uses raw SQL with session_replication_role = replica to bypass FK triggers.
"""
import os
import sys
import django

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection

KEEP_IDS_QUERY = "SELECT id FROM tenants_settings WHERE slug IN ('nbne', 'mind-department')"

with connection.cursor() as c:
    # Show current state
    c.execute("SELECT id, slug, business_name FROM tenants_settings ORDER BY id")
    print("Current tenants:")
    for row in c.fetchall():
        print(f"  id={row[0]} slug={row[1]} name={row[2]}")

    # Get IDs to remove
    c.execute(f"SELECT id, slug FROM tenants_settings WHERE slug NOT IN ('nbne', 'mind-department')")
    remove = c.fetchall()
    if not remove:
        print("Nothing to clean up.")
        sys.exit(0)

    remove_ids = [r[0] for r in remove]
    print(f"\nRemoving tenant IDs: {remove_ids}")

    # Disable FK trigger checks for this session
    c.execute("SET session_replication_role = replica")

    # Find ALL tables with tenant_id
    c.execute("""
        SELECT table_name FROM information_schema.columns
        WHERE column_name = 'tenant_id' AND table_schema = 'public'
        AND table_name != 'tenants_settings'
    """)
    tables = [r[0] for r in c.fetchall()]

    placeholders = ','.join(['%s'] * len(remove_ids))

    # Delete from all tenant-scoped tables
    for table in tables:
        c.execute(f'DELETE FROM "{table}" WHERE tenant_id IN ({placeholders})', remove_ids)
        if c.rowcount > 0:
            print(f"  Deleted {c.rowcount} rows from {table}")

    # Delete orphan demo users (may not have tenant_id pointing to removed tenants)
    c.execute("DELETE FROM accounts_user WHERE email LIKE '%%@demo.local' OR email LIKE '%%@salon-x.demo' OR email LIKE '%%@restaurant-x.demo' OR email LIKE '%%@health-club-x.demo'")
    if c.rowcount > 0:
        print(f"  Deleted {c.rowcount} orphan demo users")

    # Delete tenant rows
    c.execute(f'DELETE FROM tenants_settings WHERE id IN ({placeholders})', remove_ids)
    print(f"  Deleted {c.rowcount} tenant rows")

    # Re-enable FK checks
    c.execute("SET session_replication_role = DEFAULT")

# Final state
with connection.cursor() as c:
    print("\n=== Final state ===")
    c.execute("SELECT id, slug, business_name FROM tenants_settings ORDER BY id")
    print("Tenants:")
    for row in c.fetchall():
        print(f"  id={row[0]} slug={row[1]} name={row[2]}")
    c.execute("SELECT username, email FROM accounts_user ORDER BY username")
    print("Users:")
    for row in c.fetchall():
        print(f"  {row[0]} ({row[1]})")
