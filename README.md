# fibg
Script to automate water/appliances cycle's with the RaspberryPi.

# Hardware
Tested with the Pi Model 3 B+ and Pi Zero.
I'm usin 240v 10amp relays and switchin GPIO pins from HIGH to LOW.
Unfortunatly I purchase 2 differant modles and one requires a HIGH input for on and the other a LOW.
Adjust depending on your relay boards.
I may make a tutorial on the hardware later.

# Requirments
* RPi
* pickle
* python3

# How to install
* Clone whole repository.

# How to configure
* Set up the script confuration at the top of the file fibgg.py
* Liht cycle on/off, set in increments of hours
l_on = 1

l_off = 1
* There is a memory file using Pickle and so if the unit reboots or the script is reset to adjust light cycles, set to True
reset_mem = False
* If you would like to cycle your fan, set to True
fan_cycle_on = False
* Fan cycle on/off seconds (only of fann_cycle_on is True)
f_on = 420

f_off = 60
* Set to False if you don't want to pause lights for 1st run.
pause_light = False
* Socket lists set as you like in relation to your GPIO usage, use BCM pin numbers.
soc_12v = {'fill': 12, 'drain': 16}

soc_240v = {'fan': 20, 'light': 6}
* Set water date and time list [day-month-year-hour-min,19-10-2018-18-40]
water_cycles = []
* Fill from mains sec/Water plants sec
fill = 10

drain = 203
