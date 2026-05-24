import pytest
import docker
import os
import time
from projects.models import Project
from projects.services import provision_database
from projects.backup_services import backup_project_database, restore_project_database
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.mark.django_db
class TestDisasterRecovery:
    @pytest.fixture(autouse=True)
    def setup_method(self, db):
        self.user = User.objects.create_user(username="dr_user", password="password")
        self.project = Project.objects.create(name="DRProject", owner=self.user)
        self.client = docker.from_env()

    def test_postgres_backup_restore_lifecycle(self):
        # 1. Provision Postgres
        container = provision_database(self.project, "postgres")
        assert container.status == "running" or container.status == "created"

        # Wait for postgres to be ready and create a table
        time.sleep(5)
        container.exec_run("psql -U khamal -d khamal -c 'CREATE TABLE test_dr (id serial PRIMARY KEY, data text);'")
        container.exec_run("psql -U khamal -d khamal -c \"INSERT INTO test_dr (data) VALUES ('disaster_recovery_test');\"")

        # Verify data exists
        res = container.exec_run("psql -U khamal -d khamal -t -c 'SELECT data FROM test_dr;'")
        assert "disaster_recovery_test" in res.output.decode()

        # 2. Perform Backup
        backup_path = "/tmp/postgres_dr_test.sql"
        backup_project_database(self.project, "postgres", backup_path)
        assert os.path.exists(backup_path)
        assert os.path.getsize(backup_path) > 0

        # 3. Simulate Disaster (Destroy container and volume)
        container.remove(force=True)
        try:
            vol = self.client.volumes.get(f"khamal-data-postgres-{self.project.id}")
            vol.remove(force=True)
        except docker.errors.NotFound:
            pass

        # 4. Re-provision (Empty DB)
        new_container = provision_database(self.project, "postgres")
        time.sleep(5)

        # Verify table does NOT exist
        res = new_container.exec_run("psql -U khamal -d khamal -t -c \"SELECT to_regclass('public.test_dr');\"")
        assert "test_dr" not in res.output.decode() or res.output.decode().strip() == ""

        # 5. Restore from Backup
        restore_project_database(self.project, "postgres", backup_path)

        # 6. Verify data recovered
        res = new_container.exec_run("psql -U khamal -d khamal -t -c 'SELECT data FROM test_dr;'")
        assert "disaster_recovery_test" in res.output.decode()

        # Cleanup
        if os.path.exists(backup_path):
            os.remove(backup_path)
        new_container.remove(force=True)
        try:
            self.client.volumes.get(f"khamal-data-postgres-{self.project.id}").remove(force=True)
        except:
            pass

    def test_redis_backup_restore_lifecycle(self):
        # 1. Provision Redis
        container = provision_database(self.project, "redis")
        time.sleep(2)

        # Insert data
        auth = f"-a {self.project.db_redis_password} --no-auth-warning"
        container.exec_run(f"redis-cli {auth} SET dr_key disaster_recovery_redis")
        res = container.exec_run(f"redis-cli {auth} GET dr_key")
        assert "disaster_recovery_redis" in res.output.decode()

        # 2. Perform Backup
        backup_path = "/tmp/redis_dr_test.rdb"
        backup_project_database(self.project, "redis", backup_path)
        assert os.path.exists(backup_path)

        # 3. Simulate Disaster
        container.remove(force=True)
        try:
            vol = self.client.volumes.get(f"khamal-data-redis-{self.project.id}")
            vol.remove(force=True)
        except docker.errors.NotFound:
            pass

        # 4. Re-provision
        new_container = provision_database(self.project, "redis")
        time.sleep(2)
        res = new_container.exec_run("redis-cli GET dr_key")
        assert "disaster_recovery_redis" not in res.output.decode()

        # 5. Restore
        restore_project_database(self.project, "redis", backup_path)

        # 6. Verify
        # Redis might need a second to reload if we just started it or replaced RDB
        time.sleep(2)
        auth = f"-a {self.project.db_redis_password} --no-auth-warning"
        res = new_container.exec_run(f"redis-cli {auth} GET dr_key")
        assert "disaster_recovery_redis" in res.output.decode()

        # Cleanup
        if os.path.exists(backup_path):
            os.remove(backup_path)
        new_container.remove(force=True)
        try:
            self.client.volumes.get(f"khamal-data-redis-{self.project.id}").remove(force=True)
        except:
            pass
