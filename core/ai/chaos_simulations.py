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
            "name": "Out of Memory (OOM)",
            "logs": """
[2024-05-20 12:00:00] INFO: Initializing worker...
[2024-05-20 12:00:05] DEBUG: Allocating buffer for batch processing
[2024-05-20 12:00:06] CRITICAL: MemoryError: Unable to allocate 8.0 GiB for array with shape (1024, 1024, 1024) and data type float64
[2024-05-20 12:00:06] ERROR: Process 1234 terminated by signal 9 (SIGKILL)
            """,
            "project_context": {
                "project_name": "Data-Processor",
                "language": "Python/Pandas",
                "environment": "Production"
            },
            "broken_file": "processor/config.py",
            "broken_content": "BATCH_SIZE = 1000000\nCHUNK_SIZE = '8GB'",
            "fixed_content": "BATCH_SIZE = 10000\nCHUNK_SIZE = '512MB'",
            "search_block": "BATCH_SIZE = 1000000\nCHUNK_SIZE = '8GB'",
            "fixed_block": "BATCH_SIZE = 10000\nCHUNK_SIZE = '512MB'",
            "rationale": "The batch and chunk sizes are too large for the available system memory, leading to an OOM crash. Reducing them to safer values."
        }

    @staticmethod
    def get_permission_error():
        return {
            "name": "Permission Denied",
            "logs": """
2024-05-20 14:00:00 - ERROR - Failed to start logger
Traceback (most recent call last):
  File "main.py", line 45, in <module>
    with open('/var/log/app.log', 'a') as f:
PermissionError: [Errno 13] Permission denied: '/var/log/app.log'
            """,
            "project_context": {
                "project_name": "Sys-Logger",
                "language": "Python",
                "environment": "Staging"
            },
            "broken_file": "main.py",
            "broken_content": "LOG_FILE = '/var/log/app.log'",
            "fixed_content": "LOG_FILE = './logs/app.log'",
            "search_block": "LOG_FILE = '/var/log/app.log'",
            "fixed_block": "LOG_FILE = './logs/app.log'",
            "rationale": "The application is trying to write to a system-protected directory. Redirecting logs to a local subdirectory where the application has write permissions."
        }
