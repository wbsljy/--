//package com.ds.demo;
//
//import com.ververica.cdc.connectors.mysql.MySqlSource;
//import com.ververica.cdc.connectors.mysql.table.StartupOptions;
//import com.ververica.cdc.debezium.DebeziumSourceFunction;
//import com.ververica.cdc.debezium.StringDebeziumDeserializationSchema;
//import org.apache.flink.streaming.api.datastream.DataStreamSource;
//import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;
//
//public class CDCDemo {
//    public static void main(String[] args) throws Exception {
//
//        StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
//        env.setParallelism(1);
//        env.enableCheckpointing(3000);
//
//        DebeziumSourceFunction<String> sourceFunction = MySqlSource.<String>builder()
//                .hostname("ds-bigdata-005")
//                .port(3306)
//                .username("root")
//                .password("Admin_Root123")
//                .databaseList("lili")
//                // 这里一定要是db.table的形式
//                .tableList("lili.test_cdc")
//                .deserializer(new StringDebeziumDeserializationSchema())
//                .startupOptions(StartupOptions.initial())
//                .build();
//
//        DataStreamSource<String> dataStreamSource = env.addSource(sourceFunction);
//        dataStreamSource.print();
//        env.execute("CDCDemo");
//    }
//}
