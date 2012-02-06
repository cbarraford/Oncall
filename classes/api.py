#!/usr/bin/env python

import os,sys
import simplejson as json

# add this file location to sys.path
cmd_folder = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if cmd_folder not in sys.path:
     sys.path.insert(0, cmd_folder)

import mysql_layer as mysql
import user as User
import alert as Alert
# load configuration settings (dict conf)
from config import *

class Api():
	'''
	This API class is designed to return json via http request
	Not even close to being done (obviously)
	'''
	def __init__(self, type="user", count=20):
		self.db = mysql.Database()
		if type == "alert" or type == "alerts":
			obj_alerts = Alert.all_alerts()
			dict_alerts = []
			for a in obj_alerts:
				dict_alert = a.convert_to_dict()
				dict_alerts.append(dict_alert)
			j = json.dumps(dict_alerts[:count])
			print j
		elif type == "user" or type == "users":
			obj_users = User.all_users()
			dict_users = []
			for u in obj_users:
				dict_user = u.convert_to_dict()
				dict_users.append(dict_user)
			j = json.dumps(dict_users[:count])
			print j
		else:
			return {}