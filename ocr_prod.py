from datetime import datetime
import time

# Username and Password for the Samba SMB share
username = 'your_samba_username'
password = 'your_samba_password'
server = 'your_home_assistant_server_ip'
samba_folder = '\\www\\espmeter\\'
samba_file_name = 'espmeter_raw.jpg'
samba_put_name = 'latest.jpg'

# Username and Password for MQTT broker
mqtt_user = 'username_for_mqtt'
mqtt_pass = 'password_for_mqtt'
mqtt_broker_ip = 'mqtt_broker_ip'
mqtt_broker_port = 1883

# Local data folder
local_folder = 'espmeter/data/'

# Define start and endpoint for rectangle covering the value to extract - Use setup_ocr_values to find these quickly
start_point = (275, 215)
end_point = (600, 310)

# Define contrast and brightness parameters
alpha = 1.0                             # Contrast
beta = 21                               # Brightness
kernel_size = (3, 3)		# Numpy kernel size

# Threshold for accepting OCR results (int 0-100):
THRESH = 85

def timestamp():
    return f'[{datetime.now().strftime("%y-%m-%d %H:%M:%S")}]'

print()
print()
print(f'███████╗███████╗██████╗ ███╗   ███╗███████╗████████╗███████╗██████╗') 
print(f'██╔════╝██╔════╝██╔══██╗████╗ ████║██╔════╝╚══██╔══╝██╔════╝██╔══██╗')
print(f'█████╗  ███████╗██████╔╝██╔████╔██║█████╗     ██║   █████╗  ██████╔╝')
print(f'██╔══╝  ╚════██║██╔═══╝ ██║╚██╔╝██║██╔══╝     ██║   ██╔══╝  ██╔══██╗')
print(f'███████╗███████║██║     ██║ ╚═╝ ██║███████╗   ██║   ███████╗██║  ██║')
print(f'╚══════╝╚══════╝╚═╝     ╚═╝     ╚═╝╚══════╝   ╚═╝   ╚══════╝╚═╝  ╚═╝')
print()
print()
print(f'{timestamp()} Loading libraries')
print(f'{timestamp()} If this is the first time running the script,')
print(f'{timestamp()} it may take a few minutes for the OCR model.')
print()

import easyocr
import cv2
import numpy as np
import smbclient
from smbclient import shutil as smb_shutil
import paho.mqtt.client as mqtt

print(f'{timestamp()} Libraries loaded')

kernel = np.ones(kernel_size, np.uint8) 

def get_local_file_name():
    return datetime.now().strftime('%d%m%y_%H%M') + ".jpg"

def smb_copy(username, password, server, samba_folder, samba_file_name, local_file_name, local_folder):

    smbclient.register_session(server, username=username, password=password)

    print(f'{timestamp()} Opening file at: {server}.')
    print(f'{timestamp()} Storing local copy as {local_file_name}.')

    smb_shutil.copyfile(
        rf"\\{server}{samba_folder}{samba_file_name}", f"{local_folder}raw/{local_file_name}",
        username=username, password=password
    )

    print(f'{timestamp()} File collected and stored locally.')
    print()
    
    return True

def smb_put(username, password, server, samba_folder, samba_file_name, local_file_name, local_folder):

    smbclient.register_session(server, username=username, password=password)

    print(rf'{timestamp()} Accessing file at: {local_folder}final/{local_file_name}.')
    print(rf'{timestamp()} Storing remote copy as \\{server}{samba_folder}{samba_file_name}.')

    smb_shutil.copyfile(
        rf'{local_folder}final/{local_file_name}", f"\\{server}{samba_folder}{samba_file_name}',
        username=username, password=password
    )

    print(f'{timestamp()} File succesfully stored on HA server.')
    print()
    
    return True
    
def get_OCR(local_folder, local_file_name):
    print(f'{timestamp()} Instancing EasyOCR Reader.')
    print()

    reader = easyocr.Reader(['en'], gpu=False, quantize=False, verbose=False)

    print(f'{timestamp()} Loading image.')

    image = cv2.imread(local_folder + "raw/" + local_file_name)

    print(f'{timestamp()} Image loaded succesfully.')

    roi = image[start_point[1]:end_point[1], start_point[0]:end_point[0]]

    adjusted = cv2.convertScaleAbs(roi, alpha=alpha, beta=beta)
    

    cv2.imwrite(local_folder + "final/" + local_file_name, adjusted)
    
    print(f'{timestamp()} Region of Interest generated, adjusted and saved.')

    print()
    try:
        print(f'{timestamp()} Running OCR on RoI.')
        result = reader.recognize(adjusted, allowlist='0123456789')
    except Exception as err:
        print(f'{timestamp()} A problem occurred: {err}.')
    try:
        int_res = int(result[0][1])
        conf = round(result[0][2]*100, 2)
        print(f'{timestamp()} Numeric result: {int_res}. Confidence score: {conf}%.')
    except Exception as err:
        print(f'{timestamp()} Unable to format:')
        print(err)
    print()
    print(f'{timestamp()} Raw values from OCR:')
    for res in result[0][1:]:
        print(f'{" "*25}{res}')
    print()
    
    with open(local_folder + 'data.csv', 'w') as file:
        file.write(f'{timestamp()},{int_res},{conf},{result[0][1]}\n')
        print(f'{timestamp()} Data written to csv.')
    print()       
    
    return int_res, conf, result[0][1]

