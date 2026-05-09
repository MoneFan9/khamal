import pytest
from unittest.mock import patch
from rest_framework import serializers
from projects.serializers import LocalSourceSerializer

def test_local_source_serializer_path_resolution_error():
    serializer = LocalSourceSerializer()

    with patch("projects.serializers.os.path.isabs", return_value=True):
        with patch("projects.serializers.os.path.realpath", side_effect=Exception("Path too long")):
            with pytest.raises(serializers.ValidationError) as excinfo:
                serializer.validate_host_path("/some/very/long/path")
            assert "Path resolution error" in str(excinfo.value)
