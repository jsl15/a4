from mailbot import MailBot, register, Callback
import getpass, imaplib, email.message, time, re
from sklearn.externals import joblib
import csv

imap_server = 'imap.gmail.com'
imap_user = 'jessicasliang@gmail.com'
imap_password = getpass.getpass()
conn = imaplib.IMAP4_SSL(imap_server)
(retcode, capabilities) = conn.login(imap_user, imap_password)

regr = joblib.load('email_response.pkl')

f = open('sender_avg_rt.tsv')
reader = csv.DictReader(f, delimiter='\t')
sender_avg_rt = {}
count = {}
for row in reader:
    sender_avg_rt[row['sender']] = float(row['avg'])
    count[row['sender']] = int(row['count'])
f.close()

overall_avg = 139763.467532

def parse_address(email_address):
    p = re.compile('\<.*>')
    matches = p.findall(email_address)
    if len(matches) == 0:
        email = email_address
    else: 
        email = matches[0]
        email = email.replace("<", "")
        email = email.replace(">", "")
    return email.lower()

def get_features(message):
    features = []
    sender = parse_address(message['From'])
    if sender_avg_rt[sender] > 0:
        features.append(sender_avg_rt[sender])
    else:
        features.append(overall_avg)
    t = time.localtime(time.mktime(email.utils.parsedate(message['Date'])))
    features.append(t.tm_hour)
    features.append(t.tm_wday)
    if message['cc'] == None:
        features.append(0)
    else:
        features.append(len(message['cc'].split(",")))
    return features

def get_prediction(email):
    features = get_features(email)
    prediction = regr.predict(features)
    print prediction
    hours = prediction/60/60
    if hours < 2:
        return "NOREPLY"
    
    if hours > 24:
        days = hours/24
        if days > 7:
            return "NOREPLY"
        if int(days) == 1:
            return "1 day"
        return str(int(days)) + " days"
    return str(int(hours)) + " hours"

class MyCallback(Callback):
    rules = {'To': [r'jessicasliang@gmail.com|jessica_liang@brown.edu']}
    def should_reject_email(self):
        sender = parse_address(self.message['From'])
        if sender == 'jessica_liang@brown.edu':
            return True
        if sender in count and sender in sender_avg_rt:
            if count[sender] > 4 and sender_avg_rt[sender] < 0:
                print "count rejected"
                return True
        elif len(self.message['To'].split(",")) > 3:
            print "to rejected"
            return True
        return False

    def send_prediction(self):
        prediction = get_prediction(self.message)
        print prediction
        if prediction == 'NOREPLY':
            return
        new_message = email.message.Message()
        new_message['Subject'] = "[AUTO-REPLY] Re: " + self.message['subject']
        new_message['From'] = 'jessicasliang@gmail.com'
        new_message['To'] = self.message['From']
        new_message['In-Reply-To'] = self.message['Message-ID']
        body = 'Hi thanks for emailing Jessica!\n\n'
        body += 'Jessica is a little busy right now so expect a response in ' + prediction + "."
        body += " She appreciates your patience!"
        body += "\n\nLove,"
        body += '\nJessica\'s Mailbot'
        new_message.set_payload(body)

        conn.append('[Gmail]/Drafts', '', imaplib.Time2Internaldate(time.time()), str(new_message))
    
    def draft_response(self):
        mail_body = self.get_email_body()
        sections = mail_body.split("\n\r")
        last_line = sections[-1]
        words = last_line.split(" ")
        sender = "" 
        # if the last line is one word, then assume its a name (hopefully)
        if len(words) == 1 and len(sections) > 1:
            sender = words[0]
            sender = sender.replace('\t', '').replace('\r\n', '').replace('\n', '')
        print sender
        new_message = email.message.Message()
        new_message['Subject'] = "Re: " + self.message['subject']
        new_message['From'] = 'jessicasliang@gmail.com'
        new_message['To'] = self.message['From']
        new_message['In-Reply-To'] = self.message['Message-ID']
        body = ""
        # if we found a sender then add a greeting
        if sender != "":
            body += "Hi " + sender +"!\n\n"
        questions = mail_body.split("?")
        questions = questions[:len(questions)-1]
        questions = map(lambda x: re.split(r'[.!]', x), questions)
        questions = filter(lambda x: len(x) > 0, questions)
        questions = map(lambda x: x[-1], questions)
        if len(questions) == 0:
        	return
        for q in questions:
            body += q+ "?" 
            body += "\n\n"
            print q
        # sign off
        body += "\n\n\n"
        body += "-Jessica"
        print body
        new_message.set_payload(body)

        conn.append('[Gmail]/Drafts', '', imaplib.Time2Internaldate(time.time()), str(new_message))

            

   
    def trigger(self):
        print self.message['Subject']
        if self.should_reject_email():
            print "REJECTED"
            return
        self.send_prediction()
        self.draft_response()


register(MyCallback)

mailbot = MailBot(imap_server, imap_user, imap_password, port=993, ssl=True)
try:
    mailbot.process_messages()
finally:
    try:
        conn.close()
    except:
        pass
    conn.logout()
print "done"


