// Allow NO_ACTION if target matches incident and stage is AGENT_COMPLETE
@id("permit-no-action")
permit (
    principal,
    action == Recourse::Action::"NO_ACTION",
    resource
)
when {
    context.investigationStage == "AGENT_COMPLETE"
};

// Allow MANUAL_INVESTIGATION if stage is AGENT_COMPLETE
@id("permit-manual-investigation")
permit (
    principal,
    action == Recourse::Action::"MANUAL_INVESTIGATION",
    resource
)
when {
    context.investigationStage == "AGENT_COMPLETE"
};

// Allow REVIEW_CONFIGURATION if stage is AGENT_COMPLETE
@id("permit-review-configuration")
permit (
    principal,
    action == Recourse::Action::"REVIEW_CONFIGURATION",
    resource
)
when {
    context.investigationStage == "AGENT_COMPLETE"
};

// Allow DISABLE_EVENT_SOURCE only if severity is HIGH or CRITICAL
@id("permit-disable-event-source-high-severity")
permit (
    principal,
    action == Recourse::Action::"DISABLE_EVENT_SOURCE",
    resource
)
when {
    context.investigationStage == "AGENT_COMPLETE" &&
    (context.incidentSeverity == "HIGH" || context.incidentSeverity == "CRITICAL")
};

// Allow REDUCE_INVOCATION_SOURCE only if severity is HIGH or CRITICAL
@id("permit-reduce-invocation-source-high-severity")
permit (
    principal,
    action == Recourse::Action::"REDUCE_INVOCATION_SOURCE",
    resource
)
when {
    context.investigationStage == "AGENT_COMPLETE" &&
    (context.incidentSeverity == "HIGH" || context.incidentSeverity == "CRITICAL")
};

// Absolutely forbid any mutating action if human approval is missing
@id("forbid-mutating-without-approval")
forbid (
    principal,
    action in [
        Recourse::Action::"DISABLE_EVENT_SOURCE",
        Recourse::Action::"REDUCE_INVOCATION_SOURCE"
    ],
    resource
)
when {
    context.requiresHumanApproval == false
};

// Forbid if target does not match incident
@id("forbid-target-mismatch")
forbid (
    principal,
    action,
    resource
)
when {
    context.targetMatchesIncident == false
};

// Forbid mutating actions if resource is not explicitly recourse-managed
@id("forbid-unmanaged-mutations")
forbid (
    principal,
    action in [
        Recourse::Action::"DISABLE_EVENT_SOURCE",
        Recourse::Action::"REDUCE_INVOCATION_SOURCE"
    ],
    resource
)
when {
    resource.recourseManaged == false
};

// Forbid if investigation is not complete
@id("forbid-incomplete-investigation")
forbid (
    principal,
    action,
    resource
)
when {
    context.investigationStage != "AGENT_COMPLETE"
};

