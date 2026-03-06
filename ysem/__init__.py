from .settings import USE_SQLITE3
import pymysql


if not USE_SQLITE3:
    pymysql.install_as_MySQLdb()
