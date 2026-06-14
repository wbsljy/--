//package com.ds.demo;
//
//import org.apache.flink.api.java.tuple.Tuple2;
//import org.apache.flink.streaming.api.datastream.DataStream;
//import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;
//import org.apache.flink.table.api.Table;
//import org.apache.flink.table.api.bridge.java.StreamTableEnvironment;
//import org.apache.flink.types.Row;
//
//public class FlinkSQLCDC {
//    public static void main(String[] args) throws Exception {
//
//        StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
//        env.setParallelism(1);
//        env.enableCheckpointing(3000);
//
//        StreamTableEnvironment tableEnv = StreamTableEnvironment.create(env);
//        tableEnv.executeSql("CREATE TABLE test_cdc (" +
//                " id int primary key," +
//                " name STRING," +
//                " age int" +
//                ") WITH (" +
//                " 'connector' = 'mysql-cdc'," +
//                " 'scan.startup.mode' = 'latest-offset'," +
//                " 'hostname' = 'ds-bigdata-005'," +
//                " 'port' = '3306'," +
//                " 'username' = 'root'," +
//                " 'password' = 'Admin_Root123'," +
//                " 'database-name' = 'lili'," +
//                " 'table-name' = 'test_cdc'" +
//                ")");
//        Table table = tableEnv.sqlQuery("select * from test_cdc");
//        DataStream<Tuple2<Boolean, Row>> dataStreamSource = tableEnv.toRetractStream(table, Row.class);
//        dataStreamSource.print();
//        env.execute("FlinkSQLCDC");
//    }
//}
