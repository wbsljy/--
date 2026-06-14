package com.ds.demo;

import java.sql.*;
import java.util.Properties;

public class JDBCDemo {
    private static String HIVE_JDBC_URL = "jdbc:hive2://ds-bigdata-001:10000/default";
    public static void main(String[] args) throws Exception{
        Class.forName("org.apache.hive.jdbc.HiveDriver");
        Connection con = DriverManager.getConnection(HIVE_JDBC_URL);
        Statement stmt = con.createStatement();
        showDatabases(stmt);
    }
    public static void showDatabases(Statement stmt) throws Exception {
        String sql = "show databases";
        ResultSet resultSet = stmt.executeQuery(sql);
        while (resultSet.next()) {
            System.out.println(resultSet.getString(1));
        }
    }
}
