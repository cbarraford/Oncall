#!/usr/bin/env python

import web
import os, sys
import urllib
import logging
import time
from multiprocessing import Process

# add this file location to sys.path
cmd_folder = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if cmd_folder not in sys.path:
     sys.path.insert(-1, cmd_folder)
     sys.path.insert(-1, cmd_folder + "/classes")

import mysql_layer as mysql
import twilio_layer as twilio
import oncall
import user_layer as User
import alert_layer as Alert
import util_layer as Util

conf = Util.load_conf()
Util.init_logging("server")

# set port and IP to listen for alerts
# these are inhereited from the conf file
sys.argv = [conf['listen_ip'],conf['port']]

# debug mode
web.config.debug = conf['server_debug']

#load valid urls to listen to for http calls
urls = (
#   '/alert/(.+)', 'alert',
    '/sms/(.+)', 'sms',
    '/call/(.+)', 'call',
)
app = web.application(urls, globals())

class alert:
	'''
	This class handles new alerts being set to the Oncall server
	'''
	def GET(self,name):
		d = web.input()
		logging.info("Receiving an alert\n%s" % (d))
		if d.subject:
			d.subject=urllib.unquote_plus(d.subject)
		else:
			return "No subject. -s is required on sending a oncall message"
		if d.message:
			d.message=urllib.unquote_plus(d.message)
		else:
			return "No message. -m is required on sending a oncall message"
		if d.passwd:
			d.passwd=urllib.unquote_plus(d.passwd)
		if d.team:
			d.team=urllib.unquote_plus(d.team)
		else:
			d.team="default"
		try:
			#check for security password if configured to do so
			goAhead = True
			if "security_passwd" in conf:
				if d.passwd == conf['security_passwd']:
					goAhead = True
				else:
					goAhead = False
			if goAhead == True:
				isNewAlert = True
				# check to see if this alert is a new one
				for a in Alert.fresh_alerts():
					if a.subject == d.subject and a.message == d.message and a.team == d.team: isNewAlert = False
				if isNewAlert == True:
					# save new alert to the db
					newalert = Alert.Alert()
					newalert.subject = d.subject
					newalert.message = d.message
					newalert.team = d.team
					newalert.send_alert()
					return "OK:\n" + newalert.print_alert()
			else:
				return "Not authorized"
		except Exception, e:
			logging.error(e.__str__())
			return e.__str__()

class sms:
	'''
	This class handles SMS messages
	'''
	def POST(self,name):
		d = web.input()
		logging.info("Receiving SMS message\n%s" % (d))
		# incoming text message, handle it
		web.header('Content-Type', 'text/xml')
		r = twilio.twiml.Response()
		user = User.get_user_by_phone(d.From)
		# make sure person sending the text is an authorized user of Oncall
		if user == False:
			logging.error("Unauthorized access attempt via SMS by %s\n%s" % (d.From, d))
			r.sms("You are not a authorized user")
		else:
			# split the output into 160 character segments
			for text_segment in twilio.split_sms(oncall.run(d.Body + " -m -f " + d.From)):
				r.sms(text_segment)
		return r

