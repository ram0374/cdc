CDC Pipeline: SQL Server → Debezium → Kafka → PySpark → MinIO
This project demonstrates a Change Data Capture (CDC) pipeline where changes (INSERT, UPDATE, DELETE) from a SQL Server database are captured using Debezium, streamed through Kafka, processed in PySpark, and written to MinIO in Parquet format.

Architecture:

+----------------+      +-----------+      +--------+      +------------+      +--------+
| SQL Server DB  | ---> | Debezium  | ---> | Kafka  | ---> | PySpark    | ---> | MinIO  |
+----------------+      +-----------+      +--------+      +------------+      +--------+
     (CDC Source)        (Change Logs)     (CDC Topic)     (CDC Handling)     (Parquet Storage)

Components Used:
SQL Server: Source database with CDC enabled.

Debezium: Monitors SQL Server for CDC events and publishes to Kafka.

Kafka: Message broker used for streaming CDC events.

PySpark: Processes Kafka CDC events and applies insert/update/delete logic.

MinIO: S3-compatible object storage to hold final Parquet data.

Prerequisites
Docker Desktop (for local Kafka, Debezium, SQL Server, MinIO)
Python 3.8+
Java 8 or later
Apache Spark (3.3 or later)
Hadoop AWS packages for S3A support
Kafka Python client (optional, for testing)

Setup Instructions
1. Start Required Services (SQL Server, Kafka, Debezium, MinIO)
You can use Docker Compose or start each service individually.

Start MinIO:
mkdir -p ~/minio/data
docker run \
   -p 9000:9000 \
   -p 9001:9001 \
   --name minio \
   -v ~/minio/data:/data \
   -e "MINIO_ROOT_USER=root" \
   -e "MINIO_ROOT_PASSWORD=root" \
   quay.io/minio/minio server /data --console-address ":9001"
Access MinIO Console: http://localhost:9001
Credentials: root / Test@2222

Create a bucket (e.g., cdc-chnages).

2. Enable CDC in SQL Server
Ensure CDC is enabled on the database and target tables:

sql
EXEC sys.sp_cdc_enable_db;
EXEC sys.sp_cdc_enable_table  
@source_schema = 'dbo',  
@source_name   = 'chnages',  
@role_name     = NULL;

3. Configure Debezium
Start Debezium with Kafka and configure a connector for SQL Server. Sample connector config:
{
  "name": "sqlserver-connector",
  "config": {
    "connector.class": "io.debezium.connector.sqlserver.SqlServerConnector",
    "database.hostname": "sqlserver",
    "database.port": "1433",
    "database.user": "sa",
    "database.password": "Passw0rd",
    "database.dbname": "cdc",
    "database.server.name": "sqlserver",
    "table.include.list": "dbo.cdc-chnages",
    "database.history.kafka.bootstrap.servers": "kafka:9092",
    "database.history.kafka.topic": "schema-changes.sqlserver"
  }
}

4. PySpark Streaming CDC App
Update and run the provided PySpark script:

Kafka Config:
.option("kafka.bootstrap.servers", "localhost:9092") \
.option("subscribe", "cdc-topic")

MinIO Config in Spark:
.config("spark.hadoop.fs.s3a.endpoint", "http://localhost:9000") \
.config("spark.hadoop.fs.s3a.access.key", "root") \
.config("spark.hadoop.fs.s3a.secret.key", "root") \
.config("spark.hadoop.fs.s3a.path.style.access", "true")

Run the app:
spark-submit --packages org.apache.hadoop:hadoop-aws:3.3.4 cdc_spark_app.py

Output
CDC events are processed and written to MinIO as Parquet files with UPSERT/DELETE logic applied.
Navigate to your MinIO bucket to see the output under a folder raw.

Data Handling Logic
INSERT/UPDATE: Upsert into final state based on id (primary key).

DELETE: Remove row with matching id from target data in MinIO.



Resources
Debezium SQL Server Connector

Kafka + Spark Streaming Integration

MinIO + Spark (S3A)


Helpfull commands
curl -X PUT -H "Content-Type: application/json" \                                                                                                 
--data @debezium-sqlserver-connector-config.json \
http://localhost:8083/connectors/sqlserver-connector/config



curl -X DELETE http://localhost:8083/connectors/sqlserver-connector  

curl -X PUT -H "Content-Type: application/json" \                                                                                                 
--data @debezium-sqlserver-connector-config.json \
http://localhost:8083/connectors/sqlserver-connector/config


docker-compose -f sql-server/sql-server.yml up -d


python source/kafka_process.py 



Minio
----


mkdir -p ~/minio/data

docker run \
   -p 9000:9000 \
   -p 9001:9001 \
   --name minio \
   -v ./data:/data \
   -e "MINIO_ROOT_USER=root" \
   -e "MINIO_ROOT_PASSWORD=root" \
   quay.io/minio/minio server /data --console-address ":9001"

