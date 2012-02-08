#!/usr/bin/env python

import os
import sys
import logging
from optparse import OptionParser

# add this file location to sys.path
cmd_folder = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if cmd_folder not in sys.path:
     sys.path.insert(-1, cmd_folder)
     sys.path.insert(-1, cmd_folder + "/classes")

import mysql_layer as mysql
import twilio_layer as twilio
import user_layer as User
import alert_layer as Alert
import util_layer as Util

conf = Util.load_conf()

Util.init_logging("client")

def user():
	'''
	This function handles the rest of the command as it pertains to a user(s).
	'''
	# Parse the command line
	parser = OptionParser()
	parser.add_option('-i', '--id', dest='id', help='User id', type='int', default=0)
	parser.add_option('-n', '--name', dest='name', help='User name', type='string', default='')
	parser.add_option('-p', '--phone', dest='phone', help='Phone number', type='string', default='')
	parser.add_option('-e', '--email', dest='email', help='Email address', type='string', default='')
	parser.add_option('-t', '--team', dest='team', help='Team', type='string', default='')
	# default is set to 100 as an easy means of figuring out if an state is inputted by user
	parser.add_option('-s', '--state', dest='state', help='State (0 = in rotation, 3 = off rotation, 9 = global entity)', type='int', default=100)
	parser.add_option('-d', '--delete', dest='delete', help='Delete result of user list query', action="store_true", default=False)
	parser.add_option('-f', '--from', dest='_from', help='The phone number of the person using oncall (for sms identication purposes)', type='string', default='')
	(opts, args) = parser.parse_args()
	
	user_usage='''
oncall.py user create (options)
oncall.py user list (options)
oncall.py user edit -i <id> (options)
	'''

	if (len(sys.argv) > 2) and sys.argv[2] in ['create', 'list', 'edit']:
		mode = sys.argv[2]
		if mode == "create": o = user_create(opts)
		if mode == "list": o = user_list(opts)
		if mode == "edit": o = user_edit(opts)
		return o
	else:
		return user_usage

def user_create(opts):
	'''
	Create a new user in the db.
	'''
	try:
		if opts.name == '': return "User name is not set (-n)"
		if opts.email == '': return "User email is not set (-e)"
		if opts.phone == '' and opts.state != 9: return "User phone is not set (-p)"
		if "@" not in opts.email or "." not in opts.email: return "Invalid email address, try again"
		if (opts.phone.startswith("+") and len(opts.phone) == 12):
			pass
		else:
			if opts.state != 9: return "Invalid phone number format. Must be like '+12225558888' (no quotes)"
		if opts.team == '':	opts.team = "default"
		if opts.state == 100: opts.state = 0
		newuser = User.User()
		newuser.name = opts.name
		newuser.email = opts.email
		newuser.phone = opts.phone
		if opts.team != '': newuser.team = opts.team
		if opts.state != 100: newuser.state = opts.state
		newuser.save_user()
		# validate the phone number with twilio
		if opts.state != 9:
			valid_code = twilio.validate_phone(newuser)
			if valid_code == False:
				logging.error("Unable to get a validation code for new phone number")
				return newuser.print_user() + "\nUnable to get a validation code. Please verify new phone number through Twilio website"
			elif valid_code == True:
				return newuser.print_user() + "\nPhone has already been verified with Twilio"
			else:
				return newuser.print_user() + "\nValidation Code: %s" % (valid_code)
		else:
			return newuser.print_user()
	except Exception, e:
		logging.error("Failed to create new user: %s" % (e))
		return "Failed to create user: %s" % (e.__str__())
		
