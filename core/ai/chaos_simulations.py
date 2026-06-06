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
    def get_oom_error():
        return {
            "name": "Out of Memory (OOM) Error",
            "logs": """
[2024-05-20 10:00:05] INFO: Processing batch #42
[2024-05-20 10:00:10] CRITICAL: Memory usage exceeded 95%
[2024-05-20 10:00:11] FATAL: OutOfMemoryError: Java heap space
[2024-05-20 10:00:11] INFO: Process terminated by OOM Killer
            """,
            "project_context": {
                "project_name": "Data-Processor",
                "language": "Java/Spring",
                "environment": "Production"
            },
            "broken_file": "nixpacks.toml",
            "broken_content": "[variables]\nJAVA_OPTS = \"-Xmx128m\"",
            "fixed_content": "[variables]\nJAVA_OPTS = \"-Xmx512m\"",
            "search_block": "JAVA_OPTS = \"-Xmx128m\"",
            "fixed_block": "JAVA_OPTS = \"-Xmx512m\"",
            "rationale": "The application ran out of memory. Increasing the JVM heap size in nixpacks.toml."
        }

    @staticmethod
    def get_permission_denied():
        return {
            "name": "Permission Denied",
            "logs": """
[2024-05-20 10:05:00] ERROR: PermissionError: [Errno 13] Permission denied: '/app/storage/logs/app.log'
[2024-05-20 10:05:00] CRITICAL: Failed to initialize log writer.
            """,
            "project_context": {
                "project_name": "Log-Aggregator",
                "language": "Python",
                "environment": "Production"
            },
            "broken_file": "scripts/setup.sh",
            "broken_content": "mkdir -p /app/storage/logs\nchmod 444 /app/storage/logs",
            "fixed_content": "mkdir -p /app/storage/logs\nchmod 755 /app/storage/logs",
            "search_block": "chmod 444 /app/storage/logs",
            "fixed_block": "chmod 755 /app/storage/logs",
            "rationale": "The application lacks write permissions to the log directory. Correcting chmod value."
        }

    @staticmethod
    def get_dependency_conflict():
        return {
            "name": "Dependency Version Conflict",
            "logs": """
ERROR: Cannot install -r requirements.txt (line 3) because of a version conflict.
The conflict is caused by:
    The user requested Django==5.0
    The app requires Django>=6.0.4
            """,
            "project_context": {
                "project_name": "Legacy-Portal",
                "language": "Python/Django",
                "environment": "Staging"
            },
            "broken_file": "requirements.txt",
            "broken_content": "django==5.0\ndjangorestframework==3.15.0",
            "fixed_content": "django>=6.0.4\ndjangorestframework==3.15.0",
            "search_block": "django==5.0",
            "fixed_block": "django>=6.0.4",
            "rationale": "Version conflict detected for Django. Updating requirements.txt to a compatible version."
        }
