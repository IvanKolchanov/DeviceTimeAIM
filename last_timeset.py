import re
from datetime import datetime
from datetime import timedelta

def parse_time(time_str):
    try:
        return datetime.strptime(time_str, "%y-%m-%d %H:%M:%S")
    except ValueError:
        return None

def bigger_delta(a : datetime, b : datetime):
    delta = a - b
    return delta.total_seconds() > 3600 * 24

def process_file(file_path):
    connection_pattern = r"Computer connected at: (\d{2}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})"
    disconnection_pattern = r"Computer disconnected at: (\d{2}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})"
    
    last_connection_time = None
    last_valid_disconnection_time = None
    
    with open(file_path, 'r') as file:
        for line in file:
            # Search for connection times
            match_connect = re.search(connection_pattern, line)
            if match_connect:
                connection_time = parse_time(match_connect.group(1))
                if connection_time:
                    last_connection_time = connection_time
            
            # Search for disconnection times
            match_disconnect = re.search(disconnection_pattern, line)
            if match_disconnect:
                disconnection_time = parse_time(match_disconnect.group(1))
                if disconnection_time and last_connection_time and (disconnection_time < last_connection_time or bigger_delta(disconnection_time, last_connection_time)):
                    last_valid_disconnection_time = disconnection_time
    
    return last_valid_disconnection_time

def main():
    file_path = r"C:\Users\kolch\Documents\DeviceTimeAIM\AIM_LOG_2.txt"  # Change this to the path of your .txt file"
    last_disconnection_time = process_file(file_path)

    if last_disconnection_time:
        print("Last disconnection time earlier than a connection time:")
        print(last_disconnection_time.strftime("%y-%m-%d %H:%M:%S"))
    else:
        print("No valid disconnection times found.")

if __name__ == "__main__":
    main()