def user_list(opts):
	'''
	List users. Filter with options.
	'''
	all_users = User.all_users()
	users = []
	# init these variables with value True
	(id, name, phone, email, team, state) = [True] * 6
	# filter users with options given
	for u in all_users:
		if opts.id != 0 and u.id != opts.id: id = False
		if opts.name != '' and u.name != opts.name: name = False
		if opts.phone != '' and u.phone != opts.phone: phone = False
		if opts.email != '' and u.email != opts.email: email = False
		if opts.team != '' and u.team != opts.team: team = False
		if opts.state != 100 and u.state != opts.state: state = False
		# see if all values given match attributes for user object
		if id == True and name == True and phone == True and email == True and team == True and state == True: users.append(u)
	if len(users) == 0: return "No users."
	if opts.delete == True:
		output = "Deleting users...\n"
	else:
		output = ''
	for u in users:
		output=output + "%s" % (u.print_user())
		if opts.delete == True: u.delete_user()
	return output

def user_edit(opts):
	'''
	Making changes to a user account with options inputted.
	'''
	if opts.id == '' or opts.id == 0: return "User id is not set (-i)"
	user = User.User(opts.id)
	if opts.name != '': user.name = opts.name
	if opts.phone != '': user.phone = opts.phone
	if opts.email != '': user.email = opts.email
	if opts.team != '':	user.team = opts.team
	if opts.state != '' and opts.state != 100: user.state = opts.state
	user.save_user()
	return user.print_user()

def alert():
	'''
	This function handles the rest of the command as it pertains to an alert(s).
	'''
	# Parse the command line
	parser = OptionParser()
	parser.add_option('-i', '--id', dest='id', help='Alert id', type='int', default=0)
	parser.add_option('-t', '--team', dest='team', help='The team you want to send the message to', type='string', default='default')
	parser.add_option('-f', '--from', dest='_from', help='The phone number of the person using oncall (for sms identication purposes)', type='string', default='')
	parser.add_option('-a', '--ack', dest='ack', help='Ack the results of alert list query', action="store_true", default=False)
	(opts, args) = parser.parse_args()
	
	user_usage='''
oncall.py alert status -t <team> -a
oncall.py alert ack -i <id> -f <phone number>
	'''

	if (len(sys.argv) > 2) and sys.argv[2] in ['status', 'ack']:
		mode = sys.argv[2]
		#if mode == "create": o = alert_create(opts)
		if mode == "status": o = alert_status(opts)
		#if mode == "acked": o = alert_acked(opts)
		#if mode == "all": o = alert_all(opts)
		if mode == "ack": o = alert_ack(opts)
		return o
	else:
		return user_usage

def alert_create(opts):
	'''
	Creating a new alert. Currently not in use.
	'''
	try:
		if opts.subject == '': return "Subject is not set (-s)"
		if opts.message == '': return "Message is not set (-m)"
		if opts.team == '': opts.team = "default"
		newalert = Alert.Alert()
		newalert.subject = opts.subject
		newalert.message = opts.message
		if opts.team != '': newalert.team = opts.team
		newalert.save_alert()
		return newalert.print_alert()
	except Exception, e:
		return "Failed to create alert: %s" % (e.__str__())

def alert_status(opts):
	'''
	Printing out alerts that haven't been acked. If -a is given, will ack them.
	'''
	user = None
	alerts = Alert.status()
	if len(alerts) == 0: return "No active alerts."
	if opts.ack == True:
		if opts._from == '':
			return "Must use option -f to ack alerts"
		else:
			user = User.get_user_by_phone(opts._from)
			output = "Acking alerts as %s...\n" % (u.name)
	else:
		output = ''
	for a in alerts:
		output=output + "%s" % (a.print_alert())
		if user != None: a.ack_alert(user)
	return output

def alert_acked(opts):
	'''
	Printing out alerts acked. Currently not in use.
	'''
	alerts = Alert.acked()
	if len(alerts) == 0: return "No acked alerts."
	output = ''
	for a in alerts:
		output=output + "%s" % (a.print_alert())
	return output

def alert_all(opts):
	'''
	Printing out all alerts. Currently not in use.
	'''
	alerts = Alert.all_alerts()
	if len(alerts) == 0: return "No alerts."
	output = ''
	for a in alerts:
		output=output + "%s" % (a.print_alert())
	return output

