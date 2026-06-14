package com.ds.demo.sync;

import com.ds.demo.MyDbz;
import com.ververica.cdc.connectors.mysql.MySqlSource;
import com.ververica.cdc.connectors.mysql.table.StartupOptions;
import com.ververica.cdc.debezium.DebeziumSourceFunction;
import com.ververica.cdc.debezium.StringDebeziumDeserializationSchema;
import org.apache.flink.streaming.api.datastream.DataStreamSource;
import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;

public class DSCDC {
    public static void main(String[] args) throws Exception {
        StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
        env.setParallelism(1);
        env.enableCheckpointing(3000);

        // flink的编程模式非常的简单：source  transform  sink
        // 从这里开始就是MySQL CDC
        // 先定义source
        DebeziumSourceFunction<String> mysqlSource = MySqlSource.<String>builder()
                .hostname("ds-bigdata-005")
                .port(3306)
                .username("root")
                .password("Admin_Root123")
                .databaseList("lili")
                .tableList("lili.test_cdc1")
                .deserializer(new MyDbz())
                .startupOptions(StartupOptions.initial())
                .build();
        // 把source添加到flink 的运行环境之中
        DataStreamSource<String> source = env.addSource(mysqlSource);

        // transform
        source.print();


        // sink
        // source.addSink()

        // 驱动程序
        env.execute("mysql cdc");


    }
}
