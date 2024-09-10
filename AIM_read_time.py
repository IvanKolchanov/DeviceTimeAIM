import serial
import sys
import glob
import datetime
import time
import pytz
import winsound

def float_equal(a : float, b : float) -> bool:
    return abs(a - b) <= 0.00001

class Interval:
    """ Keeps track of the interval where the turnover point is

        target() gives calculate_sbs() targets to measure time between
        
        validate_target() gives calculate_sbs() targets to measure time between during validation
        
        next_check() updates the target, keeps track of validation
    """
    def __init__(self, min = 0.0, max = 1.0, mid = 0.5):
        self.min = min
        self.max = max
        self.mid = mid
        self.port = serial.Serial()

    def __str__(self):
        return "[" + str(self.min) + " " + str(self.max) + "]" + " - " + str(self.mid)
    
    def target(self) -> list[float]:
        return [self.min, self.mid]
    
    def validate_target(self) -> list[float]:
        return [self.mid, self.max]

    def next_check(self, first, second, is_inside : bool):
        print("Second increased: ", is_inside)
        if is_inside:
            self.max = self.mid
        else:
            self.port.close()
            print("VALIDATION reconnect device")
            input("Press enter after reconnection")
            self.port.open()
            if not calculate_sbs(self.port, self, False, True):
                print("Second increased: ", False)
                self.port.close()
                print("VALIDATION reconnect device")
                input("Press enter after reconnection")
                self.port.open()
                if not calculate_sbs(self.port, self, False, True):
                    raise RuntimeError
            print("Second increased: ", True)
            self.min = self.mid

        self.mid = (self.min + self.max) / 2.0
        return

def serial_ports() -> list[str]:
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

def check_available_port(port : str) -> bool:
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
    
def chose_port() -> str:
    """ Waits for user to enter a legit port or exit

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

def format_device_time(serial_string : str, curr_time : datetime) -> datetime:
    """ Format the device "r" read information to time that we can actually use

        :returns:
            A datetime object with device's current time
    """
    try:
        serial_string = serial_string.split("Device Time: ")[1]
        serial_string = serial_string.split("Last Write: ")[0]

        device_time = datetime.datetime.strptime(serial_string[:-2], '%Y-%m-%d %H:%M:%S')
        device_time = device_time.replace(tzinfo=curr_time.tzinfo)
        return device_time
    except:
        print("Failed read")
        print(serial_string)

def connect_port(port_chosen : str) -> list:
    """ Reads current time and device time, compares them and outputs difference

        :returns:
            [curr_time : datetime, device_time : datetime, difference : timedelta, read_latency : timedelta]
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

def sleep_until_datetime(wait_until : datetime):
    """ Sleeps until wait_until : datetime of actual time is reached

        :returns:
            Nothing
    """
    now = datetime.datetime.now(pytz.timezone('America/Chicago'))
    difference = wait_until - now
    time.sleep(difference.total_seconds())

def sleep_until_ms(until : float):
    """ Sleeps until a specified number of miliseconds of actual time is reached

        :returns:
            Nothing
    """
    now = datetime.datetime.now()
    now = (float)(now.microsecond) / 1000000.0
    if until > now: time.sleep(until - now)
    else: time.sleep(1 - now + until)

def calculate_turnover_point(port_chosen : str, sbs : Interval):
    serialPort = serial.Serial(
    port=port_chosen, baudrate=115200, bytesize=8, timeout=4, stopbits=serial.STOPBITS_ONE, write_timeout=2
    )
    sbs.port = serialPort
    result = 0
    for i in range(10):
        if i == 0:
            result = calculate_sbs(serialPort, sbs, True, False)
        else:
            result = calculate_sbs(serialPort, sbs, False, False)
        serialPort.close()
        print(result)
        print("Reconnect device")
        input("Press enter after reconnection")
        print()
        serialPort.open()

