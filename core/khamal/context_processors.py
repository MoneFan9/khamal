from django.conf import settings
import os

def pro_status(request):
    """
    Context processor to determine if Pro features are available.
    """
    pro_apps = ["pro.white_label", "pro.servers", "pro.ai_support"]
    is_pro_loaded = all(app in settings.INSTALLED_APPS for app in pro_apps)

    # Also check if the directory exists just in case
    pro_dir_exists = os.path.exists(os.path.join(settings.BASE_DIR.parent, "pro"))

    return {
        "is_pro_loaded": is_pro_loaded and pro_dir_exists
    }
