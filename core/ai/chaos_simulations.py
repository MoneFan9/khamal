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
    def get_oom_failure():
        return {
            "name": "Out of Memory (OOM)",
            "logs": """
[2024-05-20 12:00:00] INFO: Processing large dataset...
[2024-05-20 12:00:15] DEBUG: Memory usage: 7.2GB / 8GB
[2024-05-20 12:00:20] CRITICAL: Memory limit exceeded.
[2024-05-20 12:00:20] FATAL: kernel: [12345.678] Out of memory: Kill process 1234 (python3) score 950 or sacrifice child
[2024-05-20 12:00:21] INFO: Worker killed.
            """,
            "project_context": {
                "project_name": "Data-Processor",
                "language": "Python/Pandas",
                "environment": "Production"
            },
            "broken_file": "processor/worker.py",
            "broken_content": "df = pd.read_csv('massive_data.csv')\n# Process all at once",
            "fixed_content": "for chunk in pd.read_csv('massive_data.csv', chunksize=1000):\n    # Process chunk by chunk",
            "search_block": "df = pd.read_csv('massive_data.csv')\n# Process all at once",
            "fixed_block": "for chunk in pd.read_csv('massive_data.csv', chunksize=1000):\n    # Process chunk by chunk",
            "rationale": "The application is crashing due to OOM when loading the entire CSV. Using chunking to reduce memory footprint."
        }

    @staticmethod
    def get_permission_denied():
        return {
            "name": "Permission Denied",
            "logs": """
INFO: Initializing logger...
ERROR: [Errno 13] Permission denied: '/var/log/app.log'
CRITICAL: Could not open log file for writing.
            """,
            "project_context": {
                "project_name": "Core-Service",
                "language": "Python",
                "environment": "Production"
            },
            "broken_file": "core/config.py",
            "broken_content": "LOG_FILE = '/var/log/app.log'",
            "fixed_content": "LOG_FILE = './logs/app.log'",
            "search_block": "LOG_FILE = '/var/log/app.log'",
            "fixed_block": "LOG_FILE = './logs/app.log'",
            "rationale": "The application lacks permissions to write to /var/log/. Switching to a local logs directory."
        }
