# Phase 6: Deterministic Investigation Evidence Layer

The Deterministic Investigation Evidence Layer is a critical phase in the Recourse incident lifecycle. Its primary goal is to convert raw AWS telemetry (metrics, logs, and configuration) collected during Phase 5 into a compact, structured, and auditable "evidence package."

## Core Principles

1.  **Deterministic Analysis:** No generative AI, LLMs, or non-deterministic logic is used in this layer. The analysis relies on strict mathematical and pattern-matching rules.
2.  **Fact vs. Inference:** This layer produces facts and signals (e.g., "Invocation volume is 5x the baseline"). It explicitly avoids root cause attribution or diagnoses (e.g., "This is a traffic spike attack"), which is the responsibility of the AI investigator (Phase 7).
3.  **Idempotency:** Evidence generation is strictly idempotent. Repeated invocations for the same incident and context ID will produce the identical `evidenceId` and bypass redundant side effects.

## Architecture

The Evidence Layer consists of a new Step Functions state and a dedicated Lambda function (`evidence-builder`).

### `evidence-builder` Service
-   **Runtime:** Python 3.12
-   **Execution Model:** Triggered by Step Functions. Fetches context from DynamoDB, analyzes it, and persists the evidence back to DynamoDB.
-   **Security:** Operates with least-privilege IAM roles, restricted strictly to DynamoDB operations on the incident table.

## Evidence Structure

An Evidence Package contains the following modules:
*   **Metric Evidence:** Facts and signals extracted from CloudWatch metrics (Invocations, Errors, Throttles, Duration). Includes derived statistics like deviation ratios and error rates.
*   **Log Evidence:** Extracted error patterns (e.g., `Timeout`, `AccessDenied`) and their occurrence counts.
*   **Configuration Evidence:** Extracted properties (e.g., Memory, Timeout) and deterministic signals (e.g., `LOW_MEMORY_CONFIGURATION`).
*   **Correlations:** Simple rule-based correlations across different evidence domains (e.g., `TRAFFIC_INCREASE_WITHOUT_ERROR_SPIKE`).
*   **Summary Facts:** A templated summary array presenting the core findings as compact strings.
*   **Signal Score & Level:** An aggregated intensity score (0-100) and discrete level (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).

## Signal Scoring System

The scoring system assigns deterministic weights to observed signals. It serves as an indicator of anomaly intensity, **not** AI confidence or severity.

-   **Invocation Deviation:** `SIGNIFICANT_INCREASE` (+40), `STRONG_INCREASE` (+30), `ELEVATED` (+15).
-   **Error Spikes:** `ERROR_SPIKE` (+30), `ERRORS_PRESENT` (+20).
-   **Throttling:** `THROTTLING_SIGNIFICANT` (+30), `THROTTLING_PRESENT` (+20).
-   **Log Patterns:** Extracted patterns like `OutOfMemory` or `AccessDenied` add score dynamically.

## Idempotency and State Management

-   **Evidence ID Strategy:** `UUID5` with a fixed namespace, hashing `incidentId:contextId`.
-   **Database Write:** Handled via conditional DynamoDB `PutItem` (`attribute_not_exists(PK)`). Conflicts are safely swallowed as success.
-   **Timeline Management:** Step Functions dynamically creates deterministic event IDs for `EVIDENCE_PREPARED` to ensure timeline purity during retries.
-   **State Transition:** Upon success, the incident `investigationStage` advances to `EVIDENCE_READY`, while the primary `status` remains `INVESTIGATING`.
