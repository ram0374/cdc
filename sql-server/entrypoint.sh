#!/bin/bash

# Check for SA_PASSWORD
if [ -z "$SA_PASSWORD" ]; then
  echo "ERROR: SA_PASSWORD environment variable is not set."
  echo "Please provide it via -e SA_PASSWORD=YourStrong!Passw0rd"
  exit 1
fi

# Start SQL Server in the background
/opt/mssql/bin/sqlservr &

# Wait for SQL Server to be available
echo "Waiting for SQL Server to start..."
sleep 20

# Enable SQL Server Agent
echo "Enabling SQL Server Agent..."
/opt/mssql-tools/bin/sqlcmd -S localhost -U SA -P "$SA_PASSWORD" -Q "sp_configure 'show advanced options', 1; RECONFIGURE;"
/opt/mssql-tools/bin/sqlcmd -S localhost -U SA -P "$SA_PASSWORD" -Q "sp_configure 'Agent XPs', 1; RECONFIGURE;"

# Keep container running
wait
