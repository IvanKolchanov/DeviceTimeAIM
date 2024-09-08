import serial
import sys
import glob
import datetime
import time
import pytz
import random

class Interval:
    def __init__(self, intervals = [[0.0, 0.999999]]):
        self.intervals = intervals

    def __str__(self):
        self.intervals.sort(key=lambda i: i[0])
        a = ""
        for i in self.intervals:
            a += i.__str__()
        return a

    def contains(self, interval1, interval2):
        if (interval2[0] >= interval1[0] and interval2[0] <= interval1[1]) and (interval2[1] >= interval1[0] and interval2[1] <= interval1[1]):
            return True
        return False
    
    def is_intersection(self, interval1, interval2):
        if (interval1[1] < interval2[0] or interval1[0] > interval2[1]):
            return False
        return True

    def intersection(self, interval):
        if not (interval[0] >= 0 and interval[1] <= 1) or not (interval[1] >= 0 and interval[1] <= 1):
            return -1
        
        things_to_append = []
        things_to_remove = []
        for i in self.intervals:
            if not self.is_intersection(i, interval):
                things_to_remove.append(i)
            elif self.contains(i, interval):
                things_to_remove.append(i)
                things_to_append.append(interval)
            elif self.is_intersection(i, interval):
                things_to_remove.append(i)
                i[0] = max(i[0], interval[0])
                i[1] = min(i[1], interval[1])
                things_to_append.append(i)

        for i in things_to_append:
            self.intervals.append(i)
        for i in things_to_remove:
            self.intervals.remove(i)

    def not_intersection(self, interval):
        if not (interval[0] >= 0 and interval[1] <= 1) or not (interval[1] >= 0 and interval[1] <= 1):
            return -1
        
        things_to_append = []
        things_to_remove = []
        for i in self.intervals:
            if self.contains(interval, i):
                things_to_remove.append(i)
            elif self.contains(i, interval):
                things_to_remove.append(i)
                things_to_append.append([i[0], interval[0]])
                things_to_append.append([interval[1], i[1]])
            elif self.is_intersection(i, interval):
                things_to_remove.append(i)
                if i[1] < interval[1]: i[1] = interval[0]
                else: i[0] = interval[1]
                things_to_append.append(i)

        for i in things_to_append:
            self.intervals.append(i)
        for i in things_to_remove:
            self.intervals.remove(i)

sbs = Interval()

