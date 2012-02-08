#!/usr/bin/env python

import logging
from email.mime.text import MIMEText
import smtplib

import mysql_layer as mysql
import twilio_layer as twilio
import user_layer as User
import util_layer as Util

conf = Util.load_conf()

class Email:
	def __init__(self, user=None, alert=None):
		'''
		Initiation of email class.
		'''
		self.smtp = conf['email_server']
		self.port = conf['email_port']
		self.username = conf['email_username']
		self.passwd = conf['email_passwd']
		self.subject = ''
		self.message = ''
		self.user = user
		self.alert = alert
	
	def send_alert_email(self):
		'''
		Send an alert via email.
		'''
		self.to = self.user.email
		self.subject = "Alert from Oncall: %s" % self.alert.subject
		self.message = self.alert.message
		message = MIMEText(self.message)
		message['Subject'] = self.subject
		message['From'] = self.username
		message['To'] = self.to
		try:
			mailServer = smtplib.SMTP(self.smtp, self.port)
			mailServer.ehlo()
			mailServer.starttls()
			mailServer.ehlo()
			mailServer.login(self.username,self.passwd)
			mailServer.sendmail(self.username,self.to,message.as_string())
			mailServer.close()
			logging.info("Sent email to %s\n%s" % (self.to, self.message))
		except Exception, e:
			logging.error("Failed to send email to %s\n%s" % (self.to, self.message))
			logging.error(e.__str__())
	
	def send_custom_email(self, to='', subject='', message=''):
		'''
		Send a custom email specifiying a to address, subject line, and message.
		'''
		self.to = to
		self.subject = subject
		self.message = message
		message = MIMEText(self.message)
		message['Subject'] = self.subject
		message['From'] = self.username
		message['To'] = self.to
		try:
			mailServer = smtplib.SMTP(self.smtp, self.port)
			mailServer.ehlo()
			mailServer.starttls()
			mailServer.ehlo()
			mailServer.login(self.username,self.passwd)
			mailServer.sendmail(self.username,self.to,message.as_string())
			mailServer.close()
			logging.info("Sent email to %s\n" % (self.to, self.message))
		except Exception, e:
			logging.error("Failed to send email to %s\n%s" % (self.to, self.message))
			logging.error(e.__str__())