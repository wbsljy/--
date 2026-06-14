//package com.ds.demo
//
//import org.apache.spark.sql.SparkSession
//
//object CsvSource {
//  def main(args: Array[String]): Unit = {
//    val spark = SparkSession.builder()
//      .master("local")
//      .appName("csv")
//      .getOrCreate()
//
//    // 隐式转换
//
//    // 使用header选项
//    // 使用schema参数
//    val schema =
//    """
//      |name string,
//      |age int,
//      |height int
//      |""".stripMargin
//
//    val df = spark.read
////      .option("header",true)
//        .schema(schema)
//      .csv("src/main/resources/data/people.csv")
//
//    df.write.csv("src/main/resources/data/people1.csv")
//  }
//}
