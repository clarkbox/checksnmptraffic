#! /usr/bin/env python

import sys
import getopt
import optparse
import commands
import shelve
import os
import time
import datetime


log = True
snmp_ifout="1.3.6.1.2.1.31.1.1.1.6.2"
snmp_ifin="1.3.6.1.2.1.31.1.1.1.10.2"

def buildHostRecord(ifNumber, trafficIn, trafficOut, timeRecorded ):
	return {ifNumber:{"inCount":trafficIn, "outCount":trafficOut, "recorded": timeRecorded }}

def runSnmpCheck(snmpCommand, snmpIn, snmpOut, host, ifNumber, warnWhen, critWhen, dir, community, period, checkOnly):

	trafLastIn = 0
	trafLastOut = 0
	trafLastRecorded = 0
	timeDiffMin = 0
	dbFile = dir+"/nagiostraffic.db"
	status = {"warn":0, "crit":0, "message":""}
	returnCode = 0

	#open DB
	d = shelve.open(dbFile)
	#todo ensure DB was opened/writable

	#snmp command line
	cmdSnmpIn = snmpCommand+" -v2c -c "+ community +" "+ host +" "+ snmpIn
	cmdSnmpOut = snmpCommand+" -v2c -c "+ community +" "+ host +" "+ snmpOut

	#execure the command TODO thread these based on user parameter option
	(cInStatus,cInOutput) = commands.getstatusoutput(cmdSnmpIn)
	(cOutStatus,cOutOutput) = commands.getstatusoutput(cmdSnmpOut)

	#set the time the commands were completed
	now = time.mktime(datetime.datetime.now().timetuple())

	#get the CURRENT value of counter from output string
	trafCurrentIn = cInOutput[cInOutput.rfind(":")+1:].strip()
	trafCurrentOut = cOutOutput[cOutOutput.rfind(":")+1:].strip()

	#get last value if this host is in db. assume if there is host, there is data.
	if d.has_key(host):
		trafLastIn = d[host][ifNumber]["inCount"]
		trafLastOut = d[host][ifNumber]["outCount"]
		trafLastRecorded = d[host][ifNumber]["recorded"]

		if int(trafLastOut) > int(trafCurrentOut) or int(trafLastIn) > int(trafCurrentIn):
			#print "current less than last"
			if critWhen["currentLtLast"]:
				status["crit"] = status["crit"]+1
				status["message"] += "current value is less than last record. traffic counter has been reset and is at zero. "
			elif warnWhen["currentLtLast"]:
				status["warn"] = status["warn"]+1
				status["message"] += "current value is less than last record. traffic counter has been reset and is at zero. "

			if not checkOnly:
				d[host] = buildHostRecord(ifNumber, trafCurrentIn, trafCurrentOut, now )

		timeDiffSeconds = (int(now) - int(trafLastRecorded))
		timeDiffMin = timeDiffSeconds//60

		#print "timeDiffSeocns "+str(timeDiffSeconds)
		#print "period "+str(period)

		if not checkOnly:
			if(int(timeDiffSeconds) > int(period)):
				#update host if period has expired.
				d[host] = buildHostRecord(ifNumber, trafCurrentIn, trafCurrentOut, now )

	else:
		if critWhen["emptyDb"]:
			status["crit"] = status["crit"]+1
			status["message"] += " datbase did not contain host. traffic counter is at zero. "
		elif warnWhen["emptyDb"]:
			status["warn"] = status["warn"]+1
			status["message"] += " datbase did not contain host. traffic counter is at zero. "

		if checkOnly:
			print "could not check host. no host in database.\nremove checkOnly option to insert host, and begin tracking bandwidth. "
			sys.exit(3);
		else:
			#insert host regardless of period
			d[host] = buildHostRecord(ifNumber, trafCurrentIn, trafCurrentOut, now )

	trafInDiff = int(trafCurrentIn) - int(trafLastIn)
	trafInDiffMb = trafInDiff//1024//1024

	trafOutDiff = int(trafCurrentOut) - int(trafLastOut)
	trafOutDiffMb = trafOutDiff//1024//1024

	if int(trafInDiffMb) > critWhen["trafficInThreshold"]:
		status["crit"] = status["crit"]+1
		status["message"] += "INCOMING TRAFFIC OVERAGE. "
	elif int(trafInDiffMb) > warnWhen["trafficInThreshold"]:
		status["warn"] = status["warn"]+1
		status["message"] += "Warning: Incoming traffic about to exceed maximum. "

	if int(trafOutDiffMb) > int(critWhen["trafficOutThreshold"]):
		status["crit"] = status["crit"]+1
		status["message"] += "OUTGOING TRAFFIC OVERAGE."
	elif int(trafOutDiffMb) > warnWhen["trafficOutThreshold"]:
		status["warn"] = status["warn"]+1
		status["message"] += "Warning: Outgoing traffic about to exceed maximum. "

	if status["crit"] > 0:
		returnCode = 2
	elif status["warn"] > 0:
		returnCode = 1
	else:
		returnCode = 0
		status["message"] += "TRAFFIC OK "

	returnOutput = status["message"] + "- IN: "+ str(trafInDiffMb)+"MB / OUT: "+str(trafOutDiffMb)+"MB / duration: " +str(timeDiffMin)+"min. "

	print returnOutput
	sys.exit(returnCode)

