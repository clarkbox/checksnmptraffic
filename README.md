<h1>check snmp traffic total</h1>

This is a nagios plugin to check the total amount of traffic passing over an interface within a defined time period. It can also be used stand alone as CLI tool. Run the script with --help for the full list of options.<br>
<br>
The script will exit code > 0 if the threshold of in/out is exceeded within the time period. A summary is also printed. This script does not need to be run via Nagios, and could be used stand alone, or invoked via cron.

I have used this script in production since 2010 and its been solid. Please provide feedback/bug reports. I will maintain this script, and expand it based on input from users. This project was moved from google code (http://code.google.com/p/checksnmptraffic/).

Send all commercial use bitcoin donations to: 1H6vCrypVRySXyovxWAcAUMEJV2Y7Rdh5B

##Help
<pre>
#./check_snmp_traffic --help
usage: check_snmp_traffic [options]

options:
  -h, --help            show this help message and exit
  --host=HOST           host to check.
  --period=PERIOD       timeframe (in seconds) for traffic threshold to occur
                        within. eg 3600 to reset the counter every hour.
  --warnIn=WARNIN       incoming traffic MAX in Mb to cause return warn
  --warnOut=WARNOUT     outgoing traffic MAX in Mb to cause return warn
  --critIn=CRITIN       incoming traffuc MAX in Mb to cause return crit
  --critOut=CRITOUT     outgoing traffuc MAX in Mb to cause return crit
  --checkOnly           specify this option for read only access to database.
  --dir=DIR             directory to store persistance file. reccomend storing
                        in tmp. do not add trailing slash
  --community=COMMUNITY
                        SNMP Community. usually public.
  --currentLtLast=CURRENTLTLAST
                        warn or crit - if current traffic is less than last
                        recorder, usually indicates that host was reset.
  --emptyDb=EMPTYDB     warn or crit - if the database does not contain this
                        host. might indicate this server nagios runs on was
                        reset.
  --snmpCommand=SNMPCOMMAND
                        SNMP Command to use - snmpget or snmpwalk. snmpget by
                        default
  --snmpIn=SNMPIN       SNMP MIB for intrafce IN counter
  --snmpOut=SNMPOUT     SNMP MIB for intrafce OUT counter
  --if-number=IFNUMBER  the interface for the host. this is used only to
                        differentiate data between multiple interfaces on a
                        single host.
}}}
</pre>

##Requirements:
snmpwalk (yum install net-snmp-utils)

