# Recourse Architecture

## Overall Workflow

AI Investigates -> Policy Constrains -> Human Approves -> AWS Executes.

## Implemented (Phase 1 & Phase 2)
- **Monorepo Foundation**: npm workspaces containing frontend, CDK, shared types, and Python services.
- **Frontend Framework**: Next.js App Router with Tailwind CSS (ready state page).
- **Infrastructure Code**: CDK foundation stack and tagging standards.
- **Backend Scaffold**: Python Lambda placeholder services with pytest.
- **Demo Workload**: A controlled, bounded AWS workload (Processor + Load Generator) driven by SSM Parameter Store to safely simulate production traffic spikes for anomaly detection.
  - *Safety Controls*: Primarily controlled via a bounded invocation count, batching, and a hard duration loop (observed ~48.5s cut-off).
  - *Concurrency*: Unreserved concurrency deployed due to fresh AWS account limitations; relies on soft state boundaries instead of hard AWS Lambda concurrency limits.
## Planned (Future Phases)
- **Monitoring**: CloudWatch anomaly detection alarms.
- **Routing**: EventBridge routing to Step Functions.
- **Investigation**: Strands + Amazon Bedrock agent for root cause analysis.
- **Persistence**: DynamoDB audit timeline.
- **Remediation**: Least-privilege automated executor.
