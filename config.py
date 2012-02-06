#!/usr/bin/env python
# load configuraiton of Oncall

from ConfigParser import SafeConfigParser
import ast, logging

parser = SafeConfigParser()
parser.read('oncall.conf')

conf={}

for section_name in parser.sections():
    for name, value in parser.items(section_name):
        conf[name] = value

logging.basicConfig(format='%(asctime)s - %(levelname)s: %(message)s', filename=conf['logdir'] + '/server.log',level=logging.DEBUG, datefmt='%m/%d/%Y %I:%M:%S %p')
logging.debug("Loading configuration")

# making sure a mysql password is set
try:
	conf['mysql_passwd']
except:
	conf['mysql_passwd'] = ''

# converting these from strings to dict
def convert_to_dict(var):
	try:
		var = ast.literal_eval(var)
		return var
	except:
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
conf['twilio_pin']=convert_to_dict(conf['twilio_pin'])


# converting numbers as strings to integers
conf['alert_interval']=int(conf['alert_interval'])
conf['alert_escalation']=int(conf['alert_escalation'])
conf['team_failover']=int(conf['team_failover'])
conf['call_failover']=int(conf['call_failover'])
conf['alert_freshness']=int(conf['alert_freshness'])
conf['mysql_port']=int(conf['mysql_port'])