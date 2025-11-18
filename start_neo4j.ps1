# Start Neo4j in console mode
$env:JAVA_HOME = "C:\Program Files\Eclipse Adoptium\jdk-21.0.9.10-hotspot"
$env:PATH = "$env:JAVA_HOME\bin;$env:PATH"
$env:NEO4J_HOME = "C:\Users\jpswi\.neo4j\neo4j-community-5.26.0"

$neo4jDir = "C:\Users\jpswi\.neo4j\neo4j-community-5.26.0"
$neo4jPath = "$neo4jDir\bin\neo4j.bat"

Write-Host "Starting Neo4j in console mode..." -ForegroundColor Yellow
$neo4jProcess = Start-Process -FilePath "powershell.exe" `
    -ArgumentList "-NoExit", "-Command", "& '$neo4jPath' console" `
    -WorkingDirectory $neo4jDir `
    -WindowStyle Minimized `
    -PassThru

Write-Host "Neo4j process started (PID: $($neo4jProcess.Id))" -ForegroundColor Green
Write-Host "Waiting for Neo4j to initialize (20 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 20

# Verify Neo4j is running
$portTest = Test-NetConnection -ComputerName localhost -Port 7687 -WarningAction SilentlyContinue
if ($portTest.TcpTestSucceeded) {
    Write-Host "Neo4j is running on bolt://localhost:7687" -ForegroundColor Green
} else {
    Write-Host "WARNING: Neo4j may not be fully started on port 7687" -ForegroundColor Yellow
}