def alert_ack(opts):
	'''
	Acking a specific alert. Assumes the last alert to be sent to user if not given.
	'''
	user = None
	if opts._from == '': return "Must use option -f to go on/off call"
	user = User.get_user_by_phone(opts._from)
	if user == False: return "No user ends with that phone number (-f)"
	output = "Acking alerts as %s...\n" % (user.name)
	if opts.id > 0:
		alert = Alert.Alert(opts.id)
		alert.ack_alert(user)
		return "Acknowledged"
	if user.lastAlert > 0:
		alert = Alert.Alert(user.lastAlert)
		alert.ack_alert(user)
		return "Acknowledged"
	else:
		return "No alert associated with your user"

def oncall():
	# Parse the command line
	parser = OptionParser()
	parser.add_option('-s', '--state', dest='state', help='On call stage (1 = primary, 2= secondary, etc)', type='int', default=1)
	parser.add_option('-t', '--team', dest='team', help='A team name', type='string', default='default')
	parser.add_option('-f', '--from', dest='_from', help='The phone number of the person using oncall (for sms identication purposes)', type='string', default='')
	(opts, args) = parser.parse_args()
	
	user_usage='''
oncall.py oncall on -s <state> -f <phone>
oncall.py oncall off -f <phone>
oncall.py oncall status -t <team>
	'''

	if (len(sys.argv) > 2) and sys.argv[2] in ['on', 'off', 'status']:
		mode = sys.argv[2]
		if mode == "off": opts.state = 0
		if mode == "on" or mode == "off": o = oncall_change(opts)
		if mode == "status": o = oncall_status(opts)
		return o
	else:
		return user_usage

def oncall_change(opts):
	'''
	Change your own oncall status
	'''
	user = None
	if opts._from == '': return "Must use option -f to go on/off call"
	user = User.get_user_by_phone(opts._from)
	if user == False: return "No user ends with that phone number (-f)"
	user.print_user()
	user.state = opts.state
	user.save_user()
	if user.state > 0:
		return "You, %s, are now on call" % user.name
	else:
		return "You, %s, are now off call" % user.name

def oncall_status(opts):
	'''
	Get a list of people oncall for a specific team
	'''
	users = User.on_call(opts.team)
	oncall_users = []
	for u in users:
		if u.state > 0 and u.state < 9:
			oncall_users.append(u)
	if len(oncall_users) == 0: return "No one is on call on the %s team." % (opts.team)
	output = ''
	for user in oncall_users:
		output=output + "%s" % (user.print_user())
	return output

def run(args):
	'''
	This gets run from oncall-server to execute the Oncall CLI
	'''
	# convert argsuments into input params
	sys.argv = args.split()
	# gotta pad the arguments because usually sys.argv[0] is the python file name
	sys.argv.insert(0, 'spacer')
	return main()

def main():
	usage = '''
oncall.py user create (options)
oncall.py user list (options)
oncall.py user edit -i <id> (options)

oncall.py alert status -t <team> -a
oncall.py alert ack -i <id> -f <phone number>

oncall.py oncall on -s <state> -f <phone>
oncall.py oncall off -f <phone>
oncall.py oncall status -t <team>
'''

	# converting all parameters to be lowercase to remove any case sensitivity
	sys.argv = map(lambda x:x.lower(),sys.argv)

	if (len(sys.argv) > 1) and sys.argv[1] in ['user', 'users', 'status', 'alert', 'alerts', 'ack', 'rotation', 'oncall']:
		mode = sys.argv[1]
		if mode == "user" or mode == 'users': o = user()
		if mode == "alert" or mode == 'alerts': o = alert()
		if mode == "status":
			sys.argv.insert(1, "alert")
			o = alert()
		if mode == "ack": 
			sys.argv.insert(1, "alert")
			o = alert()
		if mode == "oncall": o = oncall()
		#if mode == "rotation": o = rotation()
		logging.info("Oncall.py output: %s" % o)
		return o
	else:
		return usage

if __name__ == "__main__": print main()