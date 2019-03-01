#!/usr/bin/env python3
# 
import os
import time
from time import sleep
import signal
import sys
import RPi.GPIO as GPIO
import commands
import subprocess
import requests


fanPin = 17 # The pin ID, edit here to change it
switchSensPin = 18
ledPin = 21
hostname = "https://google.com"
desiredTemp = 45 # The maximum temperature in Celsius after which we trigger the fan
fanSpeed=100
sum=0
pTemp=15
iTemp=0.4
counter=0
delay=2
MOUNT_DIR = "/media/USBdrive"
driveFound = False
driveMounted = False
driveId = "not found"

def is_service_running(name):
    with open(os.devnull, 'wb') as hide_output:
        exit_code = subprocess.Popen(['service', name, 'status'], stdout=hide_output, stderr=hide_output).wait()
        return exit_code == 0

def is_online():
	try:
		response = requests.get(hostname)
		#print (response)
		code = int(response.status_code)
		#print(code)
		if code ==200:
			#print hostname, "is up"
			return True
		else:
			#print hostname, "is down"
			return False
	except:
		return False

def blink(times):
	for x in range(times):
		ledON()
		sleep(0.05)
		ledOFF()
		sleep(0.3)
	sleep(1)
	return()

def heartbeat():
	pwm = GPIO.PWM(21,1000) #0.5 Hz i.e. every 2 secs
	pwm.start(0)
	pwm.ChangeDutyCycle(10)
	sleep(0.05)
	pwm.ChangeDutyCycle(0)
	sleep(0.2)

	for x in range(0,100,4): # This Loop will run 100 times
		pwm.ChangeDutyCycle(x) # Change duty cycle
		sleep(0.01)  # Delay of 10mS

	for x in range(100,0,-4): # Loop will run 100 times; 100 to 0
		pwm.ChangeDutyCycle(x)
		sleep(0.01)

	pwm.ChangeDutyCycle(0)
	sleep(1)
	return()

def run_command(command):
	ret_code, output = commands.getstatusoutput(command)
	if ret_code == 1:
		raise Exception("FAILED: %s" % command)
	return output.splitlines()

def uuid_from_line(line):
	start_str = "UUID=\""
	uuid_start = line.index(start_str) + len(start_str)
	uuid_end= line.index("\"",uuid_start+1)
	return line[uuid_start: uuid_end]

def Shutdown():
	fanOFF()
	ledOFF()
	print ("Stopping Samba")
	command="sudo service smbd stop"
	run_command(command)
	print ("Samba stopped. Unmounting USB drive")
	command="sudo umount /media/USBdrive"
	run_command(command)
	print ("USB drive unmounted. Waiting 5 seconds for drive to stop")
	blink(10) #blink(10) takes 3.5 seconds
	sleep(1.5)
	GPIO.cleanup()  # Make all the output pins LOW

	os.system("sudo shutdown -h now")
	sleep(100)

def getCPUtemperature():
	res = os.popen('vcgencmd measure_temp').readline()
	temp =(res.replace("temp=","").replace("'C\n",""))
	# print("temp is {0}".format(temp)) #Uncomment here for testing
	return temp

def fanOFF():
	myPWM.ChangeDutyCycle(0)   # switch fan off
	return()

def ledOFF():
	GPIO.output(ledPin,GPIO.LOW)
	# print ("LED off")
	return()

def ledON():
	GPIO.output(ledPin,GPIO.HIGH)
	# print ("LED on")
	return()

def handleFan():
	global fanSpeed,sum,delay
	delay -= 1
	if delay >1:
		#print ("Waiting ", delay)
		return()
	delay = 20
	actualTemp = float(getCPUtemperature())
	diff=actualTemp-desiredTemp
	sum=sum+diff
	pDiff=diff*pTemp
	iDiff=sum*iTemp
	fanSpeed=pDiff +iDiff
	if fanSpeed>100:
		fanSpeed=100
	if fanSpeed<15:
		fanSpeed=0
	if sum>100:
		sum=100
	if sum<-100:
		sum=-100
	# print("CPUTemp %4.2f TempDiff %4.2f pDiff %4.2f iDiff %4.2f fanSpeed %5d" % (actualTemp,diff,pDiff,iDiff,fanSpeed))
	myPWM.ChangeDutyCycle(fanSpeed)
	return()

def handleSwitch():
	# print (GPIO.input(switchSensPin)) 
	if GPIO.input(switchSensPin)==1:
		global counter 
		print ("Shutdown in ", 2-counter)
		counter += 1
		if counter > 2:
			ledOFF()
			print ("Shutdown()")
			sleep(1)
			Shutdown()
	else:
		counter=0
	return()

def testUsbInsert():
	global driveFound
	partitionsFile = open("/proc/partitions")
	lines = partitionsFile.readlines()[2:]#Skips the header lines
	for line in lines:
		words = [x.strip() for x in line.split()]
		minorNumber = int(words[1])
		deviceName = words[3]
		if minorNumber % 16 == 0:
			#print("device name: "),deviceName
			if deviceName.find("sd") == 0:
				global driveId
				driveId = deviceName
				print ("Found device /dev/%s" % driveId)
				driveFound = True
			else:
				driveFound = False
	return()

def autoMountUsb():
	global driveId
	output = run_command("sudo blkid | grep %s | grep -v boot" % driveId)
	#print(output)

	for usb_device in output:
		command = "sudo mount --uuid %s %s" % (uuid_from_line(usb_device), MOUNT_DIR)
		#print(command)
		run_command(command)
		break
	return()

def testUsbMount():
	global driveMounted
	path = "/sys/class/block/" + driveId
	if os.path.islink(path):
		if os.path.realpath(path).find("/usb") > 0:
			driveMounted=True
			print("USB drive mounted")
	return()

def setPin(mode): # A little redundant function but useful if you want to add logging
	GPIO.output(fanPin, mode)
	return()
try:
	GPIO.setwarnings(False)
	GPIO.setmode(GPIO.BCM)
	GPIO.setup(fanPin, GPIO.OUT)
	myPWM=GPIO.PWM(fanPin,50)
	myPWM.start(50)
	GPIO.setup(switchSensPin, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
	GPIO.setwarnings(False)
	#turn on LED
	GPIO.setup(ledPin,GPIO.OUT)

	fanOFF()
	print ("Running fan and shutdown script")
	samba_running = False
	avahi_running = False
	while True:
		handleFan()
		handleSwitch()
		samba_running = is_service_running('smbd')
		if not samba_running:
			print "Samba is not running. Blink 5"
			blink(5) #was blink(2) but this looks like the heartbeat

		avahi_running = is_service_running('avahi-daemon')
		if not avahi_running:
			print("Avahi is not running. Blink 3")
			blink(3)

		connected = is_online()
		if not connected:
			print hostname +" is NOT reachable. Blink 4"
			blink(4)
		#else:
			#print hostname +" is reachable"

		#print "Samba running = "+ str(samba_running)
		#print "Avahi running = " + str(avahi_running)
		#print "Connected = " + str(connected)

		if samba_running and avahi_running and connected and driveFound:
			if driveMounted:
				heartbeat()
			else:
				autoMountUsb() #Mounts the USB 
				testUsbMount() #Tests if the USB drive mounted OK, and sets driveMounted if mmounted OK
		else:
			if samba_running and avahi_running and connected:
				blink(1)
				testUsbInsert() #Tests if USB drive is insseted and sets driveFound to True
		sleep(1)
except KeyboardInterrupt: # trap a CTRL+C keyboard interrupt 
	fanOFF()
	GPIO.cleanup() # resets all GPIO ports used by this program
