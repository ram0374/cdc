from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, expr
from pyspark.sql.types import StructType, StringType, IntegerType, MapType
from schema import cdc_schema
from pyspark.sql.functions import col, from_json, when
# Create Spark Session with Hadoop S3 configs for MinIO
spark = SparkSession.builder \
    .appName("Kafka-CDC-to-MinIO") \
    .config("spark.hadoop.fs.s3a.endpoint", "http://127.0.0.1:9000/") \
    .config("spark.hadoop.fs.s3a.access.key", "p4hJIYQqmbYcVqeF203K") \
    .config("spark.hadoop.fs.s3a.secret.key", "5d4oej9Me9w7TpUvDS83UmatFUnng2xuBI6uQQLK") \
    .config("spark.hadoop.fs.s3a.path.style.access", "true") \
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
    .config(
        "spark.jars.packages",
        "org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1,"
        "org.apache.hadoop:hadoop-aws:3.3.4,"
        "com.amazonaws:aws-java-sdk-bundle:1.12.375"
    ) \
    .getOrCreate()

spark.sparkContext.setLogLevel("INFO")

# Kafka topic and MinIO output path
kafka_topic = "sqlserver.cdc.dbo.changes"
minio_path = "s3a://cdc-chnages/raw/"

# Define schema for CDC JSON payload
# df = spark.createDataFrame([(1, "test")], ["id", "value"])
# df.repartition(1).write.mode("overwrite").parquet(f"{minio_path}/test-data/")
# Read stream from Kafka
df_raw = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:29092") \
    .option("subscribe", kafka_topic) \
    .option("startingOffsets", "latest") \
    .load()
    
print("Reading from Kafka topic:", kafka_topic)
print("Writing to MinIO path:", minio_path)
# print("CDC schema:", cdc_schema)
# print("Kafka topic schema:", df_raw.schema)

df = df_raw.select(
    col("key").cast("string").alias("key"),
    col("value").cast("string").alias("value"),
    col("topic"),
    col("partition"),
    col("offset"),
    col("timestamp")
)

df.printSchema()
# df.writeStream \
#     .format("console") \
#     .outputMode("append") \
#     .start() \
#     .awaitTermination()



df_parsed = df.selectExpr("CAST(value AS STRING) as json_string") \
    .select(from_json(col("json_string"), cdc_schema).alias("data")) \
    .select("data.payload.*") \
    .select(
        col("op"),
        col("before"),
        col("after"),
        when(col("op") == "c", "insert")
         .when(col("op") == "u", "update")
         .when(col("op") == "d", "delete")
         .when(col("op") == "r", "snapshot")
         .alias("operation")         
    )

# df_parsed.writeStream \
#     .format("console") \
#     .outputMode("append") \
#     .option("truncate", False) \
#     .start() \
#     .awaitTermination()


# inserts_updates = df_parsed.filter(col("operation").isin("insert", "update")) \
#     .selectExpr("after.*")

# deletes = df_parsed.filter(col("operation") == "delete").select("after.id")

# # Use in-memory Delta table approach to simulate upserts (use real Delta for production)
from pyspark.sql.streaming import DataStreamWriter

def upsert_microbatch(batch_df, batch_id):
    from pyspark.sql.functions import col
    print(f"Batch ID: {batch_id}")
    # batch_df.printSchema()
    # batch_df.show(10)
    from pyspark.sql.functions import get_json_object

    #df_debug = batch_df.selectExpr("CAST(after AS STRING) as json_str")
    # batch_df.select("after.*").show(truncate=False)
    #df_debug.show()

    if batch_df is not None and not batch_df.isEmpty():
        print(f"\n=== Processing microbatch {batch_id} ===")

        # Try reading existing data
        try:
            existing_df = spark.read.parquet(minio_path)
            print("Read existing data.")
        except:
            existing_df = spark.createDataFrame([], batch_df.schema)
            print("No existing data found. Initialized empty DataFrame.")

        # Step 1: Separate DELETE and UPSERT
        deletes_df = batch_df.filter(col("operation") == "delete").selectExpr("before.id as id")
        upserts_df = batch_df.filter(col("operation").isin("insert", "update")).selectExpr("after.*")

        # Step 2: Read existing data
        if existing_df is not None and not existing_df.isEmpty():
            # Remove rows to be deleted (and not reinserted)
            upsert_ids_df = upserts_df.select("id").distinct()
            filtered_deletes_df = deletes_df.join(upsert_ids_df, on="id", how="left_anti")

            # Remove deleted rows from existing data
            updated_df = existing_df.join(filtered_deletes_df, on="id", how="left_anti")

            # Step 3: Remove overlapping records from updated_df that also exist in upserts_df
            updated_df = updated_df.join(upsert_ids_df, on="id", how="left_anti")

            print("Applied deletes and removed overlapping IDs.")
        else:
            updated_df = spark.createDataFrame([], upserts_df.schema)

        # Step 4: Union updated_df + upserts_df
        if updated_df is not None and not updated_df.isEmpty():
            upserts_df = updated_df.unionByName(upserts_df, allowMissingColumns=True)

        # Step 5: Write to MinIO
        
        print("Writing final data to MinIO with partition overwrite...")
        upserts_df.show(10, truncate=False)
        # Partition by 'id' (or any other suitable partition column)
        spark.conf.set("spark.sql.sources.partitionOverwriteMode", "dynamic")
        upserts_df.write \
            .option("mergeSchema", "true") \
            .mode("overwrite") \
            .partitionBy("id")  \
            .parquet(minio_path)    
            #.option("replaceWhere", "id IN ({})".format(",".join(map(str, final_df.select("id").rdd.flatMap(lambda x: x).collect())))) \
            

        print(f"Finished writing batch {batch_id}.")
    else:
        print(f"Batch {batch_id} is empty. Skipping.")

# Write the stream using foreachBatch
 # .outputMode("update") 

query = df_parsed.writeStream \
    .foreachBatch(upsert_microbatch) \
    .outputMode("append") \
    .option("checkpointLocation", "/tmp/checkpoints/cdc-to-minio") \
    .start()

query.awaitTermination()
