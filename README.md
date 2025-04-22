# CDC Pipeline: SQL Server → Debezium → Kafka → PySpark → MinIO

This project demonstrates a Change Data Capture (CDC) pipeline where changes (INSERT, UPDATE, DELETE) from a SQL Server database are captured using Debezium, streamed through Kafka, processed with PySpark, and written to MinIO in Parquet format.

## Architecture

SQL Server → Debezium → Kafka → PySpark → MinIO

- SQL Server: Source database with CDC enabled
- Debezium: Monitors SQL Server and emits changes as Kafka events
- Kafka: Message broker to transport CDC events
- PySpark: Processes CDC events and applies insert, update, and delete logic
- MinIO: S3-compatible object storage for Parquet output

## Components

- SQL Server 2022 (Developer Edition)
- Kafka (Apache or Confluent)
- Debezium SQL Server Connector
- Apache Spark 3.3+
- MinIO (S3-compatible storage)
- Python 3.8+ with PySpark

## Setup Instructions

### 1. Start MinIO

Create a local directory and run MinIO using Docker:

```bash
mkdir -p ~/minio/data

docker run \
  -p 9000:9000 \
  -p 9001:9001 \
  --name minio \
  -v ~/minio/data:/data \
  -e "MINIO_ROOT_USER=root" \
  -e "MINIO_ROOT_PASSWORD=root" \
  quay.io/minio/minio server /data --console-address ":9001"


Access the MinIO console at: http://localhost:9001
-------


##2. Create a bucket named cdc-data.

## 2. Enable CDC in SQL Server
Enable CDC on your database and tables using the following SQL commands:
EXEC sys.sp_cdc_enable_db;

EXEC sys.sp_cdc_enable_table  
@source_schema = 'dbo',  
@source_name   = 'cdc_changes',  
@role_name     = NULL;

##3. Configure Debezium Connector
Create a Debezium connector for SQL Server with the following configuration:
{
  "name": "sqlserver-connector",
  "config": {
    "connector.class": "io.debezium.connector.sqlserver.SqlServerConnector",
    "database.hostname": "sqlserver",
    "database.port": "1433",
    "database.user": "sa",
    "database.password": "YourStrong!Passw0rd",
    "database.dbname": "cdc",
    "database.server.name": "sqlserver",
    "table.include.list": "dbo.cdc_changes",
    "database.history.kafka.bootstrap.servers": "kafka:9092",
    "database.history.kafka.topic": "schema-changes.sqlserver"
  }
}
Post this configuration to the Debezium REST API (typically available at http://localhost:8083).

##4. Run PySpark CDC App
Make sure you have Hadoop AWS and necessary Spark configurations for S3A/MinIO.

Example Spark job snippet:
spark = SparkSession.builder \
    .appName("CDC Processor") \
    .config("spark.hadoop.fs.s3a.endpoint", "http://localhost:9000") \
    .config("spark.hadoop.fs.s3a.access.key", "root") \
    .config("spark.hadoop.fs.s3a.secret.key", "root") \
    .config("spark.hadoop.fs.s3a.path.style.access", "true") \
    .getOrCreate()

df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("subscribe", "cdc-topic") \
    .load()

# Your transformation logic for inserts/updates/deletes here

df.writeStream \
    .format("parquet") \
    .option("checkpointLocation", "/tmp/checkpoint") \
    .option("path", "s3a://cdc-data/final-output/") \
    .outputMode("append") \
    .start() \
    .awaitTermination()

##5. Handle Inserts, Updates, and Deletes
Debezium CDC messages include an op field:

c for create (insert)

u for update

d for delete

Use this to route your logic in PySpark and apply:

Upserts for c and u

Deletes using a join/merge logic with existing data


Output
Final records are written to the configured MinIO bucket (cdc-data/final-output/) in Parquet format.

Notes
Use spark-submit with appropriate JAR packages (hadoop-aws, aws-java-sdk) when running the Spark job.

Make sure the MinIO endpoint and credentials are configured in Spark correctly.

Use schema evolution-compatible storage (like Hudi or Delta) if dealing with frequent schema changes.

Resources
Debezium SQL Server Connector: https://debezium.io/documentation/reference/connectors/sqlserver.html

Spark Structured Streaming with Kafka: https://spark.apache.org/docs/latest/structured-streaming-kafka-integration.html

MinIO with Spark: https://min.io/docs/minio/linux/integrations/apache-spark.html


###Helpfull-commands

curl -X PUT -H "Content-Type: application/json" \
--data @debezium-sqlserver-connector-config.json
http://localhost:8083/connectors/sqlserver-connector/config

curl -X DELETE http://localhost:8083/connectors/sqlserver-connector

curl -X PUT -H "Content-Type: application/json" \
--data @debezium-sqlserver-connector-config.json
http://localhost:8083/connectors/sqlserver-connector/config

docker-compose -f sql-server/sql-server.yml up -d

python source/kafka_process.py
