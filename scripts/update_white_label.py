
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'khamal.settings.development')
django.setup()

from pro.white_label.models import WhiteLabelConfiguration

def update_white_label():
    config = WhiteLabelConfiguration.objects.filter(is_active=True).first()
    if not config:
        print("No active white label config found.")
        return

    # Override the primary gradient to a red theme to verify it works
    config.custom_css = """
    :root {
        --primary-gradient-from: #ef4444; /* red-500 */
        --primary-gradient-to: #b91c1c;   /* red-700 */
    }
    """
    config.save()
    print("White label configuration updated with red theme.")

if __name__ == "__main__":
    update_white_label()
