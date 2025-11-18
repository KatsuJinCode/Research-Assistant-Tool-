#!/usr/bin/env python3
"""Change Neo4j password by accepting the forced password change."""

from neo4j import GraphDatabase

uri = "bolt://localhost:7687"
username = "neo4j"
old_password = "research123"
new_password = "research123"

print(f"Connecting to {uri}...")
print(f"Username: {username}")

try:
    # Connect with the initial password
    driver = GraphDatabase.driver(uri, auth=(username, old_password))

    # Try to verify connectivity (this will fail if password change is required)
    try:
        driver.verify_connectivity()
        print("Connected successfully! Password is already set correctly.")
    except Exception as e:
        print(f"Initial connection failed: {e}")
        print("Attempting to change password...")

        # Try to execute password change query
        with driver.session() as session:
            try:
                # Change password from old to new (even if same)
                session.run(f"ALTER CURRENT USER SET PASSWORD FROM '{old_password}' TO '{new_password}'")
                print(f"Password changed successfully from '{old_password}' to '{new_password}'")
            except Exception as change_error:
                print(f"Password change failed: {change_error}")

    driver.close()
    print("Driver closed.")

    # Try connecting again with the new password
    print("\nVerifying new connection...")
    driver2 = GraphDatabase.driver(uri, auth=(username, new_password))
    driver2.verify_connectivity()
    print("SUCCESS: Connected with new password!")
    driver2.close()

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
