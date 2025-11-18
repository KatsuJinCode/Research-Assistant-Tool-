# Set JAVA_HOME and reset Neo4j password
$env:JAVA_HOME = "C:\Program Files\Eclipse Adoptium\jdk-21.0.9.10-hotspot"
$env:PATH = "$env:JAVA_HOME\bin;$env:PATH"

Write-Host "Setting initial password..."
& "C:\Users\jpswi\.neo4j\neo4j-community-5.26.0\bin\neo4j-admin.bat" dbms set-initial-password research123

if ($LASTEXITCODE -eq 0) {
    Write-Host "Password set successfully!"
} else {
    Write-Host "Failed to set password"
    exit 1
}
