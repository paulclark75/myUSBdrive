# Python Code to Change Brightness of LED

import RPi.GPIO as GPIO     # Importing RPi library to use the GPIO pins
from time import sleep  # Importing sleep from time library
led_pin = 21            # Initializing the GPIO pin 21 for LED
GPIO.setmode(GPIO.BCM)          # We are using the BCM pin numbering
GPIO.setup(led_pin, GPIO.OUT)   # Declaring pin 21 as output pin
pwm = GPIO.PWM(led_pin, 1)    # Created a PWM object, frequency = 1Hz
pwm.start(10)                    # Started PWM at 10% duty cycle
try:
    while 1:                    # Loop will run forever
        for x in range(100):    # This Loop will run 100 times
            pwm.ChangeDutyCycle(x) # Change duty cycle
            sleep(0.01)         # Delay of 10mS
            
        for x in range(100,0,-1): # Loop will run 100 times; 100 to 0
            pwm.ChangeDutyCycle(x)
            sleep(0.01)
# If keyboard Interrupt (CTRL-C) is pressed
except KeyboardInterrupt:
    pass        # Go to next line
pwm.stop()      # Stop the PWM
GPIO.cleanup()  # Make all the output pins LOW

# Don't try to run this as a script or it will all be over very quickly  
# it won't do any harm though.  
# these are all the elements you need to control PWM on 'normal' GPIO ports  
# with RPi.GPIO - requires RPi.GPIO 0.5.2a or higher  
  
import RPi.GPIO as GPIO # always needed with RPi.GPIO  
  
GPIO.setmode(GPIO.BCM)  # choose BCM or BOARD numbering schemes. I use BCM  
  
GPIO.setup(25, GPIO.OUT)# set GPIO 25 as an output. You can use any GPIO port  
  
p = GPIO.PWM(25, 50)    # create an object p for PWM on port 25 at 50 Hertz  
                        # you can have more than one of these, but they need  
                        # different names for each port   
                        # e.g. p1, p2, motor, servo1 etc.  
  
p.start(50)             # start the PWM on 50 percent duty cycle  
                        # duty cycle value can be 0.0 to 100.0%, floats are OK  
  
p.ChangeDutyCycle(90)   # change the duty cycle to 90%  
  
p.ChangeFrequency(100)  # change the frequency to 100 Hz (floats also work)  
                        # e.g. 100.5, 5.2  
  
p.stop()                # stop the PWM output  
  
GPIO.cleanup()          # when your program exits, tidy up after yourself  