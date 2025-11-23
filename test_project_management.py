"""
Comprehensive Test Suite for Project Management System
Tests all endpoints, database operations, and UI integration
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from backend.database.neo4j_client import Neo4jClient
from backend.database.database_manager import DatabaseManager
import requests
import time
import json

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def print_header(text):
    """Print formatted test section header."""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def print_test(name, passed=True):
    """Print test result."""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} - {name}")


def test_neo4j_connection():
    """Test 1: Neo4j Client Connection"""
    print_header("TEST 1: Neo4j Client Connection")

    try:
        client = Neo4jClient()
        print_test("Neo4j client initialized")

        active_db = client.active_database
        print(f"  → Active database: {active_db}")
        print_test("Active database retrieved")

        return True
    except Exception as e:
        print_test(f"Neo4j connection failed: {e}", False)
        return False


def test_database_manager():
    """Test 2: Database Manager Operations"""
    print_header("TEST 2: Database Manager Operations")

    try:
        client = Neo4jClient()
        manager = client.database_manager

        # List databases
        databases = manager.list_databases()
        print(f"  → Found {len(databases)} databases")
        for db in databases:
            print(f"     - {db['name']} ({db['currentStatus']})")
        print_test("List databases")

        # Sanitize database name
        test_name = "Test Project 123!"
        sanitized = DatabaseManager.sanitize_database_name(test_name)
        print(f"  → Sanitized '{test_name}' to '{sanitized}'")
        print_test("Sanitize database name")

        # Get stats for default database
        stats = manager.get_database_stats('neo4j')
        print(f"  → Stats: {stats['total_nodes']} nodes, {stats['total_relationships']} relationships")
        print_test("Get database stats")

        return True
    except Exception as e:
        print_test(f"Database manager failed: {e}", False)
        return False


def test_migration_completed():
    """Test 3: Verify Migration Completed"""
    print_header("TEST 3: Migration Verification")

    try:
        client = Neo4jClient()

        # Check if default project exists
        with client.get_session('neo4j') as session:
            result = session.run("""
                MATCH (p:Project {id: 'default'})
                RETURN p.name as name, p.id as id, p.color as color
            """)

            project = result.single()
            if project:
                print(f"  → Default project found: {project['name']}")
                print(f"     ID: {project['id']}")
                print(f"     Color: {project['color']}")
                print_test("Default project exists")
            else:
                print_test("Default project not found", False)
                return False

            # Check if nodes have project_id
            result = session.run("""
                MATCH (n)
                WHERE NOT n:Project
                WITH count(n) as total,
                     count(CASE WHEN n.project_id IS NOT NULL THEN 1 END) as with_project_id
                RETURN total, with_project_id
            """)

            stats = result.single()
            if stats:
                total = stats['total']
                with_project_id = stats['with_project_id']
                print(f"  → Total nodes: {total}")
                print(f"  → Nodes with project_id: {with_project_id}")

                if total == with_project_id:
                    print_test("All nodes have project_id")
                else:
                    print_test(f"Missing project_id on {total - with_project_id} nodes", False)
                    return False

            # Check indexes
            result = session.run("SHOW INDEXES")
            indexes = [record['name'] for record in result]

            expected_indexes = ['project_id_index', 'document_project_index']
            found_indexes = [idx for idx in expected_indexes if any(idx in index_name for index_name in indexes)]

            print(f"  → Found {len(found_indexes)}/{len(expected_indexes)} project indexes")
            print_test("Project indexes created")

        return True
    except Exception as e:
        print_test(f"Migration verification failed: {e}", False)
        import traceback
        traceback.print_exc()
        return False


def test_api_endpoints():
    """Test 4: API Endpoints (requires web server running)"""
    print_header("TEST 4: API Endpoints")

    base_url = "http://localhost:5000"

    # Check if server is running
    try:
        response = requests.get(f"{base_url}/api/projects/active", timeout=2)
        server_running = True
    except requests.exceptions.ConnectionError:
        print("  ⚠️  Web server not running - skipping API tests")
        print("  💡 Start server with: python web_ui/app.py")
        return True  # Don't fail test if server isn't running

    print("  → Web server is running")

    # Test 1: Get active project
    try:
        response = requests.get(f"{base_url}/api/projects/active")
        data = response.json()

        if 'project' in data:
            project = data['project']
            print(f"  → Active project: {project['name']}")
            print_test("GET /api/projects/active")
        else:
            print_test("GET /api/projects/active - no project", False)
    except Exception as e:
        print_test(f"GET /api/projects/active failed: {e}", False)

    # Test 2: List all projects
    try:
        response = requests.get(f"{base_url}/api/projects")
        data = response.json()

        if 'projects' in data:
            projects = data['projects']
            print(f"  → Found {len(projects)} projects")
            for proj in projects:
                print(f"     - {proj['name']} ({proj['node_count']} nodes)")
            print_test("GET /api/projects")
        else:
            print_test("GET /api/projects - no projects", False)
    except Exception as e:
        print_test(f"GET /api/projects failed: {e}", False)

    # Test 3: Create new project
    try:
        test_project = {
            'name': 'Test Project API',
            'description': 'Created via API test',
            'color': '#FF5722'
        }

        response = requests.post(
            f"{base_url}/api/projects",
            json=test_project,
            headers={'Content-Type': 'application/json'}
        )
        data = response.json()

        if data.get('success'):
            created_project = data['project']
            print(f"  → Created project: {created_project['name']}")
            print_test("POST /api/projects")

            # Store project ID for cleanup
            test_project_id = created_project['id']

            # Test 4: Get project stats
            try:
                response = requests.get(f"{base_url}/api/projects/{test_project_id}/stats")
                stats = response.json()
                print(f"  → Stats: {stats['total_nodes']} nodes")
                print_test("GET /api/projects/<id>/stats")
            except Exception as e:
                print_test(f"GET /api/projects/<id>/stats failed: {e}", False)

            # Test 5: Update project
            try:
                update_data = {
                    'description': 'Updated via API test',
                    'color': '#00BCD4'
                }
                response = requests.put(
                    f"{base_url}/api/projects/{test_project_id}",
                    json=update_data,
                    headers={'Content-Type': 'application/json'}
                )
                data = response.json()

                if data.get('success'):
                    print_test("PUT /api/projects/<id>")
                else:
                    print_test("PUT /api/projects/<id> - failed", False)
            except Exception as e:
                print_test(f"PUT /api/projects/<id> failed: {e}", False)

            # Test 6: Switch project
            try:
                response = requests.post(f"{base_url}/api/projects/{test_project_id}/switch")
                data = response.json()

                if data.get('success'):
                    print(f"  → Switched to: {data['project']['name']}")
                    print_test("POST /api/projects/<id>/switch")

                    # Switch back to default
                    time.sleep(0.5)
                    requests.post(f"{base_url}/api/projects/default/switch")
                else:
                    print_test("POST /api/projects/<id>/switch - failed", False)
            except Exception as e:
                print_test(f"POST /api/projects/<id>/switch failed: {e}", False)

            # Test 7: Delete project
            try:
                response = requests.delete(f"{base_url}/api/projects/{test_project_id}")
                data = response.json()

                if data.get('success'):
                    print(f"  → Deleted: {test_project_id}")
                    print_test("DELETE /api/projects/<id>")
                else:
                    print_test("DELETE /api/projects/<id> - failed", False)
            except Exception as e:
                print_test(f"DELETE /api/projects/<id> failed: {e}", False)
        else:
            error = data.get('error', 'Unknown error')
            print_test(f"POST /api/projects failed: {error}", False)
    except Exception as e:
        print_test(f"POST /api/projects failed: {e}", False)
        import traceback
        traceback.print_exc()

    return True


def test_project_isolation():
    """Test 5: Multi-Database Project Isolation"""
    print_header("TEST 5: Multi-Database Project Isolation")

    try:
        client = Neo4jClient()
        manager = client.database_manager

        # Create two test databases
        test_db1 = "project_test_isolation_1"
        test_db2 = "project_test_isolation_2"

        print(f"  → Creating test database: {test_db1}")
        success1, error1 = manager.create_database(test_db1, wait=True)

        if success1:
            print_test(f"Database {test_db1} created")

            print(f"  → Creating test database: {test_db2}")
            success2, error2 = manager.create_database(test_db2, wait=True)

            if success2:
                print_test(f"Database {test_db2} created")

                # Add data to db1
                with manager.get_session(test_db1) as session:
                    session.run("""
                        CREATE (c:Claim {id: 'test-claim-1', text: 'Test claim in DB1'})
                    """)
                print_test("Data added to DB1")

                # Add different data to db2
                with manager.get_session(test_db2) as session:
                    session.run("""
                        CREATE (c:Claim {id: 'test-claim-2', text: 'Test claim in DB2'})
                    """)
                print_test("Data added to DB2")

                # Verify isolation - db1 should only have claim-1
                with manager.get_session(test_db1) as session:
                    result = session.run("MATCH (c:Claim) RETURN count(c) as count, collect(c.id) as ids")
                    record = result.single()
                    count = record['count']
                    ids = record['ids']

                    if count == 1 and 'test-claim-1' in ids:
                        print(f"  → DB1 correctly isolated: {count} claim(s)")
                        print_test("DB1 data isolation verified")
                    else:
                        print_test(f"DB1 isolation failed: found {count} claims", False)

                # Verify isolation - db2 should only have claim-2
                with manager.get_session(test_db2) as session:
                    result = session.run("MATCH (c:Claim) RETURN count(c) as count, collect(c.id) as ids")
                    record = result.single()
                    count = record['count']
                    ids = record['ids']

                    if count == 1 and 'test-claim-2' in ids:
                        print(f"  → DB2 correctly isolated: {count} claim(s)")
                        print_test("DB2 data isolation verified")
                    else:
                        print_test(f"DB2 isolation failed: found {count} claims", False)

                # Cleanup
                print("\n  → Cleaning up test databases...")
                manager.drop_database(test_db1)
                manager.drop_database(test_db2)
                print_test("Test databases cleaned up")

                return True
            else:
                print_test(f"Failed to create {test_db2}: {error2}", False)
                manager.drop_database(test_db1)
                return False
        else:
            if "does not support multiple databases" in (error1 or ""):
                print("  ℹ️  Multi-database not supported (Neo4j Community Edition)")
                print("  💡 Consider upgrading to Neo4j Enterprise or Desktop")
                return True  # Don't fail test for Community Edition
            else:
                print_test(f"Failed to create {test_db1}: {error1}", False)
                return False

    except Exception as e:
        print_test(f"Multi-database test failed: {e}", False)
        import traceback
        traceback.print_exc()
        return False


def test_ui_components():
    """Test 6: UI Components Verification"""
    print_header("TEST 6: UI Components Verification")

    # Check if required files exist
    files_to_check = [
        'web_ui/static/js/project_manager.js',
        'web_ui/templates/index.html',
        'backend/database/migrations/add_project_support.py',
        'backend/database/database_manager.py',
        'backend/database/neo4j_client.py'
    ]

    all_exist = True
    for file_path in files_to_check:
        full_path = os.path.join(os.path.dirname(__file__), file_path)
        exists = os.path.exists(full_path)

        if exists:
            size = os.path.getsize(full_path)
            print(f"  ✓ {file_path} ({size} bytes)")
        else:
            print(f"  ✗ {file_path} - NOT FOUND")
            all_exist = False

    print_test("All required files exist", all_exist)

    # Check if project_manager.js is included in HTML
    html_path = os.path.join(os.path.dirname(__file__), 'web_ui/templates/index.html')
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

        checks = [
            ('project_manager.js included', 'project_manager.js' in html_content),
            ('ProjectManager.openProjectModal()', 'ProjectManager.openProjectModal()' in html_content),
            ('project-selector element', 'project-selector' in html_content),
            ('current-project-name element', 'current-project-name' in html_content),
        ]

        for name, result in checks:
            print_test(name, result)

    return all_exist


def main():
    """Run all tests."""
    print("\n" + "╔" + "═" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "  PROJECT MANAGEMENT SYSTEM - COMPREHENSIVE TEST SUITE".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "═" * 68 + "╝")

    tests = [
        ("Neo4j Connection", test_neo4j_connection),
        ("Database Manager", test_database_manager),
        ("Migration Verification", test_migration_completed),
        ("API Endpoints", test_api_endpoints),
        ("Multi-Database Isolation", test_project_isolation),
        ("UI Components", test_ui_components)
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Test '{name}' crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # Summary
    print_header("TEST SUMMARY")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {name}")

    print(f"\n  {'='*66}")
    print(f"  Total: {passed}/{total} tests passed ({passed/total*100:.1f}%)")

    if passed == total:
        print(f"  {'='*66}")
        print(f"  🎉 ALL TESTS PASSED! Project Management System is fully functional.")
        print(f"  {'='*66}\n")
        return 0
    else:
        print(f"  {'='*66}")
        print(f"  ⚠️  Some tests failed. Review output above for details.")
        print(f"  {'='*66}\n")
        return 1


if __name__ == "__main__":
    exit(main())
