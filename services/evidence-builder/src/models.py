from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional
from decimal import Decimal

@dataclass
class MetricFact:
    metric: str
    status: str
    baseline: Optional[Decimal] = None
    observed: Optional[Decimal] = None
    deviationRatio: Optional[Decimal] = None
    direction: Optional[str] = None
    signal: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ErrorFact:
    status: str
    signal: Optional[str] = None
    totalErrors: Optional[Decimal] = None
    errorRate: Optional[Decimal] = None

@dataclass
class ThrottleFact:
    status: str
    signal: Optional[str] = None
    totalThrottles: Optional[Decimal] = None

@dataclass
class DurationFact:
    status: str
    signal: Optional[str] = None
    medianDuration: Optional[Decimal] = None
    peakDuration: Optional[Decimal] = None

@dataclass
class MetricEvidence:
    invocations: MetricFact
    errors: ErrorFact
    throttles: ThrottleFact
    duration: DurationFact

@dataclass
class ConfigurationEvidence:
    facts: Dict[str, Any]
    signals: List[str]

@dataclass
class LogSignal:
    pattern: str
    count: int
    signal: str

@dataclass
class LogEvidence:
    patterns: List[Dict[str, Any]]
    signals: List[Dict[str, Any]] # Will hold asdict(LogSignal)

@dataclass
class Correlation:
    type: str
    statement: str

@dataclass
class SummaryFact:
    type: str
    statement: str

@dataclass
class EvidencePackage:
    evidenceId: str
    incidentId: str
    contextId: str
    evidenceCompleteness: str
    metricEvidence: Dict[str, Any]
    configurationEvidence: Dict[str, Any]
    logEvidence: Dict[str, Any]
    correlations: List[Dict[str, Any]]
    summaryFacts: List[Dict[str, Any]]
    signalScore: int
    signalLevel: str
    generatedAt: str
    schemaVersion: str = "1.0"
    resources: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
