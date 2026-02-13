

from machine import I2C, Pin
import time
import gc
try:
    import config
except ImportError:
    print("config.py not found. Using default settings.")
    class config:
        I2C_SCL_PIN = 5
        I2C_SDA_PIN = 4
        I2C_FREQ = 400000
        USE_MULTIPLEXER = False
        TCA9548A_ADDRESS = 0x70
        MPU6050_CHANNEL = 0
        MPU6050_2_CHANNEL = 1
        MAX30102_CHANNEL = 2
        MPU6050_ADDRESS = 0x68
        MAX30102_ADDRESS = 0x57

try:
    from mpu6050_1 import MPU6050
    MPU_AVAILABLE = True
except ImportError:
    print("mpu6050_1.py not found")
    MPU_AVAILABLE = False

try:
    from max30102_1 import MAX30102
    MAX_AVAILABLE = True
except ImportError:
    print("max30102_1.py not found")
    MAX_AVAILABLE = False

try:
    from gps_module import GPS
    GPS_AVAILABLE = True
except ImportError:
    print("gps_module.py not found")
    GPS_AVAILABLE = False


class SensorMonitor:
    
    def __init__(self):
        print("=" * 60)
        print(" SENSOR MONITOR - Real-time Readings")
        print("=" * 60)

        self.i2c = I2C(0, scl=Pin(config.I2C_SCL_PIN), 
                       sda=Pin(config.I2C_SDA_PIN), 
                       freq=config.I2C_FREQ)
        
        print(f"\n I2C initialized (SCL=GPIO{config.I2C_SCL_PIN}, SDA=GPIO{config.I2C_SDA_PIN})")
        self.scan_i2c()
        self.mpu_sensor = None  
        self.max_sensor = None
        self.gps = None

        if MPU_AVAILABLE:
            self.init_mpu_sensor()

        if MAX_AVAILABLE:
            self.init_max_sensor()

        if GPS_AVAILABLE:
            self.init_gps()
        
        print("\n" + "=" * 60)
        print(" Starting continuous monitoring...")
        print("   Press Ctrl+C to stop")
        print("=" * 60 + "\n")
    
    def scan_i2c(self):
        print("\n Scanning I2C bus...")
        devices = self.i2c.scan()
        
        if devices:
            print(f"   Found {len(devices)} device(s):")
            for addr in devices:
                name = self.get_device_name(addr)
                print(f"   - 0x{addr:02X} ({name})")
        else:
            print("No devices found!")
    
    def get_device_name(self, addr):
        names = {
            0x70: "TCA9548A Multiplexer",
            0x68: "MPU6050 Accelerometer",
            0x57: "MAX30102 Pulse Oximeter"
        }
        return names.get(addr, "Unknown")
    
    def select_mux_channel(self, channel):
        if config.USE_MULTIPLEXER and 0 <= channel <= 7:
            self.i2c.writeto(config.TCA9548A_ADDRESS, bytes([1 << channel]))
    
    def init_mpu_sensor(self):
        try:
            if config.USE_MULTIPLEXER:
                self.select_mux_channel(config.MPU6050_CHANNEL)
                self.mpu_sensor = MPU6050(self.i2c)
                print(f"MPU6050 (Channel {config.MPU6050_CHANNEL})")
            else:
                self.mpu_sensor = MPU6050(self.i2c)
                print("MPU6050 initialized (direct I2C)")
        except Exception as e:
            print(f"MPU6050 init failed: {e}")
    
    def init_max_sensor(self):
        try:
            if config.USE_MULTIPLEXER:
                self.select_mux_channel(config.MAX30102_CHANNEL)

            self.max_sensor = MAX30102(self.i2c)
            print(f"MAX30102 initialized")
        except Exception as e:
            print(f"MAX30102 init failed: {e}")

    def init_gps(self):
        try:
            self.gps = GPS(
                uart_id=config.GPS_UART_ID,
                tx_pin=config.GPS_TX_PIN,
                rx_pin=config.GPS_RX_PIN,
                baudrate=config.GPS_BAUDRATE
            )
            print(f"GPS initialized (UART{config.GPS_UART_ID}, TX=GPIO{config.GPS_TX_PIN}, RX=GPIO{config.GPS_RX_PIN})")
        except Exception as e:
            print(f"GPS init failed: {e}")
    
    def read_mpu(self, sensor, name):
        try:
            accel = sensor.get_accel_data()
            gyro = sensor.get_gyro_data()
            temp = sensor.get_temp()
            motion = abs(accel['x']) + abs(accel['y']) + abs(accel['z'])
            
            return {
                'accel': accel,
                'gyro': gyro,
                'temp': temp,
                'motion': motion,
                'available': True
            }
        except Exception as e:
            return {'available': False, 'error': str(e)}
    
    def read_max(self):
        try:
            spo2 = self.max_sensor.read_spo2()
            hr = self.max_sensor.read_heart_rate()

            return {
                'spo2': spo2,
                'heart_rate': hr,
                'available': True
            }
        except Exception as e:
            return {'available': False, 'error': str(e)}

    def read_gps(self):
        try:
            self.gps.update(timeout=1000)  

            return {
                'latitude': self.gps.latitude,
                'longitude': self.gps.longitude,
                'altitude': self.gps.altitude,
                'satellites': self.gps.satellites,
                'has_fix': self.gps.has_fix,
                'available': True
            }
        except Exception as e:
            return {'available': False, 'error': str(e)}
    
    def display_readings(self, mpu_data, max_data, gps_data):
        """Display sensor readings in formatted output"""
        print("\033[2J\033[H", end="")

        print("=" * 60)
        print(f" SENSOR READINGS - {time.localtime()}")
        print("=" * 60)

        print("\n MPU6050 (Motion Sensor)")
        print("-" * 60)
        if mpu_data and mpu_data.get('available'):
            print(f"  Accelerometer:")
            print(f"    X: {mpu_data['accel']['x']:7.2f} m/s²")
            print(f"    Y: {mpu_data['accel']['y']:7.2f} m/s²")
            print(f"    Z: {mpu_data['accel']['z']:7.2f} m/s²")
            print(f"  Gyroscope:")
            print(f"    X: {mpu_data['gyro']['x']:7.2f} °/s")
            print(f"    Y: {mpu_data['gyro']['y']:7.2f} °/s")
            print(f"    Z: {mpu_data['gyro']['z']:7.2f} °/s")
            print(f"  Temperature: {mpu_data['temp']:.1f} °C")
            print(f"  Motion Magnitude: {mpu_data['motion']:.2f}")
        else:
            print(f"Not available")
        print("\n MAX30102 (Pulse Oximeter)")
        print("-" * 60)
        if max_data and max_data.get('available'):
            print(f"  SpO2: {max_data['spo2']}%")
            print(f"  Heart Rate: {max_data['heart_rate']} BPM")
        else:
            print(f"Not available")
        print("\n GPS Location")
        print("-" * 60)
        if gps_data and gps_data.get('available'):
            if gps_data.get('has_fix'):
                print(f"  Latitude:  {gps_data['latitude']:.6f}°")
                print(f"  Longitude: {gps_data['longitude']:.6f}°")
                print(f"  Altitude:  {gps_data['altitude']:.1f} m")
                print(f"  Satellites: {gps_data['satellites']}")
                print(f"  Status:  GPS Fix Acquired")
                if gps_data['latitude'] and gps_data['longitude']:
                    maps_url = f"https://maps.google.com/?q={gps_data['latitude']},{gps_data['longitude']}"
                    print(f"  Maps: {maps_url}")
            else:
                print(f" Searching for GPS fix...")
                print(f" Satellites: {gps_data['satellites']}")
        else:
            print(f"GPS not available")

        print("\n" + "=" * 60)
        print("Press Ctrl+C to stop monitoring")
        print("=" * 60)
    
    def run(self, interval=2):
        while True:
            try:
                mpu_data = None
                if self.mpu_sensor:
                    if config.USE_MULTIPLEXER:
                        self.select_mux_channel(config.MPU6050_CHANNEL)
                    mpu_data = self.read_mpu(self.mpu_sensor, "MPU6050")
                max_data = None
                if self.max_sensor:
                    if config.USE_MULTIPLEXER:
                        self.select_mux_channel(config.MAX30102_CHANNEL)
                    max_data = self.read_max()
                gps_data = None
                if self.gps:
                    gps_data = self.read_gps()
                self.display_readings(mpu_data, max_data, gps_data)
                gc.collect()
                time.sleep(interval)
                
            except KeyboardInterrupt:
                print("\n\n Monitoring stopped by user")
                break
            except Exception as e:
                print(f"\n Error: {e}")
                time.sleep(interval)


if __name__ == "__main__":
    try:
        monitor = SensorMonitor()
        monitor.run(interval=2)  
    except Exception as e:
        print(f"\n Fatal error: {e}")
        import sys
        sys.print_exception(e)


