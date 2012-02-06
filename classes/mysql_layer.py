#!/usr/bin/env python

import os, sys, logging
import MySQLdb
import datetime

# add this file location to sys.path
cmd_folder = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if cmd_folder not in sys.path:
     sys.path.insert(0, cmd_folder)
     sys.path.insert(0, cmd_folder + "/classes")

# load configuration settings (dict conf)
from config import *

logging.basicConfig(format='%(asctime)s - %(levelname)s: %(message)s', filename=conf['logdir'] + '/server.log',level=logging.DEBUG, datefmt='%m/%d/%Y %I:%M:%S %p')

def alerts_convert_to_dict(v):
	'''
	convert results to dict for easy reading
	'''
	logging.debug(v)
	return { 'id':v[0], 'createDate':v[1], 'subject':v[2], 'message':v[3], 'team':v[4], 'ack':v[5], 'ackby':v[6], 'acktime':v[7], 'lastAlertSent':v[8], 'tries':v[9] }
	
	
def users_convert_to_dict(v):
	'''
	convert results to dict for easy reading
	'''
	logging.debug(v)
	return { 'id':v[0], 'createDate':v[1], 'name':v[2], 'email':v[3], 'phone':v[4], 'team':v[5], 'state':v[6], 'lastAlert':v[7] }

class Database:
	def __init__(self):
		logging.debug("Initializing db")
		self.connectDB()

	def connectDB(self):
		'''
		Connect to the db
		'''
		logging.debug("Connecting to db at %s on port %s, as %s" % (conf['mysql_host'], conf['mysql_port'], conf['mysql_username']))
		try:
			self._connection = MySQLdb.connect(host=conf['mysql_host'], port=conf['mysql_port'], user=conf['mysql_username'], passwd=conf['mysql_passwd'], db=conf['mysql_db'])
			self._cursor = self._connection.cursor()
		except Exception, e:
			logging.error("Cannot connect to db, creating new one....")
			db = MySQLdb.connect(host=conf['mysql_host'], port=conf['mysql_port'], user=conf['mysql_username'], passwd=conf['mysql_passwd'])
			c = db.cursor()
			cmd = "CREATE DATABASE %s;" % (conf['mysql_db'])
			c.execute(cmd)
			cmd = "use %s;" % (conf['mysql_db'])
			c.execute(cmd)
			cmd = '''CREATE TABLE IF NOT EXISTS alerts (id INT PRIMARY KEY AUTO_INCREMENT, createDate TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, subject TEXT, message TEXT, team CHAR(50), ack INT NOT NULL DEFAULT 0, ackby INT NOT NULL DEFAULT 0, acktime TIMESTAMP, lastAlertSent TIMESTAMP, tries INT NOT NULL DEFAULT 0);'''
			c.execute(cmd)
			cmd = '''CREATE TABLE IF NOT EXISTS users (id INT PRIMARY KEY AUTO_INCREMENT, createDate TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, name CHAR(50), email CHAR(50), phone varchar(50), team CHAR(50), state INT NOT NULL DEFAULT 0, lastAlert INT NOT NULL DEFAULT 0);'''
			c.execute(cmd)
			self.connectDB()
	
	def save(self):
		'''
		save the changes to the db
		'''
		logging.debug("saving changing to the db")
		self._connection.commit()
	
	def close(self):
		'''
		close the connection to the database
		'''
		logging.debug("closing connection to the db")
		self._connection.close ()
		self._cursor.close()