def calculate_sbs(serialPort : serial.Serial, sbs : Interval, first_read : bool, validate : bool) -> any:
    """ Calculates the current step of turnover or validates an interval

        :returns:
            Nothing in case of error or Interval object sbs
    """
    target = sbs.target()
    if validate: target = sbs.validate_target()

    if first_read: target[0] -= 0.05
    sleep_until_ms(target[0])

    read_request = str.encode('r')
    start_time = time.time()
    serialPort.write(read_request) # Set device in read mode
    curr_time1 = datetime.datetime.now(pytz.timezone('America/Chicago'))
    read_latency1 = time.time() - start_time
    
    input_chunk1 = serialPort.read(serialPort.in_waiting)
    time.sleep(0.01)
    while serialPort.in_waiting > 0:
        input_chunk1 += serialPort.read(serialPort.in_waiting)
        time.sleep(0.01)

    sleep_until_ms(target[1])
    
    start_time = time.time()
    serialPort.write(read_request) # Set device in read mode
    curr_time2 = datetime.datetime.now(pytz.timezone('America/Chicago'))
    read_latency2 = time.time() - start_time
    
    input_chunk2 = serialPort.read(serialPort.in_waiting)
    time.sleep(0.01)
    while serialPort.in_waiting > 0:
        input_chunk2 += serialPort.read(serialPort.in_waiting)
        time.sleep(0.01)

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

    print(first)
    print(second)
    if device_difference.seconds > 1:
        print("Took too long")
        return
    
    num1 = (float)(first[0].microsecond) / 1000000.0
    num2 = (float)(second[0].microsecond) / 1000000.0
    print(num1, num2)
    if validate: return device_difference.seconds == 1
    sbs.next_check(num1, num2, device_difference.seconds == 1)

    return sbs

def prepare_write_date_time() -> bytes:
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

def write_date_time(port_chosen : str):
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

def calculate_ppm(first: datetime, second: datetime, time_period: float) -> float:
    """ Calculates ppm from two time measurement of devices over the time_period

        :returns:
            ppm
    """
    time_difference = second - first
    ppm = (time_difference.total_seconds() / time_period) * 10**6
    return ppm

def calculate_register_from_ppm(ppm: float) -> list[int]:
    """ Calculates values of registers CALP and CALM

        :returns:
            [CALP, CALM]
    """
    maximum_increase = 488.5
    step_down_value = 0.9537
    CALM, CALP = 0, 0
    if (ppm > 0):
        CALM = round(ppm / step_down_value)
    else:
        CALP = 1
        if ppm + maximum_increase > 0:
            CALM = round((ppm + maximum_increase) / step_down_value)
    return [CALP, CALM]


def calibrate(port_chosen : str):
    """Steps to calibration:
        1. Set fresh time - 
        2. Scan accurate time right now - calibrate_sbs
        3. Wait N time, play a sound 30 seconds before end, sleep 30 more seconds
        4. Scan accurate time again - calibrate_sbs ✓✓✓
        5. Calculate the time difference over N - calculate_ppm ✓✓✓
        6. Get calibration value for the device - calculate_register_for_ppm ✓✓✓
    """
    N = 40
    #3
    #Sleep till time -30 seconds
    print(datetime.datetime.now(pytz.timezone('America/Chicago')))
    target = datetime.datetime.now(pytz.timezone('America/Chicago')) + datetime.timedelta(seconds=(N - 30))
    sleep_until_datetime(target)
    #Play a sound to call for attention
    winsound.PlaySound('C:\\Users\\kolch\\Documents\\DeviceTimeAIM\\notification.wav', winsound.SND_ASYNC)
    print(datetime.datetime.now(pytz.timezone('America/Chicago')))
    target = datetime.datetime.now(pytz.timezone('America/Chicago')) + datetime.timedelta(seconds=30)
    #Continue sleeping till full time
    sleep_until_datetime(target)
    print(datetime.datetime.now(pytz.timezone('America/Chicago')))
    return

if __name__ == '__main__':
    while 1:
        print("\nEnter number to perform operation or Ctrl+C to exit:")
        print("1. Read time from device")
        print("2. Set time to device")
        print("3. Find subseconds")
        print("4. Calibration (TODO)")
        option_chosen = (int)(input("Enter: "))

        if option_chosen == 1:
            port_chosen = chose_port()
            result = connect_port(port_chosen)
        if option_chosen == 2:
            port_chosen = chose_port()
            result = write_date_time(port_chosen)
        if option_chosen == 3:
            port_chosen = chose_port()
            result = Interval()
            calculate_turnover_point(port_chosen, result)
        if option_chosen == 4:
            port_chosen = chose_port()
            calibrate(port_chosen)
            