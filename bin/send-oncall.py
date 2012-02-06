#!/usr/bin/env python

import sys, urllib, urllib2
from optparse import OptionParser

# Parse the command line
parser = OptionParser()
parser.add_option('-s', '--subject', dest='subject', help='The subject line (required)', type='string', default='')
parser.add_option('-m', '--message', dest='message', help='The body of the message (required)', type='string', default='')
parser.add_option('-t', '--team', dest='team', help='The team you want to send the message to', type='string', default='default')
parser.add_option('-q', '--host', dest='host', help='Oncall Host', type='string', default='localhost')
parser.add_option('-p', '--port', dest='port', help='Oncall Port', type='int', default=8008)
parser.add_option('-w', '--passwd', dest='passwd', help='Oncall server security password (optional)', type='string', default='')
(opts, args) = parser.parse_args()

# create encoded url query
if opts.host.startswith('http'):
	query='%s:%i/alert/event?message=%s&subject=%s&team=%s&passwd=%s' % (opts.host, opts.port,urllib.quote_plus(opts.message),urllib.quote_plus(opts.subject),urllib.quote_plus(opts.team),urllib.quote_plus(opts.passwd))
else:
	query='http://%s:%i/alert/event?message=%s&subject=%s&team=%s&passwd=%s' % (opts.host, opts.port,urllib.quote_plus(opts.message),urllib.quote_plus(opts.subject),urllib.quote_plus(opts.team),urllib.quote_plus(opts.passwd))

try:
	# query the server
	req = urllib2.Request(query)
	response = urllib2.urlopen(req)
	rawreturn = response.read()
except urllib2.URLError, e:
	if e.reason[0] == 61:
		print "Unable to contact server. Check that the service is running on the server and you are inputting the correct host (-q) and port (-p)"
	else:
		print e
	sys.exit(1)

if rawreturn.startswith("OK"):
	print "Successfully sent message: %s" % (rawreturn)
	sys.exit(0)
else:
	print "Failed to send message: %s" % (rawreturn)
	sys.exit(1)