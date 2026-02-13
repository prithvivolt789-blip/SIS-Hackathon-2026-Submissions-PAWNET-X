

from machine import I2C
import time

class MPU6050:

    PWR_MGMT_1 = 0x6B
    ACCEL_XOUT_H = 0x3B
    GYRO_XOUT_H = 0x43
    TEMP_OUT_H = 0x41
    
    def __init__(self, i2c, address=0x68):
        self.i2c = i2c
        self.address = address
        
        self.i2c.writeto_mem(self.address, self.PWR_MGMT_1, b'\x00')
        time.sleep_ms(100)
    
    def read_raw_data(self, register):
        high = self.i2c.readfrom_mem(self.address, register, 1)[0]
        low = self.i2c.readfrom_mem(self.address, register + 1, 1)[0]
        
        value = (high << 8) | low
        
        if value > 32767:
            value -= 65536
        
        return value
    
    def get_accel_data(self):
        accel_x = self.read_raw_data(self.ACCEL_XOUT_H)
        accel_y = self.read_raw_data(self.ACCEL_XOUT_H + 2)
        accel_z = self.read_raw_data(self.ACCEL_XOUT_H + 4)
        scale = 9.81 / 16384.0
        
        return {
            'x': accel_x * scale,
            'y': accel_y * scale,
            'z': accel_z * scale
        }
    
    def get_gyro_data(self):
        gyro_x = self.read_raw_data(self.GYRO_XOUT_H)
        gyro_y = self.read_raw_data(self.GYRO_XOUT_H + 2)
        gyro_z = self.read_raw_data(self.GYRO_XOUT_H + 4)
        scale = 1.0 / 131.0
        
        return {
            'x': gyro_x * scale,
            'y': gyro_y * scale,
            'z': gyro_z * scale
        }
    
    def get_temp(self):
        temp_raw = self.read_raw_data(self.TEMP_OUT_H)
        temp_c = (temp_raw / 340.0) + 36.53
        
        return temp_c
    
    def get_all_data(self):
        accel = self.get_accel_data()
        gyro = self.get_gyro_data()
        temp = self.get_temp()
        
        return {
            'accel': accel,
            'gyro': gyro,
            'temp': temp
        }


if __name__ == '__main__':
    from machine import Pin
    
    print("MPU6050 Test")
    print("=" * 40)
    
    i2c = I2C(0, scl=Pin(5), sda=Pin(4), freq=400000)
    devices = i2c.scan()
    print(f"I2C devices found: {[hex(d) for d in devices]}")
    
    if 0x68 in devices:
        mpu = MPU6050(i2c)
        
        print("\nReading sensor data...")
        for i in range(5):
            data = mpu.get_all_data()
            print(f"\nReading {i+1}:")
            print(f"  Accel: X={data['accel']['x']:.2f}, Y={data['accel']['y']:.2f}, Z={data['accel']['z']:.2f} m/s²")
            print(f"  Gyro:  X={data['gyro']['x']:.2f}, Y={data['gyro']['y']:.2f}, Z={data['gyro']['z']:.2f} °/s")
            print(f"  Temp:  {data['temp']:.1f} °C")
            time.sleep(1)
    else:
        print(" MPU6050 not found at address 0x68")