def send_config(mqttc):
    mqttc.publish("homeassistant/sensor/espmeter/result/config", 
                    """{
                      "name":"ESPMeter Result",
                      "object_id":"espmeter_result",
                      "unit_of_measurement":"kWh",
                      "device_class":"energy",
                      "state_class":"total_increasing",
                      "state_topic": "homeassistant/sensor/espmeter/result"
                     }""", qos=1, retain=True)
    mqttc.publish("homeassistant/sensor/espmeter/result/status", 
                    """{
                      "name":"ESPMeter Status",
                      "object_id":"espmeter_status",
                      "device_class":"sensor",
                      "state_class":"measurement",
                      "state_topic": "homeassistant/sensor/espmeter/status"
                     }""", qos=1, retain=True)
    mqttc.publish("homeassistant/sensor/espmeter/confidence/config", 
                    """{
                      "name":"ESPMeter Confidence",
                      "object_id":"espmeter_confidence",
                      "unit_of_measurement":"%",
                      "state_topic": "homeassistant/sensor/espmeter/confidence"
                     }""", qos=1, retain=True)
    mqttc.publish("homeassistant/sensor/espmeter/raw/config", 
                    """{
                      "name":"espmeter raw value",
                      "object_id":"espmeter",
                      "unit_of_measurement":"kWh",
                      "device_class":"energy",
                      "state_class":"total_increasing",
                      "state_topic": "homeassistant/sensor/espmeter/raw"
                     }""", qos=1, retain=True)
    print(f"{timestamp()} Published HA Discovery message.")
    print()
    
    
def on_connect(client, userdata, flags, reason_code, properties):
    print(f"{timestamp()} Connected with result code {reason_code}.")
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("espmeter/#")
    client.subscribe("homeassistant/status")
    send_config(mqttc)                     
    print()
    

def on_message(client, userdata, msg):
    print(f'{timestamp()} {msg.topic} {str(msg.payload)[2:-1]}')
    if msg.topic == "homeassistant/status" and str(msg.payload)[2:-1] =="online":
        send_config(mqttc)
        
    if str(msg.payload)[2:-1] == 'Ready for OCR':
        im_load = False
        im_put = False
        try:
            local_file_name = get_local_file_name()
            im_load = smb_copy(username, password, server, samba_folder, samba_file_name, local_file_name, local_folder)
        except Exception as err:
            print(f'{timestamp()} A problem occurred: {err}.')
            pass
        
        if im_load:
            int_res, conf, raw = get_OCR(local_folder, local_file_name)
            
            if conf > THRESH:
                mqttc.publish("homeassistant/sensor/espmeter/status", "OK", qos=1, retain=True)
                mqttc.publish("homeassistant/sensor/espmeter/result", int_res, qos=1, retain=True)
                mqttc.publish("homeassistant/sensor/espmeter/confidence", conf, qos=1, retain=True)
                mqttc.publish("homeassistant/sensor/espmeter/raw", raw, qos=1, retain=True)
                
                print(f'{timestamp()} MQTT Published {int_res}, {conf}, {raw}')
            else:
                mqttc.publish("homeassistant/sensor/espmeter/status", "Confidence too low", qos=1, retain=True)
                mqttc.publish("homeassistant/sensor/espmeter/confidence", conf, qos=1, retain=True)
                mqttc.publish("homeassistant/sensor/espmeter/raw", raw, qos=1, retain=True)
                
                print(f'{timestamp()} MQTT Published. Too low, {conf}, {raw}')
        try:
            im_put = smb_put(username, password, server, samba_folder, samba_put_name, local_file_name, local_folder)
        except Exception as err:
            print(f'{timestamp()} A problem occurred: {err}.')
            pass

    print()
            
               

mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.on_connect = on_connect
mqttc.on_message = on_message

mqttc.username_pw_set(mqtt_user, mqtt_pass)

mqttc.connect(mqtt_broker_ip, mqtt_broker_port, 60)

mqttc.loop_start()

run = True
loops = 0
while run:
    loops += 1
    print(f'{timestamp()} MQTT Loop running ({loops} loops).')
    time.sleep(60)
    
    
mqttc.loop_stop()    
