

def get_features(email_id):
    e = all_emails[email_id]
    features = []
    #features.append(last_sent_time[email_id])
    if e['sender'] in sender_avg_rt:
        features.append(sender_avg_rt[e['sender']])
    else:
        features.append(overall_avg)
    t = time.localtime(e['date'])
    features.append(t.tm_hour)
    features.append(t.tm_wday)
    features.append(len(e['cc']))
    return features