class call:
	'''
	This class handles phone calls
	'''	
	def POST(self,name):
		d = web.input(init="true", Digits=0)
		logging.info("Receiving phone call\n%s" % (d))
		web.header('Content-Type', 'text/xml')
		r = twilio.twiml.Response()
		# the message to say when a timeout occurs
		timeout_msg = "Sorry, didn't get any input from you. Goodbye."
		# check if this call was initialized by sending an alert
		if name == "alert":
			# the digit options to press
			digitOpts = '''
Press 1 to hear the message.
Press 2 to acknowledge this alert.
'''
			receiver = User.get_user_by_phone(d.To)
			alert = Alert.Alert(d.alert_id)
			# check if this is the first interaction for this call session
			if d.init.lower() == "true":
				with r.gather(action="%s:%s/call/alert?alert_id=%s&init=false" % (conf['server_address'],conf['port'],alert.id), timeout=conf['call_timeout'], method="POST", numDigits="1") as g:
					g.say('''Hello %s, a message from Oncall. An alert has been issued with subject "%s". %s.''' % (receiver.name, alert.subject, digitOpts))
				r.say(timeout_msg)
			else:
				if int(d.Digits) == 1:
					with r.gather(action="%s:%s/call/alert?alert_id=%s&init=false" % (conf['server_address'],conf['port'],alert.id), timeout="30", method="POST", numDigits="1") as g:
						g.say('''%s. %s''' % (alert.message, digitOpts))
					r.say(timeout_msg)
				elif int(d.Digits) == 2:
					if alert.ack_alert(receiver):
						r.say("The alert has been acknowledged. Thank you and goodbye.")
						r.redirect(url="%s:%s/call/alert?alert_id=%s&init=false" % (conf['server_address'],conf['port'],alert.id))
					else:
						r.say("Sorry, failed to acknowledge the alert. Please try it via SMS")
						r.redirect(url="%s:%s/call/alert?alert_id=%s&init=false" % (conf['server_address'],conf['port'],alert.id))
				elif d.Digits == 0:
					with r.gather(action="%s:%s/call/alert?alert_id=%s&init=false" % (conf['server_address'],conf['port'],alert.id), timeout="30", method="POST", numDigits="1") as g:
						g.say('''%s''' % (digitOpts))
					r.say(timeout_msg)
				else:
					r.say("Sorry, didn't understand the digits you entered. Goodbye")
		else:
			requester = User.get_user_by_phone(d.From)
			# get the team that is associate with this phone number the user called
			team = twilio.twil_reverse_phone_num(d.To)
			# if caller is not a oncall user or they are, but calling a different team then they are in
			if requester == False or requester.team != team:
				if team == '':
					r.say("Sorry, The phone number you called is not associated with any team. Please contact you system administrator for help.")
				else:
					# get the first user on call and forward the call to them
					oncall_users = User.sort_by_state(User.on_call(team))
					if len(oncall_users) > 0:
						foundOncallUser = False
						for userlist in oncall_users:
							for u in userlist:
								r.say("Calling %s." % u.name)
								r.dial(number=u.phone)
								foundOncallUser = True
								break
							if foundOncalluser == True: break
					else:
						r.say("Sorry, currently there is no one on call for %s. Please try again later." % team)
			else:
				# the caller is calling the same team phone number as the team that they are on
				# check if d.Digits is the default value (meaning, either the caller hasn't pushed a button and this is the beginning of the call, or they hit 0 to start over
				if int(d.Digits) == 0:
					if d.init.lower() == "true":
						if requester.state > 0 and requester.state < 9: 
							oncall_status = "You are currently on call in spot %s" % (requester.state)
						else:
							oncall_users = User.sort_by_state(User.on_call(requester.team))
							if len(oncall_users) > 0:
								for userlist in oncall_users:
									for u in userlist:
										oncall_status = "Currenty, %s is on call" % (u.name)
							else:
								oncall_status = "Currenty, no one is on call"
						with r.gather(action="%s:%s/call/event?init=false" % (conf['server_address'],conf['port']), timeout=conf['call_timeout'], method="POST", numDigits="1") as g:
							g.say('''Hello %s. %s. Press 1 if you want to hear the present status of alerts. Press 2 to acknowledge the last alert sent to you. Press 3 to conference call everyone on call into this call.''' % (requester.name, oncall_status))
					else:
						with r.gather(action="%s:%s/call/event?init=false" % (conf['server_address'],conf['port']), timeout=conf['call_timeout'], method="POST", numDigits="1") as g:
							g.say('''Press 1 if you want to hear the present status of alerts. Press 2 to acknowledge the last alert sent to you. Press 3 to conference call everyone on call into this call.''')
					r.say(timeout_msg)
				elif int(d.Digits) == 1:
					# getting the status of alerts
					r.say(oncall.run("alert status -f " + requester.phone))
					r.redirect(url="%s:%s/call/event?init=false" % (conf['server_address'],conf['port']))
				elif int(d.Digits) == 2:
					# acking the last alert sent to the user calling
					r.say(oncall.run("alert ack -f " + requester.phone))
					r.redirect(url="%s:%s/call/event?init=false" % (conf['server_address'],conf['port']))
				elif int(d.Digits) == 3:
					# calling the other users on call
					oncall_users_raw = User.on_call(requester.team)
					for user in oncall_users_raw:
						if user.phone == requester.phone: continue
						r.say("Calling %s." % user.name)
						r.dial(number=user.phone)
				else:
					r.say("Sorry, number you pressed is not valid. Please try again.")
		return r

def check_alerts():
	'''
	This function runs in an infinite loop to find any unacked alerts that need an alert to be sent out.
	'''
	foobar = True
	while foobar == True:
		for a in Alert.check_alerts():
			a.send_alert()
		time.sleep(5)

if __name__ == "__main__":
	p = Process(target=check_alerts)
	p.start()
	app.run()