def serial_ports():
    print("COM ports available:")
    """ Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        if check_available_port(port):
            result.append(port)
    return result

def check_available_port(port):
    """ Checks if the entered port is available

        :returns:
            True or False depending on the result
    """
    try:
        s = serial.Serial(port)
        s.close()
        return True
    except (OSError, serial.SerialException):
        return False
    
def chose_port():
    """ Wait for user to enter a legit port or exit

        :returns:
            A string with the chosen port
    """
    port_chosen = ""
    while port_chosen == "":
        print(serial_ports())
        port_chosen = (input("Enter the name of the port you want to read time from or press enter to scan again, enter \"Exit\" to exit\n"))
            
        if port_chosen == "Exit" or port_chosen == "exit": return
            
        if check_available_port(port_chosen):
                print("The port is available")
        else:
            print("The port is NOT available")
            port_chosen = ""
    return port_chosen

def format_device_time(serial_string, curr_time):
    serial_string = serial_string.split("Device Time: ")[1]
    serial_string = serial_string.split("Last Write: ")[0]

    device_time = datetime.datetime.strptime(serial_string[:-2], '%Y-%m-%d %H:%M:%S')
    device_time = device_time.replace(tzinfo=curr_time.tzinfo)
    return device_time

def connect_port(port_chosen):
    """ Reads current time and device time, compares them and outputs difference

        :returns:
            Nothing
    """
    serial_string = "" # Used to hold data coming over UART
    serialPort = serial.Serial(
    port=port_chosen, baudrate=115200, bytesize=8, timeout=4, stopbits=serial.STOPBITS_ONE
    )
    start_time = time.time()
    curr_time = datetime.datetime.now(pytz.timezone('America/Chicago'))
    serialPort.write(str.encode('r')) # Set device in read mode
    read_latency = time.time() - start_time
    print("It took: ", read_latency, "to read time from the device")
    
    input_chunk = serialPort.read(size=1024)
    serial_string += input_chunk.decode("Ascii")
    while len(input_chunk) > 0:
        try:
            serial_string += input_chunk.decode("Ascii")
            input_chunk = serialPort.read(size=1024)
        except:
            serialPort.close()
            return []
            
    
    if serial_string == "":
        print("Error in reading device info")
        print("Reading: \"", serial_string, "\"")
        return []
    
    serialPort.close()

    print("Actual time: ", curr_time)

    device_time = format_device_time(serial_string, curr_time)
    print("Device time: ", device_time)

    difference = curr_time - device_time
    if device_time > curr_time: difference = device_time - curr_time
    
    print("Difference: ", difference)
    return [curr_time, device_time, difference, read_latency]

def calculate_sbs(serialPort):
    start_time = time.time()
    curr_time1 = datetime.datetime.now(pytz.timezone('America/Chicago'))
    print("first write")
    serialPort.write(str.encode('r')) # Set device in read mode
    read_latency1 = time.time() - start_time
    
    input_chunk1 = serialPort.read(serialPort.in_waiting)
    print("before first read")
    time.sleep(0.01)
    while serialPort.in_waiting > 0 and time.time() - start_time < 1:
        input_chunk1 += serialPort.read(serialPort.in_waiting)
        time.sleep(0.01)
    #serial_string += input_chunk.decode("Ascii")
    #first = serial_string
    print("after first read")

    time.sleep(random.random())
    start_time = time.time()
    curr_time2 = datetime.datetime.now(pytz.timezone('America/Chicago'))
    serialPort.write(str.encode('r')) # Set device in read mode
    read_latency2 = time.time() - start_time
    
    print("before second read")
    input_chunk2 = serialPort.read(serialPort.in_waiting)
    time.sleep(0.01)
    while serialPort.in_waiting > 0 and time.time() - start_time < 1:
        input_chunk2 += serialPort.read(serialPort.in_waiting)
        time.sleep(0.01)
    print("after second read")

    #We can finaly decode and do stuff
    text1 = input_chunk1.decode("Ascii")
    device_time1 = format_device_time(text1, curr_time1)
    difference1 = curr_time1 - device_time1
    if device_time1 > curr_time1: difference1 = device_time1 - curr_time1
    first = [curr_time1, device_time1, difference1, read_latency1]
    
    text2 = input_chunk2.decode("Ascii")
    device_time2 = format_device_time(text2, curr_time2)
    difference2 = curr_time2 - device_time2
    if device_time2 > curr_time2: difference2 = device_time2 - curr_time2
    second = [curr_time2, device_time2, difference2, read_latency2]
    
    
    if len(first) == 0 or len(second) == 0:
        print("Reading fail")
        return
    
    device_difference = second[1] - first[1]
    print(device_difference)

    print(first)
    print(second)
    if device_difference.seconds > 1:
        print("Took too long")
        return
    
    interval = []
    num1 = (float)(first[0].microsecond) / 1000000.0
    num2 = (float)(second[0].microsecond) / 1000000.0
    print(num1, num2)
    difference_actual_seconds = second[0].second - first[0].second
    if difference_actual_seconds == 0:
        interval = [num1, num2]
    elif difference_actual_seconds > 0:
        interval = [[num1, 0.999999], [0.0, num2]]
    print(interval)

    if device_difference.seconds == 0:
        if type(interval[0]) == float:
            sbs.not_intersection(interval)
        else:
            sbs.not_intersection(interval[0])
            sbs.not_intersection(interval[1])
    else:
        if  type(interval[0]) == float:
            sbs.intersection(interval)
        else:
            sbs.not_intersection([interval[1][1], interval[0][0]])

    return sbs

def prepare_write_date_time():
    """ Prepares a string to set time to the device

        :returns:
            Prepared string
    """

    curr_time = datetime.datetime.now(pytz.timezone('America/Chicago'))
    time_info = (str)(curr_time.second)
    if (len(time_info) < 2): time_info = '0' + time_info
    write_info = 'gS' + time_info + ','

    time_info = (str)(curr_time.minute)
    if (len(time_info) < 2): time_info = '0' + time_info
    write_info += 'D' + time_info + ','

    time_info = (str)(curr_time.hour)
    if (len(time_info) < 2): time_info = '0' + time_info
    write_info += 'H' + time_info + ','

    time_info = (str)(curr_time.day)
    if (len(time_info) < 2): time_info = '0' + time_info
    write_info += 'T' + time_info + ','

    time_info = (str)(curr_time.month)
    if (len(time_info) < 2): time_info = '0' + time_info
    write_info += 'M' + time_info + ','

    write_info += 'J' + (str)(curr_time.year)[2:]
    write_info_bytes = write_info.encode("Ascii")
    return write_info_bytes

def write_date_time(port_chosen):
    """ Writes new date&time to the device

        :returns:
            Nothing
    """
    print("Preparing to write")
    serialPort = serial.Serial(port=port_chosen, baudrate=115200, bytesize=8, timeout=4, stopbits=serial.STOPBITS_ONE)
    start_time = time.time()
    write_info = prepare_write_date_time()
    serialPort.write(write_info)
    print("It took: ", time.time() - start_time, " to set time to the device")
    serialPort.close()
    time.sleep(1)
    
    connect_port(port_chosen)
    print("Finished writing: ", write_info)

if __name__ == '__main__':
    while 1:
        print("\nEnter number to perform operation or Ctrl+C to exit:")
        print("1. Read time from device")
        print("2. Set time to device")
        print("3. Find subseconds")
        option_chosen = (int)(input("Enter: "))

        if option_chosen == 1:
            port_chosen = chose_port()
            result = connect_port(port_chosen)
        if option_chosen == 2:
            port_chosen = chose_port()
            result = write_date_time(port_chosen)
        if option_chosen == 3:
            port_chosen = chose_port()
            serialPort = serial.Serial(
            port=port_chosen, baudrate=115200, bytesize=8, timeout=4, stopbits=serial.STOPBITS_ONE, write_timeout=2
            )
            for i in range(10):
                result = calculate_sbs(serialPort)
                print(result)
                serialPort.close()
                print("reconnect device")
                input("Press enter after reconnection")
                serialPort.open()
                
            serialPort.close()
            print("\n\n")
            print(sbs)
            