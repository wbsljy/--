package com.ds.demo;

import org.apache.flink.api.java.tuple.Tuple2;
import org.apache.flink.streaming.api.datastream.DataStream;
import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;
import org.apache.flink.table.api.Table;
import org.apache.flink.table.api.bridge.java.StreamTableEnvironment;
import org.apache.flink.types.Row;

public class MySQLToHDFS {
    public static void main(String[] args) throws Exception {

        StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
        env.setParallelism(1);
        env.enableCheckpointing(3000);

        StreamTableEnvironment tableEnv = StreamTableEnvironment.create(env);
        // 如果原表有主键，则需要声明主键
        tableEnv.executeSql("CREATE TABLE my_source (\n" +
                "        id INT primary key,\n" +
                "        name STRING,\n" +
                "        age INT\n" +
                ") WITH (\n" +
                "        'connector' = 'mysql-cdc',\n" +
                "        'hostname' = 'ds-bigdata-005',\n" +
                "        'port' = '3306',\n" +
                "        'username' = 'root',\n" +
                "        'password' = 'Admin_Root123',\n" +
                "        'scan.startup.mode' = 'initial'," +
                "        'database-name' = 'lili',\n" +
                "        'table-name' = 'test_cdc',\n" +
                "        'scan.incremental.snapshot.enabled' = 'false'\n" +
                "        )");

        // 表必须要提前创建号
        tableEnv.executeSql("CREATE TABLE my_sink (\n" +
                "        id INT primary key,\n" +
                "        name STRING,\n" +
                "        age INT\n" +
                ") WITH (\n" +
                "        'connector' = 'jdbc',\n" +
                "        'url' = 'jdbc:mysql://ds-bigdata-005:3306/lili?serverTimezone=UTC&useUnicode=true&characterEncoding=utf-8&useSSL=false',\n" +
                "        'username' = 'root',\n" +
                "        'password' = 'Admin_Root123',\n" +
                "        'driver' = 'com.mysql.cj.jdbc.Driver',\n" +
                "        'table-name' = 'test_cdc1'\n" +
                "        )");

        tableEnv.executeSql("INSERT INTO my_sink\n" +
                "        SELECT id, name, age\n" +
                "        FROM my_source");
    }
}