def main():
	parser = optparse.OptionParser()
	parser.add_option("--host",dest="host",help="host to check.")
	parser.add_option("--period",type="int", dest="period",help="timeframe (in seconds) for traffic threshold to occur within. eg 3600 to reset the counter every hour.")
	parser.add_option("--warnIn",type="int",dest="warnIn",help="incoming traffic MAX in Mb to cause return warn")
	parser.add_option("--warnOut",type="int",dest="warnOut",help="outgoing traffic MAX in Mb to cause return warn")
	parser.add_option("--critIn",type="int",dest="critIn",help="incoming traffuc MAX in Mb to cause return crit")
	parser.add_option("--critOut",type="int",dest="critOut",help="outgoing traffuc MAX in Mb to cause return crit")

	#optional
	parser.add_option("--checkOnly",dest="checkOnly",help="specify this option for read only access to database.",action="store_true")
	parser.add_option("--dir",dest="dir",help="directory to store persistance file. reccomend storing in tmp. do not add trailing slash",default="/tmp")
	parser.add_option("--community",dest="community",help="SNMP Community. usually public.",default="public")
	parser.add_option("--currentLtLast",dest="currentLtLast",help="warn or crit - if current traffic is less than last recorder, usually indicates that host was reset.", default=False)
	parser.add_option("--emptyDb",dest="emptyDb",help="warn or crit - if the database does not contain this host. might indicate this server nagios runs on was reset.", default=False)
	parser.add_option("--snmpCommand",dest="snmpCommand",help="SNMP Command to use - snmpget or snmpwalk. snmpget by default", default="snmpget")
	parser.add_option("--snmpIn",dest="snmpIn",help="SNMP MIB for intrafce IN counter ", default=snmp_ifin)
	parser.add_option("--snmpOut",dest="snmpOut",help="SNMP MIB for intrafce OUT counter ", default=snmp_ifout)
	parser.add_option("--if-number",type="int",dest="ifNumber",help="the interface for the host. this is used only to differentiate data between multiple interfaces on a single host.", default=100)

	(options, args) = parser.parse_args(sys.argv[1:])

	critWhen = {"trafficOutThreshold":options.critOut, "trafficInThreshold" : options.critIn}
	warnWhen = {"trafficOutThreshold" : options.warnOut, "trafficInThreshold" : options.warnIn}

	warnWhen["currentLtLast"] = False
	critWhen["currentLtLast"] = False
	if(options.currentLtLast == "crit"):
		critWhen["currentLtLast"] = True
	elif(options.currentLtLast == "warn"):
		warmWhen["currentLtLast"] = True

	warnWhen["emptyDb"] = False
	critWhen["emptyDb"] = False
	if(options.emptyDb == "crit"):
		critWhen["emptyDb"] = True
	elif(options.emptyDb == "warn"):
		warmWhen["emptyDb"] = True

	#ensure commands were specified TODO

	#run the command
	commandsStatus = runSnmpCheck(options.snmpCommand, options.snmpIn, options.snmpOut, options.host, options.ifNumber, warnWhen, critWhen, options.dir, options.community, options.period, options.checkOnly)

if __name__ == "__main__":
	main()