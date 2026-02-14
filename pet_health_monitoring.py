import network
import time
from machine import I2C, Pin
import gc
import config
from twilio_client import TwilioClient
try:
    from mpu6050_1 import MPU6050
    from max30102_1 import MAX30102
    SENSORS_AVAILABLE = True
except ImportError:
    print(" Sensor libraries not found. Running in simulation mode.")
    SENSORS_AVAILABLE = False
try:
    from gps_module import GPS
    GPS_AVAILABLE = True
except ImportError:
    print(" GPS module not found. GPS tracking disabled.")
    GPS_AVAILABLE = False


class PetHealthMonitor:
    def __init__(self):
        """Initialize the monitoring system"""
        self.last_alert_time = 0
        self.last_gps_update = 0
        self.wifi = None
        self.i2c = None
        self.mpu_sensor = None  
        self.max_sensor = None
        self.twilio = None
        self.gps = None
        self.current_location = None

        print("=" * 50)
        print("Pet Health Monitor Starting...")
        print("=" * 50)
        self.connect_wifi()
        if SENSORS_AVAILABLE and not config.SIMULATE_SENSORS:
            self.init_sensors()
        else:
            print(" Running in SIMULATION mode")
        if config.USE_GPS and GPS_AVAILABLE:
            self.init_gps()
        else:
            print(" GPS tracking disabled")
        self.init_twilio()

        print(" System initialized successfully!")
        print("=" * 50)
    
    def connect_wifi(self):
        print(f" Connecting to WiFi: {config.WIFI_SSID}")
        
        self.wifi = network.WLAN(network.STA_IF)
        self.wifi.active(True)
        self.wifi.connect(config.WIFI_SSID, config.WIFI_PASSWORD)
        timeout = 20
        while not self.wifi.isconnected() and timeout > 0:
            print(".", end="")
            time.sleep(1)
            timeout -= 1
        
        if self.wifi.isconnected():
            print(f"\n WiFi connected!")
            print(f"   IP: {self.wifi.ifconfig()[0]}")
        else:
            print("\n WiFi connection failed!")
            raise Exception("WiFi connection timeout")
    
    def init_sensors(self):
        """Initialize I2C and sensors"""
        print(" Initializing sensors...")
        self.i2c = I2C(0, scl=Pin(config.I2C_SCL_PIN), sda=Pin(config.I2C_SDA_PIN), freq=config.I2C_FREQ)
        
        if config.USE_MULTIPLEXER:
            print(f"   Using TCA9548A multiplexer at 0x{config.TCA9548A_ADDRESS:02X}")
            self.select_mux_channel(config.MPU6050_CHANNEL)
            self.mpu_sensor = MPU6050(self.i2c)
            print(f" MPU6050 on channel {config.MPU6050_CHANNEL}")

            self.select_mux_channel(config.MAX30102_CHANNEL)
            self.max_sensor = MAX30102(self.i2c)
            print(f" MAX30102 on channel {config.MAX30102_CHANNEL}")
        else:
            self.mpu_sensor = MPU6050(self.i2c)
            self.max_sensor = MAX30102(self.i2c)
            print(" Sensors initialized (direct I2C)")
    
    def select_mux_channel(self, channel):
        if 0 <= channel <= 7:
            self.i2c.writeto(config.TCA9548A_ADDRESS, bytes([1 << channel]))
    
    def init_twilio(self):
        print(" Initializing Twilio client...")
        
        self.twilio = TwilioClient(
            account_sid=config.TWILIO_ACCOUNT_SID,
            auth_token=config.TWILIO_AUTH_TOKEN,
            from_number=config.TWILIO_PHONE_NUMBER,
            api_url=config.TWILIO_API_URL
        )
        if self.twilio.test_connection():
            print(" Twilio ready")
        else:
            print("  Twilio connection test failed (will retry on alert)")

    def init_gps(self):
        print("\n Initializing GPS...")

        try:
            self.gps = GPS(
                uart_id=config.GPS_UART_ID,
                tx_pin=config.GPS_TX_PIN,
                rx_pin=config.GPS_RX_PIN,
                baudrate=config.GPS_BAUDRATE
            )
            print(" GPS module initialized")
            print(" Waiting for GPS fix (this may take 30-60 seconds)...")
        except Exception as e:
            print(f" GPS initialization failed: {e}")
            self.gps = None

    def read_gps(self):
        if not self.gps:
            return None

        try:
            self.gps.update(timeout=config.GPS_TIMEOUT)
            if self.gps.has_fix:
                location = self.gps.get_location()
                self.current_location = location

                if config.DEBUG_MODE:
                    print(f" GPS: {self.gps.get_coordinates_string()} | "
                          f"Sats: {self.gps.satellites} | Alt: {self.gps.altitude}m")

                return location
            else:
                if config.DEBUG_MODE:
                    print(f" GPS: Searching for fix... (Sats: {self.gps.satellites})")
                return None

        except Exception as e:
            print(f" GPS read error: {e}")
            return None
    
    def read_sensors(self): 
        if config.SIMULATE_SENSORS or not SENSORS_AVAILABLE: 
            import random
            return (
                random.randint(85, 100),  
                random.randint(60, 160),  
                random.uniform(0.2, 2.0)
                )

        try:
            if config.USE_MULTIPLEXER:
                self.select_mux_channel(config.MAX30102_CHANNEL)

            spo2 = self.max_sensor.read_spo2()
            heart_rate = self.max_sensor.read_heart_rate()
        except Exception as e:
            print(f" MAX30102 read error: {e}")
            spo2 = 0
            heart_rate = 0

        try:
            if config.USE_MULTIPLEXER:
                self.select_mux_channel(config.MPU6050_CHANNEL)

            accel = self.mpu_sensor.get_accel_data()
            motion = abs(accel['x']) + abs(accel['y']) + abs(accel['z'])
        except Exception as e:
            print(f" MPU6050 read error: {e}")
            motion = 0

        return (spo2, heart_rate, motion)

    def analyze_health(self, spo2, heart_rate, motion):
        abnormal_count = 0
        issues = []
        if spo2 > 0 and spo2 < config.SPO2_MIN_THRESHOLD:
            abnormal_count += 1
            issues.append(f"Low SpO2: {spo2}%")
        if heart_rate > 0:
            if heart_rate < config.HEART_RATE_MIN:
                abnormal_count += 1
                issues.append(f"Low heart rate: {heart_rate} BPM")
            elif heart_rate > config.HEART_RATE_MAX:
                abnormal_count += 1
                issues.append(f"High heart rate: {heart_rate} BPM")
        if motion < config.MOTION_MIN_THRESHOLD:
            abnormal_count += 1
            issues.append(f"Low motion: {motion:.2f}")
        elif motion > config.MOTION_MAX_THRESHOLD:
            abnormal_count += 1
            issues.append(f"Excessive motion: {motion:.2f}")

        return (abnormal_count, issues)

    def send_alert(self, issues, location=None):
        current_time = time.time()
        if current_time - self.last_alert_time < config.ALERT_COOLDOWN:
            remaining = config.ALERT_COOLDOWN - (current_time - self.last_alert_time)
            print(f" Alert cooldown active ({remaining:.0f}s remaining)")
            return

        print(" EMERGENCY DETECTED!")
        print(f"   Issues: {', '.join(issues)}")

        if location:
            print(f" Location: {location['latitude']:.6f}, {location['longitude']:.6f}")
            print(f" Satellites: {location.get('satellites', 0)}")
        print(" Initiating voice call...")
        call_result = self.twilio.make_call(
            to_number=config.OWNER_PHONE_NUMBER,
            twiml_url=config.TWIML_URL
        )

        if call_result:
            print(" Voice call initiated!")
        else:
            print(" Voice call failed")
        if config.SEND_LOCATION_VIA_SMS:
            if location and location.get('has_fix'):
                self.send_location_sms(issues, location)
            else:
                print(" Sending SMS alert (no GPS fix available)...")
                self.send_basic_sms(issues) 
        if call_result or config.SEND_LOCATION_VIA_SMS:
            self.last_alert_time = current_time

    def send_location_sms(self, issues, location):
        try:
            lat = location['latitude']
            lon = location['longitude']
            alt = location.get('altitude', 0)
            sats = location.get('satellites', 0)
            sms_body = " PET HEALTH ALERT!\n\n"
            sms_body += "Health Issues:\n"
            for issue in issues:
                sms_body += f"• {issue}\n"

            sms_body += f"\n GPS Location:\n"
            sms_body += f"Latitude: {lat:.6f}°\n"
            sms_body += f"Longitude: {lon:.6f}°\n"
            sms_body += f"Altitude: {alt:.1f}m\n"
            sms_body += f"Satellites: {sats}\n"
            if config.INCLUDE_MAPS_LINK:
                maps_url = f"https://www.google.com/maps?q={lat:.6f},{lon:.6f}"
                sms_body += f"\n View Location:\n{maps_url}" 
            print(" Sending GPS location SMS...")
            result = self.twilio.send_sms(
                to_number=config.OWNER_PHONE_NUMBER,
                message=sms_body
            )

            if result:
                print(" Location SMS sent successfully!")
            else:
                print(" Location SMS failed to send")

        except Exception as e:
            print(f" Error sending location SMS: {e}")

    def send_basic_sms(self, issues): 
        try: 
            sms_body = " PET HEALTH ALERT!\n\n"
            sms_body += "Health Issues:\n"
            for issue in issues:
                sms_body += f"• {issue}\n"
            sms_body += "\n GPS location unavailable" 
            print(" Sending basic SMS alert...")
            result = self.twilio.send_sms(
                to_number=config.OWNER_PHONE_NUMBER,
                message=sms_body
            )

            if result:
                print(" SMS alert sent!")
            else:
                print("  SMS alert failed")

        except Exception as e:
            print(f" Error sending SMS: {e}")

    def run(self):
        """Main monitoring loop"""
        print("\n Starting monitoring loop...")
        print(f"   Reading interval: {config.SENSOR_READ_INTERVAL}s")
        print(f"   Alert threshold: {config.ABNORMAL_COUNT_THRESHOLD} abnormal readings")
        if config.USE_GPS and self.gps:
            print(f"   GPS update interval: {config.GPS_UPDATE_INTERVAL}s")
        print("-" * 50)

        while True:
            try:
                spo2, heart_rate, motion = self.read_sensors()
                current_time = time.time()
                if config.USE_GPS and self.gps:
                    if current_time - self.last_gps_update >= config.GPS_UPDATE_INTERVAL:
                        self.read_gps()
                        self.last_gps_update = current_time
                abnormal_count, issues = self.analyze_health(spo2, heart_rate, motion)
                if config.DEBUG_MODE:
                    print(f" SpO2: {spo2}% | HR: {heart_rate} BPM | Motion: {motion:.2f}")
                    if abnormal_count > 0:
                        print(f" Abnormal: {abnormal_count} - {issues}")
                if abnormal_count >= config.ABNORMAL_COUNT_THRESHOLD:
                    self.send_alert(issues, location=self.current_location)
                gc.collect()
                time.sleep(config.SENSOR_READ_INTERVAL)

            except KeyboardInterrupt:
                print("\n\n Monitoring stopped by user")
                break
            except Exception as e:
                print(f" Error in main loop: {e}")
                time.sleep(5) 
if __name__ == "__main__":
    try:
        monitor = PetHealthMonitor()
        monitor.run()
    except Exception as e:
        print(f" Fatal error: {e}")
        import sys
        sys.print_exception(e)


