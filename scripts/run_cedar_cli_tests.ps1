$cases = @(
    @{
        Name = "CASE A - NO_ACTION"
        Action = 'Recourse::Action::"NO_ACTION"'
        Context = @{ incidentSeverity = "HIGH"; evidenceCompleteness = "COMPLETE"; signalScore = 40; proposedRisk = "LOW"; requiresHumanApproval = $true; targetMatchesIncident = $true; incidentStatus = "INVESTIGATING"; investigationStage = "AGENT_COMPLETE" }
        Managed = $true
        Expected = "Allow"
    },
    @{
        Name = "CASE B - MANUAL_INVESTIGATION"
        Action = 'Recourse::Action::"MANUAL_INVESTIGATION"'
        Context = @{ incidentSeverity = "HIGH"; evidenceCompleteness = "COMPLETE"; signalScore = 40; proposedRisk = "LOW"; requiresHumanApproval = $true; targetMatchesIncident = $true; incidentStatus = "INVESTIGATING"; investigationStage = "AGENT_COMPLETE" }
        Managed = $true
        Expected = "Allow"
    },
    @{
        Name = "CASE C - DISABLE_EVENT_SOURCE safe"
        Action = 'Recourse::Action::"DISABLE_EVENT_SOURCE"'
        Context = @{ incidentSeverity = "HIGH"; evidenceCompleteness = "COMPLETE"; signalScore = 40; proposedRisk = "LOW"; requiresHumanApproval = $true; targetMatchesIncident = $true; incidentStatus = "INVESTIGATING"; investigationStage = "AGENT_COMPLETE" }
        Managed = $true
        Expected = "Allow"
    },
    @{
        Name = "CASE D - Missing Human Approval"
        Action = 'Recourse::Action::"DISABLE_EVENT_SOURCE"'
        Context = @{ incidentSeverity = "HIGH"; evidenceCompleteness = "COMPLETE"; signalScore = 40; proposedRisk = "LOW"; requiresHumanApproval = $false; targetMatchesIncident = $true; incidentStatus = "INVESTIGATING"; investigationStage = "AGENT_COMPLETE" }
        Managed = $true
        Expected = "Deny"
    },
    @{
        Name = "CASE E - Unmanaged Resource"
        Action = 'Recourse::Action::"DISABLE_EVENT_SOURCE"'
        Context = @{ incidentSeverity = "HIGH"; evidenceCompleteness = "COMPLETE"; signalScore = 40; proposedRisk = "LOW"; requiresHumanApproval = $true; targetMatchesIncident = $true; incidentStatus = "INVESTIGATING"; investigationStage = "AGENT_COMPLETE" }
        Managed = $false
        Expected = "Deny"
    },
    @{
        Name = "CASE F - Wrong Target"
        Action = 'Recourse::Action::"DISABLE_EVENT_SOURCE"'
        Context = @{ incidentSeverity = "HIGH"; evidenceCompleteness = "COMPLETE"; signalScore = 40; proposedRisk = "LOW"; requiresHumanApproval = $true; targetMatchesIncident = $false; incidentStatus = "INVESTIGATING"; investigationStage = "AGENT_COMPLETE" }
        Managed = $true
        Expected = "Deny"
    },
    @{
        Name = "CASE G - DELETE_FUNCTION unknown action"
        Action = 'Recourse::Action::"DELETE_FUNCTION"'
        Context = @{ incidentSeverity = "HIGH"; evidenceCompleteness = "COMPLETE"; signalScore = 40; proposedRisk = "LOW"; requiresHumanApproval = $true; targetMatchesIncident = $true; incidentStatus = "INVESTIGATING"; investigationStage = "AGENT_COMPLETE" }
        Managed = $true
        Expected = "Deny"
    },
    @{
        Name = "CASE H - LOW severity"
        Action = 'Recourse::Action::"DISABLE_EVENT_SOURCE"'
        Context = @{ incidentSeverity = "LOW"; evidenceCompleteness = "COMPLETE"; signalScore = 40; proposedRisk = "LOW"; requiresHumanApproval = $true; targetMatchesIncident = $true; incidentStatus = "INVESTIGATING"; investigationStage = "AGENT_COMPLETE" }
        Managed = $true
        Expected = "Deny"
    }
)

Get-Content policies\cedar\policies\investigation-actions.cedar, policies\cedar\policies\resource-safety.cedar | Set-Content policies.cedar

foreach ($case in $cases) {
    $req = @{
        principal = 'Recourse::Agent::"investigation-agent"'
        action = $case.Action
        resource = 'Recourse::AWSResource::"target"'
        context = $case.Context
    }
    $req | ConvertTo-Json -Depth 10 | Out-File request.json -Encoding utf8
    
    $entities = @(
        @{
            uid = @{ type = "Recourse::Agent"; id = "investigation-agent" }
            attrs = @{}
            parents = @()
        },
        @{
            uid = @{ type = "Recourse::AWSResource"; id = "target" }
            attrs = @{ recourseManaged = $case.Managed }
            parents = @()
        }
    )
    $entities | ConvertTo-Json -Depth 10 | Out-File entities.json -Encoding utf8
    
    $result = .\cedar authorize --schema policies\cedar\schema.cedarschema --policies policies.cedar --request-json request.json --entities entities.json 2>&1
    
    $decision = if ($result -match "ALLOW") { "Allow" } elseif ($result -match "DENY") { "Deny" } else { "Error: $result" }
    
    if ($decision -eq $case.Expected) {
        Write-Host "[OK] $($case.Name) -> $decision" -ForegroundColor Green
    } else {
        Write-Host "[FAIL] $($case.Name) -> Expected $($case.Expected), got $decision" -ForegroundColor Red
        Write-Host $result
    }
}
