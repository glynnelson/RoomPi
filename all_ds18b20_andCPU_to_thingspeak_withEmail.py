#!/usr/bin/env python
__author__ = 'glyn nelson'
# This program logs a Raspberry Pi's CPU temperature to a Thingspeak Channel
# To use, get a Thingspeak.com account, set up a channel, and capture the Channel Key at https://thingspeak.com/docs/tutorials/ 
# Then paste your channel ID in the code for the value of "key" below.
# Then run as sudo (access to the CPU temp requires sudo access)
# Had help for stripping the unwanted lines and text in a simpler way from: 
# www.reuk.co.uk/wordpress/raspebrry-pi/ds18b20-temperature-sensor-with-raspberry-pi

# Nov 2018.  Added an email alert to the facility account if room temp exceeds MaxT
# currently set at 26oC.  Will only email once every 24 h.

# Channel on nclbioimaging for thingspeak
# 
# publicly published to www.thingspeak.com/channels/310174
# 
# Added bioimaging API thingspeak channel

import os
import httplib, urllib
import time, datetime


#Libraries needed for email
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText

StartTime = datetime.datetime.now() # this is used to count the time since the email was sent

#make the email bit a definition and call it in the temp bit
def SpitEmail ():
	global StartTime
#variables for email settings:
	fromaddr = "yourEmail@domain.ac.uk" # change to the person it is being sent from
	toaddr = "yourEmail@domain.ac.uk" # change to the person it is being sent to (can be yourself)
	msg = MIMEMultipart()
	msg['From'] = fromaddr
	msg['To'] = toaddr
	msg['Subject'] = "Central SP8 STED Room Temp Alert!" # change to the message title for the room your Pi is in
 
	body = "The Room Temperature for the SP8 STED confocal at Central is too high.  Check the temps at https://thingspeak.com/channels/310174" # this should be changed to whatever you want to say in the email- this example gives the link to the thingspeak channel being reported.

	msg.attach(MIMEText(body, 'plain')) 

	HOST = "smtpauth.ncl.ac.uk" # set to match you email account settings
	PORT = "465" # set to match you email account settings
	SERVER = smtplib.SMTP_SSL() # set to match you email account settings
	SERVER.connect(HOST, PORT) # set to match you email account settings
	#SERVER.starttls() #all internet searches suggested this was the right encryption method, but found that SSL is what is required
	USER = "user" # set to match you email account settings
	PASSWD = "password" # set to match you email account settings.  If concerned about having this here, point instead to an encrypted file (google password from file linux to find multiple examples)
	SERVER.login(USER, PASSWD) # setup to match you email account settings

	text = msg.as_string()
	SERVER.sendmail(fromaddr, toaddr, text)
	SERVER.quit()
	


sleep = 120 # how many seconds to sleep between posts to the channel
key = '8RFCPCBQJ26L6UK'  # Thingspeak channel to update- API write key from ThingSpeak

TempAtTminus2 = 0
TempAtTminus1 = 0
TempNow = 0
EndTime = StartTime + datetime.timedelta(minutes = -3)

#print("start time set as ", StartTime)
#print ("endtime set as", EndTime)

#Get clean temp data from probes:
def thermometer():
	global TempAtTminus2 
	global TempAtTminus1
	global TempNow
	global StartTime
	global EndTime
	MaxT = 26  #this is the maximum room temp triggering an email (in oC)
	TimeBetweenEmails = 1439 #set in minutes- 1439 is 23h59 mins.
	
	while True:
		tempfile = open ("/sys/bus/w1/devices/28-0000070fb272/w1_slave") #this is the probe ID file path for the room temp probe
		input = tempfile.read()
		tempfile.close()
#probe gives 2 lines output, with temp at end of second line as t=xxxxx
		tempdata = input.split("\n")[1].split(" ")[9]
#this gets the second line, splits it by the spaces and takes the 10th element (which is t=xxxxx)
		temperature = float (tempdata[2:])
#this takes that value, changes it to a string and removes the first two chars (t=)
		temperature = temperature / 1000
#gives temp in degrees C

#now check last three temps are below 25, and if all too high, email
		TempNow = temperature
#		print("tempnow_beforeIF", TempNow)
#		print("minus2_preIF", TempAtTminus2)
#		print("minus1_preIF", TempAtTminus1)
		if TempNow > MaxT and TempAtTminus1 > MaxT and TempAtTminus2 > MaxT:
			if datetime.datetime.now() > EndTime:
				SpitEmail()
				EndTime = datetime.datetime.now() + datetime.timedelta(minutes = TimeBetweenEmails)
				StartTime = datetime.datetime.now()
#				print ("email fired at ", StartTime)
#				print("Start time now set as ", StartTime)
#				print("End time now set as ", EndTime)
#			print("oh my gawd, we're all gonna die!")
#now move all temp readings back one place
		TempAtTminus2 = TempAtTminus1
		TempAtTminus1 = TempNow
		TempNow = 0
		print("minus2", TempAtTminus2)
		print("minus1", TempAtTminus1)
		print("tempnow", TempNow)

		tempfile2 = open ("/sys/bus/w1/devices/28-0000070feeaa/w1_slave")  #this is the probe ID file path for the incubator temp probe
		input2 = tempfile2.read()
		tempfile2.close()
		tempdata2 = input2.split("\n")[1].split(" ")[9]
		temperature2 = float (tempdata2[2:])
		temperature2 = temperature2 / 1000

#Report Raspberry Pi internal temperature to Thingspeak Channel
		CPUtemp = int(open('/sys/class/thermal/thermal_zone0/temp').read()) / 1e3 # Get Raspberry Pi CPU
	        params = urllib.urlencode({'field1': temperature,'field2': temperature2,'field3': CPUtemp,'key':key })  #the fields refer to the fields in the channel on ThingSpeak, ensure you note which is which (temperature is room, temperature2 is incubator)
	        headers = {"Content-typZZe": "application/x-www-form-urlencoded","Accept": "text/plain"}
	        conn = httplib.HTTPConnection("api.thingspeak.com:80")
	        try:
	            conn.request("POST", "/update", params, headers)
	            response = conn.getresponse()
#	            print temperature
#	            print temperature2
#	            print CPUtemp
	            print response.status, response.reason
	            data = response.read()
	            conn.close()
	        except:
	            print "connection failed"
		break
#sleep for desired amount of time
if __name__ == "__main__":
        while True:
                thermometer()
                time.sleep(sleep)
