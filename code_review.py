import os

files = [
    'core/requirements.txt',
    'core/khamal/settings/base.py',
    'core/khamal/asgi.py',
    'core/projects/consumers.py',
    'core/projects/routing.py',
    'core/projects/urls.py',
    'core/projects/views.py',
    'core/templates/projects/deployment_logs.html'
]

for f in files:
    print(f"--- {f} ---")
    if os.path.exists(f):
        with open(f, 'r') as content:
            print(content.read())
    else:
        print("File not found")
    print("\n")
