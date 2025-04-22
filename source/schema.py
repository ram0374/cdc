from pyspark.sql.types import *

payload_schema = StructType([
    StructField("before", StructType([
        StructField("id", IntegerType(), nullable=False),
        StructField("value", StringType(), nullable=True),
        StructField("Email", StringType(), True)  # 
    ]), nullable=True),

    StructField("after", StructType([
        StructField("id", IntegerType(), nullable=False),
        StructField("value", StringType(), nullable=True),
        StructField("Email", StringType(), True)  # 
    ]), nullable=True),

    StructField("source", StructType([
        StructField("version", StringType(), nullable=False),
        StructField("connector", StringType(), nullable=False),
        StructField("name", StringType(), nullable=False),
        StructField("ts_ms", LongType(), nullable=False),
        StructField("snapshot", StringType(), nullable=True),
        StructField("db", StringType(), nullable=False),
        StructField("sequence", StringType(), nullable=True),
        StructField("ts_us", LongType(), nullable=True),
        StructField("ts_ns", LongType(), nullable=True),
        StructField("schema", StringType(), nullable=False),
        StructField("table", StringType(), nullable=False),
        StructField("change_lsn", StringType(), nullable=True),
        StructField("commit_lsn", StringType(), nullable=True),
        StructField("event_serial_no", LongType(), nullable=True),
    ]), nullable=False),

    StructField("transaction", StructType([
        StructField("id", StringType(), nullable=False),
        StructField("total_order", LongType(), nullable=False),
        StructField("data_collection_order", LongType(), nullable=False),
    ]), nullable=True),

    StructField("op", StringType(), nullable=False),
    StructField("ts_ms", LongType(), nullable=True),
    StructField("ts_us", LongType(), nullable=True),
    StructField("ts_ns", LongType(), nullable=True)
])

cdc_schema = StructType([
    StructField("payload", payload_schema, nullable=True)
])
