import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.handler import handle

def test_handler():
    response = handle({}, None)
    assert response['service'] == 'remediation-executor'
    assert response['status'] == 'ready'
