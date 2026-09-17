export enum IncidentStatus {
  DETECTED = "DETECTED",
  INVESTIGATING = "INVESTIGATING",
  VALIDATING = "VALIDATING",
  AWAITING_APPROVAL = "AWAITING_APPROVAL",
  APPROVED = "APPROVED",
  REMEDIATING = "REMEDIATING",
  VERIFYING = "VERIFYING",
  RESOLVED = "RESOLVED",
  REJECTED = "REJECTED",
  MANUAL_REVIEW = "MANUAL_REVIEW",
  REMEDIATION_FAILED = "REMEDIATION_FAILED",
  VERIFICATION_FAILED = "VERIFICATION_FAILED",
}

export enum Severity {
  LOW = "LOW",
  MEDIUM = "MEDIUM",
  HIGH = "HIGH",
  CRITICAL = "CRITICAL",
}

export enum PolicyStatus {
  NOT_EVALUATED = "NOT_EVALUATED",
  PASSED = "PASSED",
  FAILED = "FAILED",
  MANUAL_REVIEW = "MANUAL_REVIEW",
}

export enum ApprovalStatus {
  NOT_REQUIRED = "NOT_REQUIRED",
  PENDING = "PENDING",
  APPROVED = "APPROVED",
  REJECTED = "REJECTED",
}

export enum RemediationStatus {
  PENDING = "PENDING",
  IN_PROGRESS = "IN_PROGRESS",
  COMPLETED = "COMPLETED",
  FAILED = "FAILED",
}

export enum ResourceHealth {
  HEALTHY = "HEALTHY",
  UNHEALTHY = "UNHEALTHY",
  UNKNOWN = "UNKNOWN",
}

export enum AWSResourceType {
  LAMBDA_FUNCTION = "LAMBDA_FUNCTION",
  DYNAMODB_TABLE = "DYNAMODB_TABLE",
  EC2_INSTANCE = "EC2_INSTANCE",
  EVENT_RULE = "EVENT_RULE",
}

export enum AnomalyType {
  INVOCATION_SPIKE = "INVOCATION_SPIKE",
  ERROR_RATE_INCREASE = "ERROR_RATE_INCREASE",
  THROTTLING = "THROTTLING",
  LATENCY_SPIKE = "LATENCY_SPIKE",
}

export enum RemediationAction {
  TEMPORARILY_DISABLE_EVENT_RULE = "TEMPORARILY_DISABLE_EVENT_RULE",
  NO_ACTION = "NO_ACTION",
  MANUAL_REVIEW = "MANUAL_REVIEW",
}

export interface Incident {
  incidentId: string;
  resourceArn: string;
  resourceName: string;
  resourceType: AWSResourceType;
  region: string;
  anomalyType: AnomalyType;
  metric: string;
  baseline: number;
  observed: number;
  deviationRatio: number;
  severity: Severity;
  status: IncidentStatus;
  rootCause?: string;
  agentConfidence?: number;
  recommendedAction?: RemediationAction;
  policyStatus: PolicyStatus;
  approvalStatus: ApprovalStatus;
  remediationStatus?: RemediationStatus;
  createdAt: string;
  resolvedAt?: string;
}

export interface IncidentEvent {
  incidentId: string;
  eventId: string;
  eventType: string; // DETECTED, INCIDENT_CREATED, etc.
  timestamp: string;
  actor: string;
  summary: string;
  metadata?: Record<string, any>;
}

export interface AgentResponseSchema {
  root_cause: string;
  confidence: number;
  evidence: string[];
  recommended_action: RemediationAction;
}

export interface SharedError {
  code: string;
  message: string;
  service: string;
  incidentId?: string;
  retryable: boolean;
  timestamp: string;
  details?: Record<string, any>;
}
