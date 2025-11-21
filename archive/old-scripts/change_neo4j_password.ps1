# Change Neo4j password using cypher-shell --change-password flag
$env:JAVA_HOME = "C:\Program Files\Eclipse Adoptium\jdk-21.0.9.10-hotspot"
$env:PATH = "$env:JAVA_HOME\bin;$env:PATH"
$env:NEO4J_HOME = "C:\Users\jpswi\.neo4j\neo4j-community-5.26.0"

$neo4jDir = "C:\Users\jpswi\.neo4j\neo4j-community-5.26.0"
$cypherShellPath = "$neo4jDir\bin\cypher-shell.bat"

Write-Host "Changing Neo4j password..." -ForegroundColor Yellow

# Use echo to pipe the new password to cypher-shell
$newPassword = "research123"
echo $newPassword | & $cypherShellPath -u neo4j -p research123 --change-password 2>&1

Write-Host "Password change completed" -ForegroundColor Green
