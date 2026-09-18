import sys, os
import pytest
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.handler import handle

def test_handler_missing_incident_id():
    with pytest.raises(ValueError, match="Missing incident_id in input"):
        handle({}, None)
