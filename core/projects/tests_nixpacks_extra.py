import pytest
from core.projects.nixpacks import NixpacksPlan

def test_nixpacks_plan_has_postgres():
    plan = NixpacksPlan(packages=["python3", "postgresql"])
    assert plan.has_postgres is True
    assert plan.has_redis is False

    plan = NixpacksPlan(apt_packages=["libpq-dev"])
    assert plan.has_postgres is True

    plan = NixpacksPlan(libraries=["pg"])
    assert plan.has_postgres is True

    plan = NixpacksPlan(packages=["something-postgresql-else"])
    assert plan.has_postgres is True

def test_nixpacks_plan_has_redis():
    plan = NixpacksPlan(packages=["redis"])
    assert plan.has_redis is True
    assert plan.has_postgres is False

    plan = NixpacksPlan(apt_packages=["redis-server"])
    assert plan.has_redis is True

    plan = NixpacksPlan(libraries=["hiredis"])
    assert plan.has_redis is True

def test_nixpacks_plan_from_dict_malformed():
    data = {
        "phases": {
            "setup": {
                "nixPkgs": "not-a-list",
                "nixLibs": None
            }
        },
        "variables": "not-a-dict"
    }
    plan = NixpacksPlan.from_dict(data)
    assert plan.packages == []
    assert plan.libraries == []
    assert plan.variables == {}

def test_nixpacks_plan_from_dict_start_fallback():
    data = {
        "start": {"cmd": "python manage.py runserver"}
    }
    plan = NixpacksPlan.from_dict(data)
    assert plan.start_cmd == "python manage.py runserver"
