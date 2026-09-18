from typing import Dict, Any, List

def build_configuration_evidence(config_data: Dict[str, Any]) -> tuple:
    facts = {}
    signals = []

    if not config_data:
        return facts, signals

    facts['runtime'] = config_data.get('Runtime', config_data.get('runtime'))
    facts['memorySize'] = config_data.get('MemorySize', config_data.get('memorySize'))
    facts['timeout'] = config_data.get('Timeout', config_data.get('timeout'))
    
    # Analyze reserved concurrency (from metadata or config)
    # The config structure depends on how context-collector serialized it. 
    # Usually it's in config_data, or meta. Let's look for standard fields.
    rc = config_data.get('ReservedConcurrency', config_data.get('reserved_concurrency', config_data.get('reservedConcurrency')))
    if rc is None:
        rc = config_data.get('reservedConcurrency')

    facts['reservedConcurrency'] = rc

    tracing = config_data.get('TracingConfig', {}).get('Mode', config_data.get('tracingConfig', {}).get('mode'))
    facts['tracing'] = tracing
    
    env = config_data.get('EnvironmentKeys', config_data.get('environment', {}).get('variables', {}))
    if isinstance(env, dict):
        facts['environmentVariableKeys'] = list(env.keys())
    elif isinstance(env, list):
        facts['environmentVariableKeys'] = env
    
    # Generate signals
    if rc is None or rc == "UNRESERVED":
        signals.append("RESERVED_CONCURRENCY_UNSET")
        
    mem = facts.get('memorySize')
    if mem and isinstance(mem, (int, float)) and mem <= 256:
        signals.append("LOW_MEMORY_CONFIGURATION")
        
    timeout = facts.get('timeout')
    if timeout and isinstance(timeout, (int, float)) and timeout <= 5:
        signals.append("SHORT_TIMEOUT_CONFIGURATION")
        
    if not tracing or tracing == 'PassThrough':
        signals.append("TRACING_DISABLED")

    return facts, signals
