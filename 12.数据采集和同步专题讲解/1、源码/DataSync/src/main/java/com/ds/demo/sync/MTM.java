package com.ds.demo.sync;

import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;
import org.apache.flink.table.api.bridge.java.StreamTableEnvironment;

public class MTM {
    public static void main(String[] args) {
        StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
        env.setParallelism(1);
        env.enableCheckpointing(3000);

        StreamTableEnvironment table = StreamTableEnvironment.create(env);

        // source 源mysql,监控binlog的mysql映射关系
        table.executeSql("CREATE TABLE test_cdc1 (" +
                " id int primary key," +
                " name STRING," +
                " age int" +
                ") WITH (" +
                " 'connector' = 'mysql-cdc'," +
                " 'scan.startup.mode' = 'latest-offset'," +
                " 'hostname' = 'ds-bigdata-005'," +
                " 'port' = '3306'," +
                " 'username' = 'root'," +
                " 'password' = 'Admin_Root123'," +
                " 'database-name' = 'lili'," +
                " 'table-name' = 'test_cdc1'" +
                ")");

        // sink 目的mysql，要写入的mysql
        table.executeSql("CREATE TABLE my_sink2 (\n" +
                "        id INT primary key,\n" +
                "        name STRING,\n" +
                "        age INT\n" +
                ") WITH (\n" +
                "        'connector' = 'jdbc',\n" +
                "        'url' = 'jdbc:mysql://ds-bigdata-005:3306/lili?serverTimezone=UTC&useUnicode=true&characterEncoding=utf-8&useSSL=false',\n" +
                "        'username' = 'root',\n" +
                "        'password' = 'Admin_Root123',\n" +
                "        'driver' = 'com.mysql.cj.jdbc.Driver',\n" +
                "        'table-name' = 'test_cdc3'\n" +
                "        )");

        // 串通
        table.executeSql("insert into my_sink2 select * from test_cdc1");

    }
}
