"""
Integration tests for Project API endpoints
Tests the complete multi-database project lifecycle
"""

import pytest
import json
import logging
from unittest.mock import patch

logger = logging.getLogger(__name__)


class TestProjectAPIIntegration:
    """Integration tests for Project API with real database operations."""

    @pytest.fixture
    def app(self):
        """Create Flask app instance for testing."""
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

        from web_ui.app import app
        app.config['TESTING'] = True
        return app

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return app.test_client()

    @pytest.fixture
    def db_manager(self):
        """Get DatabaseManager instance."""
        from backend.database.neo4j_client import Neo4jClient
        client = Neo4jClient()
        return client.database_manager

    @pytest.fixture
    def cleanup_test_projects(self, db_manager):
        """Cleanup any test projects after tests."""
        yield
        # Cleanup after test
        test_databases = [
            'project_integration_test',
            'project_test_project_1',
            'project_test_project_2',
            'project_renamed_project'
        ]
        for db_name in test_databases:
            try:
                db_manager.drop_database(db_name)
            except Exception as e:
                logger.warning(f"Cleanup failed for {db_name}: {e}")

    @pytest.mark.integration
    def test_create_project(self, client, db_manager, cleanup_test_projects):
        """Test creating a new project with actual database."""
        response = client.post('/api/projects',
                               data=json.dumps({
                                   'name': 'Integration Test',
                                   'description': 'Test project for integration',
                                   'color': '#FF5722'
                               }),
                               content_type='application/json')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'project' in data

        project = data['project']
        assert project['name'] == 'Integration Test'
        assert project['description'] == 'Test project for integration'
        assert project['color'] == '#FF5722'
        assert 'database_name' in project
        assert project['database_name'] == 'project_integration_test'

        # Verify database was actually created
        assert db_manager.database_exists('project_integration_test') is True

    @pytest.mark.integration
    def test_list_projects(self, client, db_manager, cleanup_test_projects):
        """Test listing all projects."""
        # Create test projects
        db_manager.create_database('project_test_project_1', wait=True)
        db_manager.initialize_database_schema('project_test_project_1')

        with db_manager.get_session(db_manager.SYSTEM_DATABASE) as session:
            session.run("""
                CREATE (p:Project {
                    id: $id,
                    name: $name,
                    database_name: $database_name,
                    is_active: false,
                    created_at: datetime(),
                    updated_at: datetime()
                })
            """, {
                'id': 'test_proj_1',
                'name': 'Test Project 1',
                'database_name': 'project_test_project_1'
            })

        response = client.get('/api/projects')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'projects' in data
        assert len(data['projects']) >= 1

        # Find our test project
        test_project = next((p for p in data['projects'] if p['name'] == 'Test Project 1'), None)
        assert test_project is not None
        assert 'node_count' in test_project

    @pytest.mark.integration
    def test_switch_project(self, client, db_manager, cleanup_test_projects):
        """Test switching between projects."""
        # Create two test projects
        db_manager.create_database('project_test_project_1', wait=True)
        db_manager.create_database('project_test_project_2', wait=True)

        with db_manager.get_session(db_manager.SYSTEM_DATABASE) as session:
            # Create project 1
            session.run("""
                CREATE (p:Project {
                    id: $id,
                    name: $name,
                    database_name: $database_name,
                    is_active: true,
                    created_at: datetime(),
                    updated_at: datetime()
                })
            """, {
                'id': 'test_proj_1',
                'name': 'Test Project 1',
                'database_name': 'project_test_project_1'
            })

            # Create project 2
            session.run("""
                CREATE (p:Project {
                    id: $id,
                    name: $name,
                    database_name: $database_name,
                    is_active: false,
                    created_at: datetime(),
                    updated_at: datetime()
                })
            """, {
                'id': 'test_proj_2',
                'name': 'Test Project 2',
                'database_name': 'project_test_project_2'
            })

        # Switch to project 2
        response = client.post('/api/projects/test_proj_2/switch')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['project']['id'] == 'test_proj_2'

        # Verify active database changed
        from backend.database.neo4j_client import Neo4jClient
        client_instance = Neo4jClient()
        assert client_instance.active_database == 'project_test_project_2'

        # Verify is_active flags in database
        with db_manager.get_session(db_manager.SYSTEM_DATABASE) as session:
            result = session.run("""
                MATCH (p:Project)
                WHERE p.id IN ['test_proj_1', 'test_proj_2']
                RETURN p.id as id, p.is_active as is_active
                ORDER BY p.id
            """)

            projects = list(result)
            assert len(projects) == 2
            proj1 = next(p for p in projects if p['id'] == 'test_proj_1')
            proj2 = next(p for p in projects if p['id'] == 'test_proj_2')
            assert proj1['is_active'] is False
            assert proj2['is_active'] is True

    @pytest.mark.integration
    def test_update_project(self, client, db_manager, cleanup_test_projects):
        """Test updating project metadata."""
        # Create test project
        db_manager.create_database('project_test_project_1', wait=True)

        with db_manager.get_session(db_manager.SYSTEM_DATABASE) as session:
            session.run("""
                CREATE (p:Project {
                    id: $id,
                    name: $name,
                    database_name: $database_name,
                    description: $description,
                    color: $color,
                    is_active: false,
                    created_at: datetime(),
                    updated_at: datetime()
                })
            """, {
                'id': 'test_proj_1',
                'name': 'Original Name',
                'database_name': 'project_test_project_1',
                'description': 'Original description',
                'color': '#FF0000'
            })

        # Update project
        response = client.put('/api/projects/test_proj_1',
                              data=json.dumps({
                                  'name': 'Renamed Project',
                                  'description': 'Updated description',
                                  'color': '#00FF00'
                              }),
                              content_type='application/json')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['project']['name'] == 'Renamed Project'
        assert data['project']['description'] == 'Updated description'
        assert data['project']['color'] == '#00FF00'

        # Verify in database
        with db_manager.get_session(db_manager.SYSTEM_DATABASE) as session:
            result = session.run("""
                MATCH (p:Project {id: 'test_proj_1'})
                RETURN p.name as name, p.description as description, p.color as color
            """)
            record = result.single()
            assert record['name'] == 'Renamed Project'
            assert record['description'] == 'Updated description'
            assert record['color'] == '#00FF00'

    @pytest.mark.integration
    def test_delete_project(self, client, db_manager, cleanup_test_projects):
        """Test deleting a project and its database."""
        # Create test project
        db_manager.create_database('project_test_project_1', wait=True)

        with db_manager.get_session(db_manager.SYSTEM_DATABASE) as session:
            session.run("""
                CREATE (p:Project {
                    id: $id,
                    name: $name,
                    database_name: $database_name,
                    is_active: false,
                    created_at: datetime(),
                    updated_at: datetime()
                })
            """, {
                'id': 'test_proj_1',
                'name': 'Test Project 1',
                'database_name': 'project_test_project_1'
            })

        # Verify database exists
        assert db_manager.database_exists('project_test_project_1') is True

        # Delete project
        response = client.delete('/api/projects/test_proj_1')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True

        # Verify database was dropped
        assert db_manager.database_exists('project_test_project_1') is False

        # Verify metadata was removed
        with db_manager.get_session(db_manager.SYSTEM_DATABASE) as session:
            result = session.run("""
                MATCH (p:Project {id: 'test_proj_1'})
                RETURN p
            """)
            assert result.single() is None

    @pytest.mark.integration
    def test_delete_active_project_fails(self, client, db_manager, cleanup_test_projects):
        """Test that deleting active project is prevented."""
        # Create active test project
        db_manager.create_database('project_test_project_1', wait=True)

        with db_manager.get_session(db_manager.SYSTEM_DATABASE) as session:
            session.run("""
                CREATE (p:Project {
                    id: $id,
                    name: $name,
                    database_name: $database_name,
                    is_active: true,
                    created_at: datetime(),
                    updated_at: datetime()
                })
            """, {
                'id': 'test_proj_1',
                'name': 'Active Project',
                'database_name': 'project_test_project_1'
            })

        # Try to delete active project
        response = client.delete('/api/projects/test_proj_1')

        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'active project' in data['error'].lower()

        # Verify database still exists
        assert db_manager.database_exists('project_test_project_1') is True

    @pytest.mark.integration
    def test_get_active_project(self, client, db_manager, cleanup_test_projects):
        """Test getting the active project."""
        # Create test project and set as active
        db_manager.create_database('project_test_project_1', wait=True)

        with db_manager.get_session(db_manager.SYSTEM_DATABASE) as session:
            # First set all projects inactive
            session.run("MATCH (p:Project) SET p.is_active = false")

            # Create and activate test project
            session.run("""
                CREATE (p:Project {
                    id: $id,
                    name: $name,
                    database_name: $database_name,
                    is_active: true,
                    created_at: datetime(),
                    updated_at: datetime()
                })
            """, {
                'id': 'test_proj_1',
                'name': 'Active Test Project',
                'database_name': 'project_test_project_1'
            })

        # Get active project
        response = client.get('/api/projects/active')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'project' in data
        assert data['project']['name'] == 'Active Test Project'
        assert data['project']['is_active'] is True

    @pytest.mark.integration
    def test_get_project_stats(self, client, db_manager, cleanup_test_projects):
        """Test getting project statistics."""
        # Create test project
        db_manager.create_database('project_test_project_1', wait=True)
        db_manager.initialize_database_schema('project_test_project_1')

        with db_manager.get_session(db_manager.SYSTEM_DATABASE) as session:
            session.run("""
                CREATE (p:Project {
                    id: $id,
                    name: $name,
                    database_name: $database_name,
                    is_active: false,
                    created_at: datetime(),
                    updated_at: datetime()
                })
            """, {
                'id': 'test_proj_1',
                'name': 'Stats Test Project',
                'database_name': 'project_test_project_1'
            })

        # Add some test data to the project database
        with db_manager.get_session('project_test_project_1') as session:
            session.run("""
                CREATE (d:Document {id: 'doc1', title: 'Test Doc'})
                CREATE (c:Claim {id: 'claim1', text: 'Test Claim'})
                CREATE (e:Evidence {id: 'ev1', text: 'Test Evidence'})
            """)

        # Get stats
        response = client.get('/api/projects/test_proj_1/stats')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['project_id'] == 'test_proj_1'
        assert data['name'] == 'Stats Test Project'
        assert data['total_nodes'] == 3
        assert data['document_count'] == 1
        assert data['claim_count'] == 1
        assert data['evidence_count'] == 1

    @pytest.mark.integration
    def test_create_project_duplicate_name(self, client, db_manager, cleanup_test_projects):
        """Test creating projects with duplicate names (should create different databases)."""
        # Create first project
        response1 = client.post('/api/projects',
                                data=json.dumps({
                                    'name': 'Duplicate Test',
                                    'description': 'First project'
                                }),
                                content_type='application/json')

        assert response1.status_code == 200
        data1 = json.loads(response1.data)
        assert data1['success'] is True

        # Create second project with same name (should get unique ID)
        response2 = client.post('/api/projects',
                                data=json.dumps({
                                    'name': 'Duplicate Test',
                                    'description': 'Second project'
                                }),
                                content_type='application/json')

        assert response2.status_code == 200
        data2 = json.loads(response2.data)
        assert data2['success'] is True

        # Verify they have different IDs
        assert data1['project']['id'] != data2['project']['id']


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-m', 'integration'])
