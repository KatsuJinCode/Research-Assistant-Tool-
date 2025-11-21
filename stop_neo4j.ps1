# Stop all Java processes (Neo4j)
Get-Process | Where-Object {$_.ProcessName -eq 'java'} | ForEach-Object {
    Write-Host "Stopping process $($_.Id)..."
    Stop-Process -Id $_.Id -Force
}
Write-Host "All Java processes stopped"
