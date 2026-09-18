# Cedar Policy Engine in Recourse

## Architecture

Recourse uses the open-source Cedar language for Authorization-as-Policy. This ensures the AI agent's proposed remediation actions are strictly constrained by deterministic, human-readable policy before execution.

## Amazon Verified Permissions Blocker

Initially, Amazon Verified Permissions (AVP) was targeted for this capability. However, the service cannot be used in the current AWS environment due to the following blocker:

- **Region:** ap-south-1
- **API Attempted:** `verifiedpermissions:CreatePolicyStore` (via CDK/CloudFormation and CLI)
- **Error Code:** `403 Forbidden` / `AccessDenied`
- **Error Message:** `The AWS Access Key Id needs a subscription for the service`

This indicates an account-level limitation with the AVP service rather than an IAM permission issue or regional unavailability.

## Fallback Implementation

Because of the above blocker, Recourse implements Authorization-as-Policy using `cedarpy`, the Python binding for the official Rust-based Cedar engine.

The policy validator is deployed as a Lambda function (`recourse-development-policy-validator`) which:
1. Receives the `incidentId`, `investigationId`, and `evidenceId`.
2. Gathers contextual facts from DynamoDB.
3. Invokes `cedarpy.is_authorized()` using the bundled `.cedar` files.
4. Persists the `PERMIT` or `FORBID` decision back to DynamoDB.

## Resource Enrollment Semantics

Resource enrollment is mandatory for any action that could eventually mutate AWS infrastructure. Non-mutating actions such as `NO_ACTION`, `MANUAL_INVESTIGATION`, and `REVIEW_CONFIGURATION` may be permitted for unmanaged resources when incident/resource linkage is valid.
