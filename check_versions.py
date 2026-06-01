import requests
import pkg_resources

packages = [
    "Django", "django-environ", "psycopg2-binary", "djangorestframework",
    "Pillow", "docker", "GitPython", "requests", "channels", "daphne", "Twisted"
]

for pkg in packages:
    try:
        response = requests.get(f"https://pypi.org/pypi/{pkg}/json")
        if response.status_code == 200:
            data = response.json()
            latest = data["info"]["version"]
            print(f"{pkg}: {latest}")
        else:
            print(f"{pkg}: Not found on PyPI")
    except Exception as e:
        print(f"{pkg}: Error {e}")
