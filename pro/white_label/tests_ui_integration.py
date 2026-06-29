import pytest
from pro.white_label.models import WhiteLabelConfiguration

@pytest.mark.django_db
def test_white_label_css_injection_order(client):
    """
    Test that the White Label custom CSS is injected after the base styles.
    """
    custom_css = ".custom-class { color: red; }"
    WhiteLabelConfiguration.objects.create(
        name="Test Config",
        custom_css=custom_css,
        is_active=True
    )

    response = client.get("/")
    html = response.content.decode()

    # Check that Tailwind CDN is before custom CSS
    tailwind_index = html.find("cdn.tailwindcss.com")
    custom_css_index = html.find(custom_css)

    assert tailwind_index != -1
    assert custom_css_index != -1
    assert tailwind_index < custom_css_index
    assert '<style id="white-label-css">' in html
