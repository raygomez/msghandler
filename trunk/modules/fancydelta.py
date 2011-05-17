import datetime

class FancyDateTimeDelta(object):
    """
    Format the date / time difference between the supplied date and
    the current time using approximate measurement boundaries
    """

    def __init__(self, dt):
        now = datetime.datetime.now()
        delta = now - dt
	self.date = dt
	self.year = delta.days / 365
	self.day = delta.days
        self.hour = delta.seconds / 3600
        self.minute = delta.seconds / 60 - (60 * self.hour)
	self.second = delta.seconds

    def format(self):
	if self.year != 0: return self.date.strftime('%b/%d/%G')
	else:
	    if self.day != 0: 
	        return self.date.strftime('%b %d')	
	    else:
		if self.hour > 1:
		    return '%d hours ago' % self.hour
		elif self.hour == 1:
		    return 'an hour ago'
		else:
		    if self.minute > 1:
		    	return '%d minutes ago' % self.minute
		    if self.minute == 1:
		    	return 'a minute ago'
		    else: return 'a few seconds ago'
