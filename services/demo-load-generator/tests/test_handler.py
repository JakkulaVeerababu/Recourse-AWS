import os
import json
from unittest.mock import patch, MagicMock

with patch.dict(os.environ, {
    'DEMO_PROCESSOR_NAME': 'mock-processor',
    'STATE_PARAMETER_NAME': 'mock-state',
    'NORMAL_BATCH_SIZE': '25'
}):
    from src.handler import handle

@patch('src.handler.ssm')
@patch("src.handler.lambda_client")
def test_demo_load_generator_normal(mock_lambda, mock_ssm):
    # Mock SSM response
    mock_ssm.get_parameter.return_value = {
        'Parameter': {
            'Value': json.dumps({"mode": "NORMAL", "invocations": 0})
        }
    }
    
    response = handle({}, None)
    
    assert response['status'] == 'normal'
    assert response['invocations'] == 25
    assert mock_lambda.invoke.call_count == 25
