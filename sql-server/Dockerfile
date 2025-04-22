FROM mcr.microsoft.com/mssql/server:2022-latest

ENV MSSQL_AGENT_ENABLED=true
ENV ACCEPT_EULA=Y
ENV MSSQL_PID=Developer

USER root

# Copy start script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]

EXPOSE 1433