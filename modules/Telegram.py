
import requests, json

class Telegram():

	def __init__(self,bot_id,chat_id=None):
		self._bot_id = bot_id
		self._chat_id = chat_id
		self._last_msg_about = {}
		with open("./msgs.json",'r') as fp:
			prior_msgs = fp.read()
			self._last_msg_about = json.loads(prior_msgs)

	def set_chat_id(self,chat_id):
		self._chat_id = chat_id

	def anti_spam(self,msg,topic):
		if(topic in self._last_msg_about and self._last_msg_about[topic] == msg):
			# print("preventing repeating myself about the same thing.")
			return False
		else:
			self._last_msg_about[topic] = msg
			js = json.dumps(self._last_msg_about)
			with open("./msgs.json",'w') as fp:
				fp.write(js)
		return True

	def text_message(self,msg,topic="general",msg_full=None):
		if(not self.anti_spam(msg,topic)):
			return False
		if(msg_full):
			msg = msg_full
		params = {"chat_id": self._chat_id, "text": msg}
		url = "https://api.telegram.org/bot" + self._bot_id + "/sendMessage"
		# try:
			# print("Calling url:" + url)
		resp = requests.get(url, params=params)
		content = resp.text
		js = json.loads(content)
		if(js):
			if(js['ok'] == True):
				return True
		else:
			print(resp)
			print("Telegram server response: " + resp.text)
		# except:
			# print("Something went wrong sending a telegram msg.")

