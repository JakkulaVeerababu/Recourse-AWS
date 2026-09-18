
foreach ($dir in Get-ChildItem services -Directory) {
    Write-Host "Testing $($dir.Name)"
    Push-Location $dir.FullName
    $env:PYTHONPATH = "c:\Users\LENOVO\Desktop\Recourse\$($dir.FullName)"
    $env:INCIDENT_TABLE_NAME = "recourse-development-incidents"
    $env:TABLE_NAME = "recourse-development-incidents"
    & "c:\Users\LENOVO\Desktop\Recourse\.venv\Scripts\python.exe" -m pytest -q
    Pop-Location
}
