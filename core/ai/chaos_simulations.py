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
    def get_missing_dependency():
        return {
            "name": "Missing Dependency",
            "logs": """
Traceback (most recent call last):
  File "app.py", line 1, in <module>
    import requests
ModuleNotFoundError: No module named 'requests'
            """,
            "project_context": {
                "project_name": "Data-Fetcher",
                "language": "Python",
                "environment": "Development"
            },
            "broken_file": "requirements.txt",
            "broken_content": "flask==3.0.0\npytest==8.0.0",
            "fixed_content": "flask==3.0.0\npytest==8.0.0\nrequests==2.31.0",
            "search_block": "pytest==8.0.0",
            "fixed_block": "pytest==8.0.0\nrequests==2.31.0",
            "rationale": "The 'requests' module is imported but not listed in requirements.txt."
        }

    @staticmethod
    def get_missing_env_var():
        return {
            "name": "Missing Environment Variable",
            "logs": """
django.core.exceptions.ImproperlyConfigured: The SECRET_KEY setting must not be empty.
            """,
            "project_context": {
                "project_name": "Secure-App",
                "language": "Python/Django",
                "environment": "Production"
            },
            "broken_file": ".env",
            "broken_content": "DEBUG=False\nALLOWED_HOSTS=*",
            "fixed_content": "DEBUG=False\nALLOWED_HOSTS=*\nSECRET_KEY=change-me-in-production",
            "search_block": "ALLOWED_HOSTS=*",
            "fixed_block": "ALLOWED_HOSTS=*\nSECRET_KEY=change-me-in-production",
            "rationale": "The application requires SECRET_KEY to be set in the environment via .env file."
        }
