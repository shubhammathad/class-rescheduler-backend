import pymysql

# This line specifically fixes the "mysqlclient 2.2.1 or newer is required" error
pymysql.version_info = (2, 2, 1, "final", 0)
pymysql.install_as_MySQLdb()