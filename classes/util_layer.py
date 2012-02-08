#!/usr/bin/env python
# load configuraiton of Oncall

from ConfigParser import SafeConfigParser
import ast, logging


def init_logging(log_file_name = 'server'):
	'''
	Loads logging with a file destination
	var log_file_name is the file name without a file extension
	'''
	conf = load_conf()
	logging.basicConfig(format='%(asctime)s - %(levelname)s: %(message)s', filename='%s/%s.log' % (conf['logdir'], log_file_name),level=logging.DEBUG, datefmt='%m/%d/%Y %I:%M:%S %p')

def load_conf(config_file = 'oncall.conf'):
	'''
	This function loads the conf file into the program's memory
	'''
	parser = SafeConfigParser()
	parser.read(config_file)
	conf={}
	#take in all keys and values from the conf file into the variable "conf"
	for section_name in parser.sections():
		for name, value in parser.items(section_name):
			conf[name] = value
	# making sure a mysql password is set
	if 'mysql_passwd' not in conf:
		conf['mysql_passwd'] = ''
	
	# converting these from strings to dict
	def convert_to_dict(var):
		'''
		Converts a string (input) to a dictionary (output)
		'''
		try:
			var = ast.literal_eval(var)
			return var
		except:
			# check if value is a single word, in which case, assume as default
			if len(var.split()) == 1:
				var={'default':var}
				return var
			else:
				logging.critical("Bad configuration variable: %s" % (var))
				raise "Bad configuration variable: %s" % (var)
	
	# converting strings to dictionaries
	conf['twilio_acct']=convert_to_dict(conf['twilio_acct'])
	conf['twilio_token']=convert_to_dict(conf['twilio_token'])
	conf['twilio_number']=convert_to_dict(conf['twilio_number'])
	
	
	# converting strings to integers
	conf['alert_interval']=int(conf['alert_interval'])
	conf['alert_escalation']=int(conf['alert_escalation'])
	conf['team_failover']=int(conf['team_failover'])
	conf['call_failover']=int(conf['call_failover'])
	conf['alert_freshness']=int(conf['alert_freshness'])
	conf['mysql_port']=int(conf['mysql_port'])
	conf['email_port']=int(conf['email_port'])
	return conf
	
#load conf file
#conf = load_conf()

# initiate logging
# init_logging()