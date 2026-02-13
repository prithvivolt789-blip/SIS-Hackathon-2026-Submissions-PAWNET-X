#configaration.py the twilio details for the main program & also for the threash hold of the sensor data

WIFI_SSID = "xxxxx"
WIFI_PASSWORD = "xxxxxx"


TWILIO_ACCOUNT_SID = "XXXXXXXXXXXX"  
TWILIO_AUTH_TOKEN = "XXXXXXXXXXXXX"                 
TWILIO_PHONE_NUMBER = "XXXXXXXXXXX"                       
OWNER_PHONE_NUMBER = "XXXXXXXXXXXX"

TWILIO_API_URL = f"https://studio.twilio.com/v2/Flows/FWd7609dee2ad07f933c4c97c8c3bf2be7"

TWIML_URL = "http://twimlets.com/message?Message=Alert"


I2C_SCL_PIN = 5  
I2C_SDA_PIN = 4  
I2C_FREQ = 400000

USE_MULTIPLEXER = True  
TCA9548A_ADDRESS = 0x70  
MPU6050_CHANNEL = 0     
MAX30102_CHANNEL = 1

MPU6050_ADDRESS = 0x68
MAX30102_ADDRESS = 0x57

SPO2_MIN_THRESHOLD = 90      
SPO2_MAX_THRESHOLD = 100

HEART_RATE_MIN = 60          
HEART_RATE_MAX = 180

MOTION_MIN_THRESHOLD = 0.3   
MOTION_MAX_THRESHOLD = 5.0

ABNORMAL_COUNT_THRESHOLD = 2  
SENSOR_READ_INTERVAL = 3      
ALERT_COOLDOWN = 300

USE_GPS = True                
GPS_UART_ID = 1              
GPS_TX_PIN = 21              
GPS_RX_PIN = 20              
GPS_BAUDRATE = 9600          
GPS_UPDATE_INTERVAL = 5      
GPS_TIMEOUT = 2000

SEND_LOCATION_VIA_SMS = True   
INCLUDE_MAPS_LINK = True

DEBUG_MODE = True             
SIMULATE_SENSORS = False