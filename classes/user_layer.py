#!/usr/bin/env python

import logging
import MySQLdb
import datetime

import mysql_layer as mysql
import twilio_layer as twilio

def query(q_string):
	'''
	Query the db with the given string and return with an array of user objects.
	'''
	try:
		_db = mysql.Database()
		_db._cursor.execute( '''%s''' % (q_string))
		logging.debug("Running mysql query: %s" % q_string)
		temp = _db._cursor.fetchall()
		users = []
		for t in temp:
			t = mysql.users_convert_to_dict(t)
			users.append(User(t['id']))
		return users
	except Exception, e:
		logging.error(e.__str__())

def all_users():
	'''
	Get all users from the db.
	'''
	return query('''SELECT * FROM users''')

def on_call(team=''):
	'''
	Get a list of all users that are currently on call.
	'''
	if team == '':
		return query('''SELECT * FROM users WHERE state > 0 and state < 9 ORDER BY state''')
	else:
		return query('''SELECT * FROM users WHERE state > 0 and state < 9 and team = "%s" ORDER BY state''' % team)

def sort_by_state(user_list):
	'''
	This function sorts a 1 dimensional user list into a two dimensional user list, sorted by user's state.
	'''
	oncall_users_sorted = []
	# sorting on call users by state
	for i in range (1,9):
		new = []
		for u in user_list:
			if u.state == i:
				new.append(u)
		oncall_users_sorted.append(new)
	return oncall_users_sorted
	
def team_entities(team=''):
	'''
	Get a list of all users that are currently on call
	'''
	if team == '':
		return query('''SELECT * FROM users WHERE state = 9 ORDER BY state''')
	else:
		return query('''SELECT * FROM users WHERE state = 9 and team = "%s" ORDER BY state''' % team)

def get_user_by_phone(phone):
	'''
	Load user by their phone number (pattern matching by 'ends with')
	'''
	try:
		x = query('''SELECT * FROM users WHERE phone LIKE '%%%s' LIMIT 1''' % phone)
		if len(x) == 0: return False
		return x[0]
	except Exception, e:
		logging.error(e.__str__())
		return False

class User:
	def __init__(self, id=0):
		'''
		This initializes a user object. If id is given, loads that user. If not, creates a new user object with default values.
		'''
		logging.debug("Initializing user: %s" % id)
		self.db = mysql.Database()
		if id == 0:
			self.name = ''
			self.phone = ''
			self.email = ''
			self.state = 0
			self.team = 'default'
			self.lastAlert = 0
			self.id = id
		else:
			self.load_user(id)

	def load_user(self, id, as_dict=False):
		'''
		load a user with a specific id
		'''
		logging.debug("Loading user: %s" % id)
		try:
			self.db._cursor.execute( '''SELECT * FROM users WHERE id = %s''', id)
			user = mysql.users_convert_to_dict(self.db._cursor.fetchone())
			if as_dict == True: return user
			self.name = user['name']
			self.phone = user['phone']
			self.email = user['email']
			self.state = user['state']
			self.team = user['team']
			self.lastAlert = user['lastAlert']
			self.createDate = user['createDate']
			self.id = user['id']
		except Exception, e:
			logging.error(e.__str__())
			self.id = 0
	
	def convert_to_dict(self):
		'''
		This method converts a user object to a dictionary.
		'''
		logging.debug("Converting user object to dictionary")
		user = {}
		user['id'] = self.id
		user['name'] = self.name
		user['email'] = self.email
		user['state'] = self.state
		user['team'] = self.team
		user['lastAlert'] = str(self.lastAlert)
		user['createDate'] = str(self.createDate)
		user['phone'] = self.phone
		return user
	
	def save_user(self):
		'''
		Save the user to the db.
		'''
		logging.debug("Saving user: %s" % self.name)
		try:
			self.db._cursor.execute('''REPLACE INTO users (id,name,email,phone,team,state,lastAlert) VALUES (%s,%s,%s,%s,%s,%s,%s)''', (self.id,self.name,self.email,self.phone,self.team,self.state,self.lastAlert))
			self.db.save()
		except Exception, e:
			logging.error(e.__str__())
			
	def delete_user(self):
		'''
		Delete the user form the db.
		'''
		logging.debug("Deleting user: %s" % self.name)
		try:
			self.db._cursor.execute('''DELETE FROM users WHERE id=%s''', (self.id))
			self.db.save()
			self.db.close()
		except Exception, e:
			logging.error(e.__str__())
			
	def print_user(self, SMS=False):
		'''
		Print out the contents of a user object. SMS variable makes output SMS friendly.
		'''
		if SMS == True:
			output = "name:%s|phone: %s |team:%s|state:%i\n" % (self.name, self.phone, self.team, self.state)
		else:
			output = "id:%i\tname:%s\tphone:%s\temail:%s\tteam:%s\tstate:%i\n" % (self.id, self.name, self.phone, self.email, self.team, self.state)
		logging.debug("Printing user: %s" % output)
		return output