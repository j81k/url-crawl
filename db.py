import mysql.connector
from mysql.connector import errorcode
from config import *

class DB():
	cnx = None
	cursor = None

	def insert(self, data, table_name = 'pages'):
		sql = ''
		values_str = ''
		values = []
		for column, value in data.items():
			sql += column + ','
			values_str += '%s,' # '%('+ column +')s,'
			values.append(value)

		sql = (
			"INSERT INTO " + table_name +
			"("+ sql[:-1] +")"
			"VALUES("+ values_str[:-1] +")"
		)

		self.cursor.execute(sql, tuple(values)) #, self.cnx)
		self.cnx.commit()
	
	def query(self, sql):
		try:
			self.cursor.execute(sql)
		except mysql.connector.Error as e:
			print "Query Error: %s" % str(e)
			exit(1)

	def create_tables(self):
		tables = {}
		tables['pages']	= (
			"CREATE TABLE IF NOT EXISTS `pages` ("
			"	`id` INT(11) NOT NULL AUTO_INCREMENT,"
			"	`name` MEDIUMTEXT NULL,"
			"	`slug` TEXT NULL,"
			"	`url` VARCHAR(255) NULL,"
			"	`header` LONGTEXT NULL,"
			"	`content` LONGTEXT NULL,"
			"	`updated_on` TIMESTAMP NOT NULL,"
			"	PRIMARY KEY(`id`)"
			") ENGINE=InnoDB"
		)

		for name, sql in tables.iteritems():
			self.query(sql)

	def check_db_exists(self):
		try: 
			self.cnx.database = DB_NAME
		except mysql.connector.Error as e:
			if e.errno == errorcode.ER_BAD_DB_ERROR:
				self.query("CREATE DATABASE {} DEFAULT CHARACTER SET \"utf8\" " . format(DB_NAME))
				self.cnx.database = DB_NAME
				self.create_tables()
			else:
				print "Error: %s" % str(e)
				exit(1)	

	def close(self):
		self.cursor.close()
		self.cnx.close()

	def connect(self):
		config = {
			'user' : DB_USER,
			'password': DB_PASS,
			'host': DB_HOST,
			#'database': DB_NAME,
			'raise_on_warnings': True,
			#'use_pure': False
		}

		try:
			self.cnx = mysql.connector.connect(**config)
			self.cursor = self.cnx.cursor()
			self.check_db_exists()
			
		except mysql.connector.Error as e:
			if e.errno == errorcode.ER_ACCESS_DENIED_ERROR:
				print "Error: Invalid database username or password!"
			elif e.errno == errorcode.ER_BAD_DB_ERROR:
				print "Error: Database (%s) is not exists!" % DB_NAME
			else:
				print "Error: %s" % str(e)	
					