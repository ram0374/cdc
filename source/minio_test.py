from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, expr
from pyspark.sql.types import StructType, StringType, IntegerType, MapType
from schema import cdc_schema
from pyspark.sql.functions import col, from_json, when
# Create Spark Session with Hadoop S3 configs for MinIO
spark = SparkSession.builder \
    .appName("Kafka-CDC-to-MinIO- Test") \
    .config("spark.hadoop.fs.s3a.endpoint", "http://127.0.0.1:9000/") \
    .config("spark.hadoop.fs.s3a.access.key", "p4hJIYQqmbYcVqeF203K") \
    .config("spark.hadoop.fs.s3a.secret.key", "5d4oej9Me9w7TpUvDS83UmatFUnng2xuBI6uQQLK") \
    .config("spark.hadoop.fs.s3a.path.style.access", "true") \
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
    .config(
        "spark.jars.packages",
        "org.apache.hadoop:hadoop-aws:3.3.4,"
        "com.amazonaws:aws-java-sdk-bundle:1.12.375"
    ) \
    .getOrCreate()

spark.sparkContext.setLogLevel("INFO")

# Kafka topic and MinIO output path
kafka_topic = "sqlserver.cdc.dbo.changes"

minio_path = "s3a://cdc-chnages/raw/"

# Define schema for CDC JSON payload
df = spark.read.option("mergeSchema", "true").parquet(minio_path)

print("Reading from MinIO path:", minio_path)
print("Kafka topic schema:", df.schema)
df.printSchema()
print(df.show(10))
spark.stop()