import RPi.GPIO as GPIO
import time
import multiprocessing
import logging
import pickle
from datetime import datetime, timedelta
import os


# Light hours on/off in hours
l_on = 18
l_off = 6
# Reset cycle - set True if you are changing light cycles.
reset_mem = False
# set True to cycle fan False for fan always on
fan_cycle_on = False
# Fan cycle on/off seconds
f_on = 420
f_off = 60
# Set to False if you don't want to pause lights for 1st run.
pause_light = False


# Not advised to edit anything below this point.
start_time = time.time()
soc_12v = {'fill': 12, 'drain': 16}
soc_240v = {'fan': 20, 'light': 6}
# Set water date and time list [day-month-year-hour-min,19-10-2018-18-40]
water_cycles = ['21-10-2018-16-55', '21-10-2018-17-00', '21-10-2018-17-05', '21-10-2018-17-10', '21-10-2018-17-15',
                '21-10-2018-17-20', '21-10-2018-17-25', '21-10-2018-17-30', '21-10-2018-17-35', '21-10-2018-17-40',
                '21-10-2018-17-45', '21-10-2018-17-50', '21-10-2018-17-55', '21-10-2018-18-00']
# Fill from mains sec/Water plants sec
fill = 10
drain = 203
logging.basicConfig(filename='/home/mrks/fibg/log/run.log', level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(name)s %(message)s')
loc = '/home/mrks/fibg/bin/memory'


# Startup


def startup(soc_lst):
    for soc in soc_lst:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(soc, GPIO.OUT)
        GPIO.output(soc, GPIO.HIGH)
        GPIO.cleanup()
        logging.info('GPIO' + str(soc) + ':Configured')


# Relay switches


def fan_on():
    soc = soc_240v['fan']
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(soc, GPIO.OUT)
    GPIO.output(soc, GPIO.HIGH)
    logging.info('GPIO' + str(soc) + ':Extractor fan on')
    return 'on'


def fan_off():
    soc = soc_240v['fan']
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(soc, GPIO.OUT)
    GPIO.output(soc, GPIO.LOW)
    logging.info('GPIO' + str(soc) + ':Extractor fan off')
    return 'off'


def light_on():
    soc = soc_240v['light']
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(soc, GPIO.OUT)
    GPIO.output(soc, GPIO.HIGH)
    logging.info('GPIO' + str(soc) + ':Grow light on')
    return 'on'


def light_off():
    soc = soc_240v['light']
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(soc, GPIO.OUT)
    GPIO.output(soc, GPIO.LOW)
    logging.info('GPIO' + str(soc) + ':Grow light off')
    return 'off'


# Cycles #


def light_cycle(on, off):
    dtn = datetime.now()
    if pause_light is not False:
        loop = 'light_pause'
        logging.info('Pausing light cycle for ' + str(pause_light) + 'sec')
        start_light_cycle = dtn + timedelta(seconds=pause_light)
        mem = memory_r()[loop]
        if mem is None:
            memory_w(loop, start_light_cycle)
            mem = start_light_cycle
        elif dtn > mem:
            memory_w(loop, start_light_cycle)
            mem = start_light_cycle
        toggle = True
        while toggle is True:
            dtn_live = datetime.now()
            if dtn_live >= mem:
                toggle = False
            time.sleep(1)
        update_var('pause_light = ' + str(pause_light), 'pause_light = ' + str(False))
    mem = memory_r()['light']
    dtn = datetime.now()
    if reset_mem:
        update_var('reset_mem = ' + str(True), 'reset_mem = ' + str(False))
        off_time = dtn + timedelta(hours=on)
        end_time = off_time + timedelta(hours=off)
        dat = {'lon': dtn, 'lof': off_time, 'le': end_time}
        memory_w('light', dat)
        logging.info('Light cycle memory reset')
        logging.info('light cycle: on: ' + str(dtn) + ' off: ' + str(off_time) + ' end: ' + str(end_time))
    elif mem is None:
        off_time = dtn + timedelta(hours=on)
        end_time = off_time + timedelta(hours=off)
        dat = {'lon': dtn, 'lof': off_time, 'le': end_time}
        memory_w('light', dat)
        logging.info('light cycle: on: ' + str(dtn) + ' off: ' + str(off_time) + ' end: ' + str(end_time))
    elif dtn > mem['le']:
        off_time = dtn + timedelta(hours=on)
        end_time = off_time + timedelta(hours=off)
        dat = {'lon': dtn, 'lof': off_time, 'le': end_time}
        memory_w('light', dat)
        logging.info('light cycle: on: ' + str(dtn) + ' off: ' + str(off_time) + ' end: ' + str(end_time))
    else:
        off_time = mem['lof']
        end_time = mem['le']
        logging.info('light cycle: on: ' + str(mem['lon']) + ' off: ' + str(off_time) +
                     ' end: ' + str(end_time) + '  | pipe broken')
    s = 'off'
    while True:
        dtn_live = datetime.now()
        if dtn_live >= end_time:
            light_cycle(on, off)
        elif s in 'off':
            if dtn_live < off_time:
                s = light_on()
            else:
                continue
        elif s in 'on':
            if dtn_live < off_time:
                continue
            else:
                s = light_off()
        time.sleep(1)


def fan_cycle(on, off):
    s = 'off'
    if fan_cycle_on:
        logging.info('Fan cycle enabled.')
    while True:
        if fan_cycle_on:
            if s is 'off':
                s = fan_on()
                time.sleep(on)
            else:
                s = fan_off()
                time.sleep(off)
        else:
            if s is 'off':
                s = fan_on()
            else:
                continue
            time.sleep(3200)


def water_cycle(cycle_f, cycle_d):
    val_f = cycle_f - 5
    val_d = cycle_d - 5
    soc_d = soc_12v['drain']
    soc_f = soc_12v['fill']
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(soc_f, GPIO.OUT)
    GPIO.setup(soc_d, GPIO.OUT)
    GPIO.output(soc_f, GPIO.LOW)
    logging.info('GPIO' + str(soc_f) + ':Mains valve open')
    time.sleep(val_f)
    GPIO.output(soc_d, GPIO.LOW)
    logging.info('GPIO' + str(soc_d) + ':Dripper valve open')
    time.sleep(5)
    GPIO.output(soc_f, GPIO.HIGH)
    logging.info('GPIO' + str(soc_f) + ':Mains valve closed')
    time.sleep(val_d)
    GPIO.output(soc_d, GPIO.HIGH)
    logging.info('GPIO' + str(soc_d) + ':Dripper valve closed')
    GPIO.cleanup()


def memory_r():
        outfile = open(loc, 'rb')
        dat = pickle.load(outfile)
        outfile.close()
        return dat


def memory_w(loop, a):
    base_dict = memory_r()
    base_dict[loop] = a
    infile = open(loc, 'wb')
    pickle.dump(base_dict, infile)
    infile.close()


def mem_set():
    if os.path.isfile(loc) is False:
        a = {'light': None, 'light_pause': None}
        infile = open(loc, 'wb+')
        pickle.dump(a, infile)
        infile.close()


def update_var(var, new_var):
    loc_var = '/home/mrks/fibg/fibg.py'
    with open(loc_var, "r") as f:
        read_data = f.read()
        line = read_data.replace(var, new_var)
        f.close()
    with open(loc_var, "w") as f:
        f.write(line)
        f.close()
    logging.info('Set ' + var + ' to ' + new_var)


def main_loop(first_run):
    running_loops = {}
    while True:
        if first_run is True:
            mem_set()
            #startup(soc_12v.values())
            fan_loop = multiprocessing.Process(target=fan_cycle, args=[f_on, f_off])
            fan_loop.daemon = True
            fan_loop.start()
            running_loops.update({'fan': fan_loop.pid})
            light_l = multiprocessing.Process(target=light_cycle, args=[l_on, l_off])
            light_l.daemon = True
            light_l.start()
            running_loops.update({'light': light_l.pid})
        if time.strftime("%d-%m-%Y-%H-%M") in water_cycles:
            water_subp = multiprocessing.Process(target=water_cycle, args=[fill, drain])
            water_subp.daemon = True
            water_subp.start()
            running_loops.update({'water': water_subp.pid})
            # Here so that it doesnt loop in the min - will loop on otherwise
        first_run = False
        time.sleep(60)


if __name__ == '__main__':
    logging.info('Starting FIBG')
    print('Starting in:\n1')
    time.sleep(1)
    print('2')
    time.sleep(1)
    print('3')
    time.sleep(1)
    print('4')
    time.sleep(1)
    print('5\nKGO!')
    main_loop(True)
