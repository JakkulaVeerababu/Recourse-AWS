import json
import logging
import os
import time
import boto3
from datetime import datetime, timezone

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

ssm = boto3.client('ssm')
lambda_client = boto3.client('lambda')

NORMAL_BATCH_SIZE = int(os.environ.get('NORMAL_BATCH_SIZE', 25))
ANOMALY_BATCH_SIZE = int(os.environ.get('ANOMALY_BATCH_SIZE', 100))
ANOMALY_MAX_DURATION_SECONDS = int(os.environ.get('ANOMALY_MAX_DURATION_SECONDS', 45))
ANOMALY_MAX_INVOCATIONS = int(os.environ.get('ANOMALY_MAX_INVOCATIONS', 500))

DEMO_PROCESSOR_NAME = os.environ.get('DEMO_PROCESSOR_NAME')
STATE_PARAMETER_NAME = os.environ.get('STATE_PARAMETER_NAME')

def get_demo_state():
    try:
        response = ssm.get_parameter(Name=STATE_PARAMETER_NAME)
        return json.loads(response['Parameter']['Value'])
    except Exception as e:
        logger.error(f"Failed to fetch state from SSM: {e}")
        return {"mode": "NORMAL", "anomaly_start_time": None, "invocations": 0}

def set_demo_state(state):
    try:
        ssm.put_parameter(
            Name=STATE_PARAMETER_NAME,
            Value=json.dumps(state),
            Type='String',
            Overwrite=True
        )
    except Exception as e:
        logger.error(f"Failed to update state in SSM: {e}")

def invoke_processor_batch(batch_size, mode):
    logger.info(f"Invoking {batch_size} demo-processors in {mode} mode")
    payload = json.dumps({'demoMode': mode, 'source': 'demo-load-generator'})
    
    success_count = 0
    for _ in range(batch_size):
        try:
            lambda_client.invoke(
                FunctionName=DEMO_PROCESSOR_NAME,
                InvocationType='Event',
                Payload=payload
            )
            success_count += 1
        except Exception as e:
            logger.error(f"Failed to invoke demo-processor: {e}")
            
    return success_count

def handle(event, context):
    logger.info("Demo load generator started")
    
    if not DEMO_PROCESSOR_NAME or not STATE_PARAMETER_NAME:
        logger.error("Missing DEMO_PROCESSOR_NAME or STATE_PARAMETER_NAME environment variables")
        return {"status": "error", "message": "Missing config"}
        
    start_time = time.time()
    
    state = get_demo_state()
    mode = state.get('mode', 'NORMAL')
    
    if mode == 'STOPPED':
        logger.info("Demo mode is STOPPED. Skipping invocations.")
        return {"status": "stopped"}
        
    elif mode == 'NORMAL':
        # Send 1 normal batch of traffic and exit
        invocations = invoke_processor_batch(NORMAL_BATCH_SIZE, 'NORMAL')
        return {"status": "normal", "invocations": invocations}
        
    elif mode == 'ANOMALY':
        logger.info("Demo mode is ANOMALY. Generating spike traffic.")
        
        anomaly_start_str = state.get('anomaly_start_time')
        if not anomaly_start_str:
            # We just transitioned to anomaly, record start time
            anomaly_start_str = datetime.now(timezone.utc).isoformat()
            state['anomaly_start_time'] = anomaly_start_str
            set_demo_state(state)
            
        anomaly_start = datetime.fromisoformat(anomaly_start_str).replace(tzinfo=None)
        
        # Bounded generation loop
        while True:
            # Refresh state to allow manual stop
            current_state = get_demo_state()
            if current_state.get('mode') != 'ANOMALY':
                logger.info("Mode changed from ANOMALY. Halting generation.")
                break
                
            elapsed = (datetime.utcnow() - anomaly_start).total_seconds()
            total_invoked = current_state.get('invocations', 0)
            
            if elapsed >= ANOMALY_MAX_DURATION_SECONDS:
                logger.info(f"Anomaly max duration ({ANOMALY_MAX_DURATION_SECONDS}s) reached. Reverting to NORMAL.")
                current_state['mode'] = 'NORMAL'
                current_state['anomaly_start_time'] = None
                current_state['invocations'] = 0
                set_demo_state(current_state)
                break
                
            if total_invoked >= ANOMALY_MAX_INVOCATIONS:
                logger.info(f"Anomaly max invocations ({ANOMALY_MAX_INVOCATIONS}) reached. Reverting to NORMAL.")
                current_state['mode'] = 'NORMAL'
                current_state['anomaly_start_time'] = None
                current_state['invocations'] = 0
                set_demo_state(current_state)
                break
                
            # Perform a batch
            batch_to_send = min(ANOMALY_BATCH_SIZE, ANOMALY_MAX_INVOCATIONS - total_invoked)
            invoked = invoke_processor_batch(batch_to_send, 'ANOMALY')
            
            # Update count
            current_state['invocations'] = total_invoked + invoked
            set_demo_state(current_state)
            
            # Sleep to pace the batch out, unless time is up
            if (datetime.utcnow() - anomaly_start).total_seconds() < ANOMALY_MAX_DURATION_SECONDS:
                time.sleep(10)
                
        return {"status": "anomaly_finished"}
