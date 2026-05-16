class ChaosGenerator:
    """
    Simulates common infrastructure and application failures.
    Provides raw logs, project context, and the expected fix data.
    """

    @staticmethod
    def get_db_failure():
        return {
            "name": "Database Connection Failure",
            "logs": """
INFO: Starting server...
INFO: Loading configurations...
DEBUG: Heartbeat sent
ERROR: psycopg2.OperationalError: could not connect to server: Connection refused
    Is the server running on host "localhost" (127.0.0.1) and accepting
    TCP/IP connections on port 5432?
INFO: Healthcheck failed
            """,
            "project_context": {
                "project_name": "WebShop",
                "language": "Python/Django",
                "environment": "Production"
            },
            "broken_file": "webshop/settings.py",
            "broken_content": "DATABASES = {\n    'default': {\n        'ENGINE': 'django.db.backends.postgresql',\n        'NAME': 'shop_db',\n        'HOST': 'localhost',\n        'PORT': '5432',\n    }\n}",
            "fixed_content": "DATABASES = {\n    'default': {\n        'ENGINE': 'django.db.backends.postgresql',\n        'NAME': 'shop_db',\n        'HOST': 'db',\n        'PORT': '5432',\n    }\n}",
            "search_block": "HOST': 'localhost'",
            "fixed_block": "HOST': 'db'",
            "rationale": "The application is trying to connect to 'localhost' instead of the 'db' service defined in the network."
        }

    @staticmethod
    def get_port_conflict():
        return {
            "name": "Port Already in Use",
            "logs": """
[2024-05-20 10:00:00] INFO: Booting worker with pid: 123
[2024-05-20 10:00:01] DEBUG: Checking port availability...
[2024-05-20 10:00:01] ERROR: [Errno 98] Address already in use
[2024-05-20 10:00:01] CRITICAL: Failed to bind to port 8000.
[2024-05-20 10:00:01] INFO: Shutting down...
            """,
            "project_context": {
                "project_name": "API-Gateway",
                "language": "Go/Fiber",
                "environment": "Staging"
            },
            "broken_file": "config.yaml",
            "broken_content": "server:\n  port: 8000\n  timeout: 30s",
            "fixed_content": "server:\n  port: 8080\n  timeout: 30s",
            "search_block": "port: 8000",
            "fixed_block": "port: 8080",
            "rationale": "Port 8000 is already occupied. Switching to 8080 to avoid the conflict."
        }

    @staticmethod
    def get_syntax_error():
        return {
            "name": "Python Syntax Error",
            "logs": """
  File "api/v1/endpoints.py", line 12
    def list_items(request)
                          ^
SyntaxError: invalid syntax
            """,
            "project_context": {
                "project_name": "Inventory-Service",
                "language": "Python/FastAPI",
                "environment": "Development"
            },
            "broken_file": "api/v1/endpoints.py",
            "broken_content": "@app.get('/items')\ndef list_items(request)\n    return []",
            "fixed_content": "@app.get('/items')\ndef list_items(request):\n    return []",
            "search_block": "def list_items(request)",
            "fixed_block": "def list_items(request):",
            "rationale": "Missing colon after function definition in api/v1/endpoints.py."
        }

    @staticmethod
    def get_dependency_failure():
        return {
            "name": "Missing Dependency / Typo",
            "logs": """
Traceback (most recent call last):
  File "app.py", line 1, in <module>
    import requestss
ModuleNotFoundError: No module named 'requestss'
            """,
            "project_context": {
                "project_name": "Data-Fetcher",
                "language": "Python/Script",
                "environment": "Development"
            },
            "broken_file": "app.py",
            "broken_content": "import requestss\n\ndef main():\n    pass",
            "fixed_content": "import requests\n\ndef main():\n    pass",
            "search_block": "import requestss",
            "fixed_block": "import requests",
            "rationale": "Fixed a typo in the import statement: 'requestss' to 'requests'."
        }

    @staticmethod
    def get_config_error():
        return {
            "name": "Missing Environment Variable",
            "logs": """
[CRITICAL] Application failed to start
Traceback (most recent call last):
  File "config.py", line 5, in <module>
    SECRET_KEY = os.environ["SECRET_KEEY"]
  File "<frozen os>", line 679, in __getitem__
KeyError: 'SECRET_KEEY'
            """,
            "project_context": {
                "project_name": "Auth-Service",
                "language": "Python/Django",
                "environment": "Production"
            },
            "broken_file": "config.py",
            "broken_content": "import os\n\nSECRET_KEY = os.environ[\"SECRET_KEEY\"]\nDEBUG = False",
            "fixed_content": "import os\n\nSECRET_KEY = os.environ[\"SECRET_KEY\"]\nDEBUG = False",
            "search_block": "os.environ[\"SECRET_KEEY\"]",
            "fixed_block": "os.environ[\"SECRET_KEY\"]",
            "rationale": "Corrected the environment variable key from 'SECRET_KEEY' to 'SECRET_KEY'."
        }
