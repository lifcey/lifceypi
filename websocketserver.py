#! /usr/bin/env python

import tornado.auth
import tornado.escape
import tornado.options
import tornado.web
import tornado.websocket
import tornado.httpserver
import tornado.ioloop
import tornado.gen
import Settings
import Repository
import threading
import time
import sys
import gpiozero
import json
import pigpio
import DHT22
import requests
from requests.auth import HTTPBasicAuth
from requests.auth import HTTPDigestAuth
from lxml import html

from time import sleep


from tornado.options import define, options
define("port", default=8081, help="run on the given port", type=int)

from RepoUsers import RepoUsers
from RepoSettings import RepoSettings

lstRelays = []


class BaseHandler(tornado.web.RequestHandler):
	def get_current_user(self):
		curuser = ""
		if self.get_secure_cookie("user"):
			curuser = tornado.escape.json_decode(self.get_secure_cookie("user"))
		return curuser


class AuthLoginHandler(BaseHandler):
	def get(self):
		params = {
			"errormessage": self.get_argument("error",''),
			"nextpage": self.get_argument("next", "/")
		}
		self.render('login.html', **params)


	def check_permission(self, password, username):
		repo = RepoUsers()
		if repo.validate_user(username, password):
			return True
		return False

	def post(self):
		username = self.get_argument("username", "")
		password = self.get_argument("password", "")

		auth = self.check_permission(password, username)
		if auth:
			self.set_current_user(username)
			self.redirect(self.get_argument("next", u"/"))
		else:
			error_msg = u"?error=" + tornado.escape.url_escape("Login incorrect")
			self.redirect(u"/auth/login/" + error_msg)

	def set_current_user(self, user):
		if user:
			self.set_secure_cookie("user", tornado.escape.json_encode(user))
		else:
			self.clear_cookie("user")


class AuthLogoutHandler(BaseHandler):
	def get(self):
		self.clear_cookie("user")
		self.redirect(self.get_argument("next", "/"))



class MainHandler(BaseHandler):
	def get(self):
		settings_link = ""
		if self.current_user:
			print (self.current_user)
			#username = tornado.escape.xhtml_escape(self.current_user.strip("\""))
			username = tornado.escape.xhtml_escape(self.current_user)
		else:
			username = ""

		repo = RepoUsers()
		if not username:
			error_msg = u"?error=" + tornado.escape.url_escape("Login incorrect")
			self.redirect(u"/auth/login/" + error_msg)
			return

		if repo.is_admin(username):
			settings_link = '<a class="nav-link" href="/settings/">Settings</a>'

		rs = RepoSettings()
		relays = tornado.escape.json_encode(rs.get_relays())
		dht22s = tornado.escape.json_encode(rs.get_dht22s())
		miners = tornado.escape.json_encode(rs.get_miners())
		self.render("../default.html", username = username, settings_link = settings_link, relays = relays, dht22s = dht22s, miners = miners)

	def post(self, *args):
		dic = {}

		self.write(json.dumps(dic))

		self.finish()



class SettingsHandler(BaseHandler):

	def get(self):
		if self.current_user:
			print (self.current_user)
			username = tornado.escape.xhtml_escape(self.current_user)
		else:
			username = ""

		if username != "admin":
			error_msg = u"?error=" + tornado.escape.url_escape("Login incorrect")
			self.redirect(u"/auth/login/" + error_msg)
			return

		rs = RepoSettings()
		relays = tornado.escape.json_encode(rs.get_relays())
		dht22s = tornado.escape.json_encode(rs.get_dht22s())
		miners = tornado.escape.json_encode(rs.get_miners())
		self.render("../settings.html", username = username, relays = relays, dht22s = dht22s, miners = miners)

	def post(self, *args):
		dic = tornado.escape.json_decode(self.request.body)
		rs = RepoSettings()
		type = dic["type"]
		if type == "relay":
			rs.set_relays(dic["data"])
			self.write(json.dumps({'status': 'ok', 'sent': dic}))
			self.finish()
		else:
			if type == "dht22":
				rs.set_dht22s(dic["data"])
				self.write(json.dumps({'status': 'ok', 'sent': dic}))
				self.finish()
			else:
				if type == "Miner":
					rs.set_miners(dic["data"])
					self.write(json.dumps({'status': 'ok', 'sent': dic}))
					self.finish()



