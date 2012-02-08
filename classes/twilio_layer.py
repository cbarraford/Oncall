#!/usr/bin/env python
# twilio layer

import logging

from twilio.rest import TwilioRestClient
from twilio import twiml

import user_layer as User
import alert_layer as Alert
import util_layer as Util

conf = Util.load_conf()

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
	This method finds the appropriate twilio phone number for the user.
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
	This method finds a team associated with a phone number.
	'''
	logging.debug("Getting associated team with phone number")
	team=''
	for key, value in conf['twilio_number'].iteritems():
		if value == phonenum:
			team = key
			break
	if team == '': team = 'default'
	return team

def split_sms(sms):
	'''
	This function splits an sms messages into 160 character list, so it can send parts of message in 160 char segments.
	'''
	if len(sms) > 160:
		output = []
		while len(sms) > 160:
			output.append(sms[:160])
			sms = sms[160:]
		if len(sms) > 0: output.append(sms)
		return output
	else:
		return [sms]
    
def send_sms(user, alert_id, _message):
	'''
	This method sends a text message to a user.
	'''
	logging.debug("Sending sms message to: %s, %s" % (user.name, _message))
	user.lastAlert = alert_id
	user.save_user()
	myauth = auth(user)
	from_phone = twil_phone_num(user)
	for text_segment in split_sms(_message):
		myauth.sms.messages.create(to=user.phone, from_=from_phone, body=text_segment)

def make_call(user, alert):
	'''
	This method calls a user about an alert.
	'''
	logging.debug("Calling user: %s" % user.name)
	user.lastAlert = alert.id
	user.save_user()
	return auth(user).calls.create(to=user.phone, from_=twil_phone_num(user), url='''%s:%s/call/alert?init=True&alert_id=%s''' % (conf['server_address'],conf['port'],alert.id))
	
def validate_phone(user):
	'''
	This method attempts to authenticate a user's phone number with Twilio.
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