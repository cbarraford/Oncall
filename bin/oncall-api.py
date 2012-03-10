#!/usr/bin/env python

import web
import os, sys
import urllib
import logging
import time

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
import api_layer as API
import util_layer as Util

conf = Util.load_conf()
Util.init_logging("api")

# set port and IP to listen for alerts
# these are inhereited from the conf file
sys.argv = [conf['api_listen_ip'],conf['api_port']]

# debug mode
web.config.debug = conf['server_debug']

#load valid urls to listen to for http calls
urls = (
    '/api/(.+)', 'api'
)
app = web.application(urls, globals())

class api:
	'''
	This class handles new alerts being set to the Oncall server
	'''
	def GET(self,name):
		data = web.input(action=name)
		logging.info("Receiving a GET api query\n%s" % (data))
		apicall = API.Api(**data)
		return apicall.fulljson
	
	def POST(self, name):
		data = web.input(action=name)
		logging.info("Receiving a POST api query\n%s" % (data))
		apicall = API.Api(**data)
		return apicall.fulljson

if __name__ == "__main__":
	app.run()