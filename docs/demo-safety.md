# Demo Workload Safety Boundaries

Because Recourse automatically monitors and responds to workloads, we must ensure our target demo workload is heavily bounded to prevent infinite loops, run-away concurrency, or unconstrained cloud spend.

## Core Limits

1. **Anomaly Duration Limit**: Anomalies automatically shut off after 45 seconds.
2. **Anomaly Invocation Limit**: No more than 500 lambda invocations per anomaly spike.
3. **SSM-Driven State**: The load generator checks SSM Parameter Store `/recourse/demo/state` on every execution to verify if it should run in `NORMAL`, `ANOMALY`, or `STOPPED` mode.
4. **Self-Healing State**: If limits are breached, the load generator writes `NORMAL` back to SSM to prevent the anomaly from continuing.

## Recourse Managed Tags

We have fixed the Phase 1 bug where `RecourseManaged=true` was globally applied.
Currently, ONLY the EventBridge Rule for the `demo-load-generator` is tagged with `RecourseManaged=true`.
This ensures Recourse will only attempt remediation on this specific authorized resource, and will never touch core infrastructure or unrelated components.

## Hard-coded Concurrency

The `demo-processor` Lambda is restricted via `reservedConcurrentExecutions: 10` in CDK. Even if the load generator fails to throttle, AWS itself will reject requests past 10 concurrent executions, ensuring low costs.
