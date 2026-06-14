//package com.ds.demo
//
//import org.apache.spark.sql.SparkSession
//
//object MysqlToHive {
//  def main(args: Array[String]): Unit = {
//    val spark = SparkSession.builder()
//      .master("local")
//      .appName("mysql to hive")
//      // 开启动态分区
//      .config("hive.exec.dynamic.partition", "true")
//      // 如果是strict模式，那么必须带有静态分区字段
//      .config("hive.exec.dynamic.partition.mode", "nonstrict")
//      .enableHiveSupport()
//      .getOrCreate()
//
//    // 隐式转换
//
//    // 配置mysql数据源
//        val df = spark.read
//          .format("jdbc")
//          .option("url", "jdbc:mysql://ds-bigdata-001:3306/ds_test?useSSl=false")
//          .option("driver", "com.mysql.jdbc.Driver")
//          .option("user", "ds_read")
//          .option("password", "ds#readA0906")
//           .option("dbtable", "stud")
//          .load()
//
//    // 创建一个临时视图
//    df.createTempView("stud")
//
//    // hive先创建动态分区表
//    spark.sql("create table ds_spark.stud2(name string) partitioned by(age int)")
//
//    // 动态分区表建好之后就要往里面导入数据
//    spark.sql("insert overwrite table ds_spark.stud2 partition(age) select name,age from stud")
//
//  }
//}
