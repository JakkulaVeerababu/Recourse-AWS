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
