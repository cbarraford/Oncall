#!/usr/bin/env python

import os, sys
import MySQLdb
import datetime, math, logging, traceback

# add this file location to sys.path
cmd_folder = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if cmd_folder not in sys.path:
     sys.path.insert(0, cmd_folder)
     sys.path.insert(0, cmd_folder + "/classes")

import mysql_layer as mysql
import twilio_layer as twilio
import user as User
# load configuration settings (dict conf)
from config import *

logging.basicConfig(format='%(asctime)s - %(levelname)s: %(message)s', filename=conf['logdir'] + '/alerts.log',level=logging.DEBUG, datefmt='%m/%d/%Y %I:%M:%S %p')

def query(q_string):
	'''
	Query the db with the given string and return with an array of alert objects
	'''
	try:
		_db = mysql.Database()
		_db._cursor.execute( '''%s''' % (q_string))
		logging.debug("Running mysql query: %s" % q_string)
		temp = _db._cursor.fetchall()
		alerts = []
		for t in temp:
			t = mysql.alerts_convert_to_dict(t)
			a = Alert(t['id'])
			alerts.append(a)
		return alerts
	except Exception, e:
		logging.error(e.__str__())

def all_alerts():
	'''
	Get all alerts
	'''
	return query('''SELECT * FROM alerts''')

def status():
	'''
	All active alerts
	'''
	return query('''SELECT * FROM alerts WHERE ack = 0 ORDER BY createDate''')

def acked():
	'''
	Get the last 20 inactive alerts
	'''
	return query('''SELECT * FROM alerts WHERE ack = 1 ORDER BY createDate LIMIT 20''')

def fresh_alerts():
	'''
	This returns a list of alerts that are considered "fresh". These are compared to incoming alerts to deem that as duplicates of alerts that already exist or not.
	'''
	return query('''select * from alerts where (NOW() - createDate) < %s''' % (conf['alert_freshness']))
	
def check_alerts():
	'''
	This returns a list of alert that need an alert sent out.
	'''
	return query('''SELECT * FROM alerts WHERE ack = 0 AND (NOW() - lastAlertSent) > %s''' % (conf['alert_interval']))

class Alert():
	def __init__(self, id=0):
		logging.debug("Initializing alert: %s" % id)
		self.db = mysql.Database()
		if id == 0:
			self.subject = ''
			self.message = ''
			self.team = 'default'
			self.ack = 0
			self.ackby = 0
			self.acktime = ''
			self.lastAlertSent = ''
			self.tries = 0
			self.id = id
		else:
			self.load_alert(id)

	def load_alert(self, id):
		'''
		load an alert with a specific id
		'''
		logging.debug("Loading alert: %s" % id)
		try:
			self.db._cursor.execute( '''SELECT * FROM alerts WHERE id = %s LIMIT 1''', id)
			alert = self.db._cursor.fetchone()
			alert = mysql.alerts_convert_to_dict(alert)
			self.subject = alert['subject']
			self.message = alert['message']
			self.team = alert['team']
			self.ack = alert['ack']
			self.ackby = alert['ackby']
			self.acktime = alert['acktime']
			self.lastAlertSent = alert['lastAlertSent']
			self.tries = alert['tries']
			self.createDate = alert['createDate']
			self.id = alert['id']
		except Exception, e:
			print "error, loading alert"
			print e
			self.id = 0
	
	def convert_to_dict(self):
		logging.debug("Converting alert object to dictionary")
		alert = {}
		alert['id'] = self.id
		alert['subject'] = self.subject
		alert['message'] = self.message
		alert['ack'] = self.ack
		alert['team'] = self.team
		alert['ackby'] = self.ackby
		alert['createDate'] = str(self.createDate)
		alert['acktime'] = str(self.acktime)
		alert['lastAlertSent'] = str(self.lastAlertSent)
		alert['tries'] = self.tries
		return alert
	
	def save_alert(self):
		'''
		save the alert to the db
		'''
		logging.debug("Saving alert: %s" % self.id)
		try:
			self.db._cursor.execute('''REPLACE INTO alerts (id,subject,message,team,ack,ackby,acktime,lastAlertSent,tries) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)''', (self.id,self.subject,self.message,self.team,self.ack,self.ackby,self.acktime,self.lastAlertSent,self.tries))
			self.db.save()
		except Exception, e:
			logging.error(e.__str__())
	
	def ack_alert(self,user):
		'''
		ack the alert
		'''
		logging.debug("Acknowledging alert: %s" % self.id)
		try:
			self.ack = 1
			self.ackby = user.id
			self.acktime = datetime.datetime.now()
			self.save_alert()
			return True
		except Exception, e:
			logging.error(e.__str__())
			return False
	
	def send_alert(self, team=''):
		logging.debug("Sending alert: %s" % self.id)
		try:
			oncall_users_raw = User.on_call(team)
			team_users = User.team_entities(team)
			if len(oncall_users_raw) > 0:
				oncall_users = []
				self.tries += 1
				self.lastAlertSent = datetime.datetime.now()
				self.save_alert()
				# grouping users into 2D arrays by state
				oncall_users = User.sort_by_state(oncall_users_raw)
				# filtering on call list with only ones to alert
				if "alert_escalation" in conf and conf['alert_escalation'] > 0:
					escalate = float(conf['alert_escalation'])
					num = int(math.ceil(self.tries/escalate))
					if num == 0: num = 1
					alert_users = oncall_users[:num]
				else:
					# just grabbing the primary users (state == 1)
					alert_users = oncall_users[0]
				
				for au in alert_users:
					for u in au:
						if "call_failover" in conf:
							if conf['call_failover'] == 0:
								twilio.make_call(u, self)
							else:
								if int(math.ceil(self.tries/float(u.state))) > conf['call_failover']:
									twilio.make_call(u, self)
								else:
									twilio.send_sms(u, self.id, self.subject + "\n" + self.message)
						else:
							twilio.send_sms(u, self.id, self.subject + "\n" + self.message)
				
				if "team_failover" in conf:
					for t in team_users:
						if conf['team_failover'] == 0:
							pass #email team
						else:
							if conf['team_failover'] >= self.tries:
								pass #email team
			else:
				logging.error("No one is currently on call")
				for t in team_users:
					pass # email team
					
		except Exception, e:
			logging.error(e.__str__())
			traceback.print_exc()
	
	def delete_alert(self):
		'''
		delete the alert form the db
		'''
		logging.debug("Deleting alert: %s" % self.id)
		try:
			self.db._cursor.execute('''DELETE FROM alerts WHERE id=%s''', (self.id))
			self.db.save()
			self.db.close()
		except Exception, e:
			logging.error(e.__str__())
		
	def print_alert(self, SMS=False):
		'''
		print out the contents of an alert
		'''
		if SMS == True:
			output = "ack:%s\ttries:%s\tteam:%s\tsubject:%s\n" % (self.ack, self.tries, self.team, self.subject)
		else:
			output = "id:%i\tack:%s\tacktime:%s\ttries:%s\tteam:%s\tsubject:%s\tmessage:%s\n" % (self.id, self.ack, self.acktime, self.tries, self.team, self.subject, self.message)
		logging.debug("Printing alert: %s" % self.id)
		return output