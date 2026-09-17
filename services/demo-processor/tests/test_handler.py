import sys
import os
import importlib.util

spec = importlib.util.spec_from_file_location("demo_processor_handler", os.path.join(os.path.dirname(__file__), '../src/handler.py'))
handler_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(handler_mod)
handle = handler_mod.handle

class MockContext:
    def __init__(self):
        self.aws_request_id = 'test-request-id'

def test_demo_processor_handler():
    context = MockContext()
    event = {'demoMode': 'NORMAL', 'source': 'pytest'}
    
    response = handle(event, context)
    
    assert response['service'] == 'demo-processor'
    assert response['status'] == 'processed'
    assert response['requestId'] == 'test-request-id'