class WebSocketHandler(tornado.websocket.WebSocketHandler):
	waiters = set()



	def get_current_values(self):
		states = {}
		relay_states = {}
		dht22_states = {}
		i = 0
		for relay in lstRelays:
			relay_states[i] = relay.value
			i += 1
		states['relays'] = relay_states

		rs = RepoSettings()
		dht22s = rs.get_dht22s()
		i = 0
		for dht22 in dht22s:
			th = get_cur_temp_and_hum(dht22[1])
			dht22_states[i] = th['humidity']
			i += 1
			dht22_states[i] = th['temperature']
			i += 1
		states['dht22s'] = dht22_states

		return json.dumps(states)

	def open(self):
		self.set_nodelay(True)
		print('Socket Connected: ' + str(self.request.remote_ip))
		repo = Repository.Repository()
		#		self.write_message(str(repo.get_current_count()))
		self.write_message(self.get_current_values())
		WebSocketHandler.waiters.add(self)

	def on_close(self):
		WebSocketHandler.waiters.remove(self)

	@classmethod
	def send_updates(cls):
		for waiter in cls.waiters:
			try:
				waiter.write_message(waiter.get_current_values())
				#waiter.write_message("updated")
			except:
				print("Error sending message")


	def on_message(self,message):
		dict_message = json.loads(message)
		if dict_message["Event"] == "RelayTrip":
			if dict_message["State"]:
				lstRelays[int(dict_message["Relay"])].on()
			else:
				lstRelays[int(dict_message["Relay"])].off()

		WebSocketHandler.send_updates()

class Application(tornado.web.Application):
	def __init__(self):
		handlers = [
			(r"/", MainHandler),
			(r'/static/(.*)', tornado.web.StaticFileHandler, {'path': '/var/www/lifceypi/static'}),
			(r"/(favicon\.ico)", tornado.web.StaticFileHandler, {'path': '/var/www/lifceypi/static'}),
			(r"/(apple-touch-icon\.png)", tornado.web.StaticFileHandler, {'path': '/var/www/lifceypi/static'}),
			(r"/(apple-touch-icon-precomposed\.png)", tornado.web.StaticFileHandler, {'path': '/var/www/lifceypi/static'}),
			(r"/websocket", WebSocketHandler),
			(r"/auth/login/", AuthLoginHandler),
			(r"/auth/logout/", AuthLogoutHandler),
			(r"/settings/", SettingsHandler),
		]
		settings = {
			"template_path":Settings.TEMPLATE_PATH,
			"static_path":Settings.STATIC_PATH,
			"debug":Settings.DEBUG,
			"cookie_secret": Settings.COOKIE_SECRET,
			"login_url": "/auth/login/"
		}
		tornado.web.Application.__init__(self, handlers, **settings)

def get_cur_temp_and_hum(sensor):
	# this connects to the pigpio daemon which must be started first
	retval = {'temperature': -999, 'humidity': -999}
	pi = pigpio.pi()
	# Pigpio DHT22 module should be in same folder as your program
	s = DHT22.sensor(pi, sensor)

	i = 0
	while ((i < 6) and (int(retval['temperature']) <= -999)):
		i += 1
		s.trigger()
		sleep(.05) # Necessary on faster Raspberry Pi's
		retval['humidity'] = round(s.humidity(), 1)
		retval['temperature'] = round(s.temperature(), 1)
		'''print("{} {} {:3.2f} {} {} {} {}".format(
			s.humidity(), s.temperature(), s.staleness(),
			s.bad_checksum(), s.short_message(), s.missing_message(),
			s.sensor_resets()))'''
	s.cancel()
	pi.stop()

	return retval


def InitialazeRelays():
	i = 0

	rs = RepoSettings()
	relays = rs.get_relays()
	for RelayPin in relays:
		relay  = gpiozero.OutputDevice(int(RelayPin[1]), active_high=False, initial_value=False)
		lstRelays.append(relay)
		# lstRelays[i].on()
		# time.sleep(0.2)
		i += 1

def UpdateDB():
	pass


def ComponentsMonitor():
		InitialazeRelays()
		while 1:
			UpdateDB();
			time.sleep(60)





"""	index = 20
	repo = Repository.Repository()
	index = int(repo.get_current_count())
	WebSocketHandler.send_updates(str(index))
	while 1:
		if button.pressed():
			index -= 1
			if index < 0:
				index = 20
			WebSocketHandler.send_updates(str(index))
			repo.set_count(index)
		time.sleep(0.05)
"""

if __name__ == "__main__":
	try:
		thread = threading.Thread(target=ComponentsMonitor)
		thread.daemon = True
		thread.start()

		tornado.options.parse_command_line()
		http_server = tornado.httpserver.HTTPServer(Application())
		http_server.listen(options.port)
		tornado.ioloop.IOLoop.instance().start()
	except KeyboardInterrupt:
		# turn the relay off
		for relay in lstRelays:
			relay.off()
		# exit the application
		sys.exit(0)
