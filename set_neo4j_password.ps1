# Set Neo4j password
$env:JAVA_HOME = "C:\Program Files\Eclipse Adoptium\jdk-21.0.9.10-hotspot"
$env:PATH = "$env:JAVA_HOME\bin;$env:PATH"
$env:NEO4J_HOME = "C:\Users\jpswi\.neo4j\neo4j-community-5.26.0"

Set-Location "C:\Users\jpswi\.neo4j\neo4j-community-5.26.0"
& ".\bin\neo4j-admin.bat" dbms set-initial-password research123
