#!/usr/bin/env python

# twilio layber

import os, sys

from twilio.rest import TwilioRestClient
from twilio import twiml

# add this file location to sys.path
cmd_folder = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if cmd_folder not in sys.path:
     sys.path.insert(0, cmd_folder)
     sys.path.insert(0, cmd_folder + "/classes")

# load configuration settings (dict conf)
from config import *

logging.basicConfig(format='%(asctime)s - %(levelname)s: %(message)s', filename=conf['logdir'] + '/server.log',level=logging.DEBUG, datefmt='%m/%d/%Y %I:%M:%S %p')

import user as User
import alert as Alert

def auth(user):
	'''
	This method finds the appropriate twilio account and token info for the user to use and authenticates with twilio.
	'''
	logging.debug("Authenticating with twilio")
	if isinstance( conf['twilio_acct'], str) and isinstance( conf['twilio_token'], str):
		return TwilioRestClient(conf['twilio_acct'], conf['twilio_token'])
	else:
		if conf['twilio_acct'][user.team] and conf['twilio_token'][user.team]:
			return TwilioRestClient(conf['twilio_acct'][user.team], conf['twilio_token'][user.team])
		elif conf['twilio_acct']['default'] and conf['twilio_token']['default']:
			return TwilioRestClient(conf['twilio_acct']['default'], conf['twilio_token']['default'])
		else:
			logging.error("Cannot find valid twilio account and/or token. Check your conf file is setup correctly.")
			sys.exit(1)
	return False

def twil_phone_num(user):
	'''
	This method finds the appropriate twilio phone number for the user
	'''
	logging.debug("Getting associated twilio number with user/team")
	if isinstance( conf['twilio_number'], str):
		return conf['twilio_number']
	else:
		if conf['twilio_number'][user.team]:
			return conf['twilio_number'][user.team]
		elif conf['twilio_number']['default']:
			return conf['twilio_number']['default']
		else:
			print "cannot find valid twilio phone number"
			sys.exit(1)
	return False

def twil_reverse_phone_num(phonenum):
	'''
	This method finds a team associated with a phone number
	'''
	logging.debug("Getting associated team with phone number")
	team=''
	for key, value in conf['twilio_number'].iteritems():
		if value == phonenum:
			team = key
			break
	if team == '': team = 'default'
	return team
    
def send_sms(user, alert_id, _message):
	'''
	This method sends a text message to a user
	'''
	logging.debug("Sending sms message to: %s, %s" % (user.name, _message))
	user.lastAlert = alert_id
	user.save_user()
	return auth(user).sms.messages.create(to=user.phone, from_=twil_phone_num(user), body=_message)

def make_call(user, alert):
	'''
	This method calls a user about an alert
	'''
	logging.debug("Calling user: %s" % user.name)
	user.lastAlert = alert.id
	user.save_user()
	return auth(user).calls.create(to=user.phone, from_=twil_phone_num(user), url='''%s:%s/call/alert?init=True&alert_id=%s''' % (conf['server_address'],conf['port'],alert.id))
	
def validate_phone(user):
	'''
	This method attempts to authenticate a user's phone number with Twilio
	'''
	logging.debug("Creating validation code for new phone number/user")
	try:
		response = auth(user).caller_ids.validate(user.phone)
		return response["validation_code"]
	except Exception, e:
		if e.status == 400:
			return True
		else:
			logging.error(e.__str__())
			return False