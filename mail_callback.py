from mailbot import register, Callback

class MyCallback(Callback):
	rules = {'subject': [r'Hello (\w)']}

	def trigger(self):
		#dosomething



register(MyCallback)
