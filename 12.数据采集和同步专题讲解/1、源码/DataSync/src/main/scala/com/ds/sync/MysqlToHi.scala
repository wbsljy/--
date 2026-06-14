//package com.ds.sync
//
//import org.apache.spark.sql.SparkSession
//
//
//object MysqlToHi {
//  def main(args: Array[String]): Unit = {
//    val spark = SparkSession.builder()
//      .master("local")
//      .appName("mysql to hive")
//      .enableHiveSupport()
//      .getOrCreate()
//
//    // 隐式转换
//    import spark.implicits._
//
//    // 配置mysql数据源
//    val df = spark.read
//      .format("jdbc")
//      .option("url", "jdbc:mysql://ds-bigdata-001:3306/ds_test?useSSl=false")
//      .option("driver", "com.mysql.jdbc.Driver")
//      .option("user", "ds_read")
//      .option("password", "ds#readA0906")
//      .option("dbtable", "stud")
//      .load()
//
//    // 创建一个临时试图
//    df.createTempView("stud")
//
//    //在hive中先要创建一张表
//    spark.sql("create table ds_spark.stud1(name string,age int)")
//
//    // 同步数据
//    spark.sql("insert overwrite table ds_spark.stud1 select name,age from stud ")
//  }
//}
