#!/usr/bin/env python

import logging, urllib
import simplejson as json
from pprint import pprint

import mysql_layer as mysql
import twilio_layer as twilio
import user_layer as User
import alert_layer as Alert
import util_layer as Util

conf = Util.load_conf()
Util.init_logging("api")

class Api():
	'''
	This API class is designed to return json via http request
	Not even close to being done (obviously)
	'''
	def __init__(self, **data):
		'''
		Initialize the api class
		'''
		# set some default attribute values
		self.count = 20
		self.status_message = None
		self.name = None
		self.state = None
		self.phone = None
		self.email = None
		self.team = None
		self.id = None
		self.ack = None
		self.user_id = 0
		
		# convert the dictionary array received into Api class attributes
		self.__dict__.update(data)
		# making sure values are correct var type
		try:
			self.count = int(self.count)
		except Exception, e:
			self.populate(1002, "Count is not a integer")
			return
		if self.id != None:
			try:
				self.id = int(self.id)
			except Exception, e:
				self.populate(1003, "ID is not a integer")
				return
		if self.state != None:
			try:
				self.state = int(self.state)
			except Exception, e:
				self.populate(1004, "State is not a integer")
				return
		if self.user_id != 0:
			try:
				self.user_id = int(self.user_id)
			except Exception, e:
				self.populate(1005, "User_id is not a integer")
				return
				
		#init database connection
		self.db = mysql.Database()

		if self.action.lower() == "query":
			self.query()
		elif self.action.lower() == "create":
			self.create()
		elif self.action.lower() == "edit":
			self.edit()
		elif self.action.lower() == "delete":
			self.delete()
		else:
			self.populate(1001,"Invalid action type")

	def query(self):
		if self.target == "alert" or self.target == "alerts":
			objects = Alert.all_alerts()
		elif self.target == "user" or self.target == "users":
			objects = User.all_users()
		else:
			self.populate(1101,"Invalid API query call: Missing valid target parameter")
			return
		dict_objs = []
		for x in objects:
			dict_objs.append(x.convert_to_dict())
			if len(dict_objs) >= self.count: break
		self.populate(200,"OK",json.dumps(dict_objs))
	
	def create(self):
		if self.target == "alert" or self.target == "alerts":
			if self.subject:
				self.subject = urllib.unquote_plus(self.subject)
			else:
				self.populate(1201,"No subject in alert creation")
				return
			if self.message:
				self.message = urllib.unquote_plus(self.message)
			else:
				self.populate(1202,"No message in alert creation")
				return
			if self.team:
				self.team= urllib.unquote_plus(self.team)
			else:
				self.team="default"
			# check to see if this alert is a new one
			isNewAlert = True
			for a in Alert.fresh_alerts():
				if a.subject == self.subject and a.message == self.message and a.team == self.team: isNewAlert = False
			if isNewAlert == True:
				# save new alert to the db
				newalert = Alert.Alert()
				newalert.subject = self.subject
				newalert.message = self.message
				newalert.team = self.team
				newalert.send_alert()
				self.populate(200,"OK")
			else:
				self.populate(200,"OK",json.dumps("Repeat alert"))
		elif self.target == "user" or self.target == "users":
			if self.name == None or len(self.name) <= 0:
				self.populate(1301,"No name parameter given in user creation")
				return
			if self.email == None or len(self.email) <= 0 or "@" not in self.email:
				self.populate(1302,"No or invalid email parameter given in user creation")
				return
			if self.phone == None or len(self.phone) != 12 or self.phone.startswith("+"):
				if self.state != 9:
					self.populate(1303,"No or invalid phone number parameter given in user creation")
					return
			if self.state == None or isinstance(self.state, int):
				self.state = 0
			if self.team == None: self.team = "default"
			newuser = User.User()
			newuser.name = self.name
			newuser.email = self.email
			newuser.phone = self.phone
			newuser.state = self.state
			newuser.team = self.team
			newuser.save_user()
			if newuser.state != 9:
				valid_code = twilio.validate_phone(newuser)
				if valid_code == False:
					self.populate(1401,"Unable to get a validation code for new phone number")
					return
				elif valid_code == True:
					self.populate(1402,"Phone has already been verified with Twilio")
					return
				else:
					self.populate(1400,"Validation Code: %s" % (valid_code))
			else:
				self.populate(200,"OK")
				return
		else:
			self.populate(1101,"Invalid API create call: Missing valid target parameter")
			return
	
	def edit(self):
		if self.id == None:
			self.populate(1699,"Invalid API edit call: Missing valid id parameter")
			return
		if self.target == "alert" or self.target == "alerts":
			try:
				obj = Alert.Alert(self.id)
				if self.ack == 1 or self.ack == True or self.ack.lower() == "true":
					obj.ack_alert(self.user_id)
				if self.ack == 0 or self.ack == False or self.ack.lower() == "false":
					obj.ack = 0
					obj.save_alert()
				self.populate(200,"OK")
			except Exception, e:
				self.populate(1602,e.__str__())
				return
		elif self.target == "user" or self.target == "users":
			try:
				obj = User.User(self.id)
				if self.name != None:
					if len(self.name) > 0: 
						obj.name = self.name
					else:
						self.populate(1603,"Bad name parameter")
						return
				if self.phone != None:
					if len(self.phone) == 12 and self.phone.startswith("+"): 
						obj.phone = self.phone
					else:
						self.populate(1604,"Bad phone parameter")
						return
				if self.email != None:
					if len(self.name) > 0 and "@" in self.phone:
						obj.email = self.email
					else:
						self.populate(1605,"Bad email parameter")
						return
				if self.state != None:
					if self.state > 9:
						obj.state = self.state
					else:
						self.populate(1606,"Bad state parameter")
						return
				if self.team != None:
					if len(self.name) > 0: 
						obj.team = self.team
					else:
						self.populate(1607,"Bad team parameter")
						return
				obj.save_user()
				self.populate(200,"OK")
			except Exception, e:
				self.populate(1602,e.__str__())
				return
		else:
			self.populate(1601,"Invalid API edit call: Missing valid target parameter")
			return
	
	def delete(self):
		if self.target == "alert" or self.target == "alerts":
			try:
				obj = Alert.Alert(self.id)
				obj.delete_alert()
				self.populate(200,"OK")
			except Exception, e:
				self.populate(1502,e.__str__())
				return
		elif self.target == "user" or self.target == "users":
			try:
				obj = User.User(self.id)
				obj.delete_user()
				self.populate(200,"OK")
			except Exception, e:
				self.populate(1502,e.__str__())
				return
		else:
			self.populate(1501,"Invalid API delete call: Missing valid target parameter")
			return
		
	def populate(self,status=500, status_message="Internal application layer error", json=None):
		self.status = status
		self.status_message = status_message
		self.json = json
		if self.status % 100 != 0:
			logging.error(self.status_message)
		fulljson = {}
		fulljson['status'] = self.status
		fulljson['message'] = self.status_message
		fulljson['data'] = self.json
		self.fulljson = fulljson
	
	def print_obj(self):
		pprint (vars(self))