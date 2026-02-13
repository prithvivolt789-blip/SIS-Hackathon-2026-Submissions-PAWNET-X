#the gps module code 

from machine import UART, Pin
import time


class GPS:
    
    def __init__(self, uart_id=1, tx_pin=21, rx_pin=20, baudrate=9600):
        self.uart = UART(uart_id, baudrate=baudrate, tx=Pin(tx_pin), rx=Pin(rx_pin))
        
        self.latitude = None
        self.longitude = None
        self.altitude = None
        self.satellites = 0
        self.speed = None
        self.course = None
        self.timestamp = None
        self.date = None
        self.fix_quality = 0
        self.hdop = None
        
        self.has_fix = False
        self.last_update = 0
        
        print(" GPS module initialized")
        print(f"   UART{uart_id}: TX=GPIO{tx_pin}, RX=GPIO{rx_pin}, Baud={baudrate}")
    
    def update(self, timeout=1000):
        start_time = time.ticks_ms()
        updated = False
        
        while time.ticks_diff(time.ticks_ms(), start_time) < timeout:
            if self.uart.any():
                try:
                    line = self.uart.readline()
                    if line:
                        sentence = line.decode('ascii', 'ignore').strip()
                        if self._parse_sentence(sentence):
                            updated = True
                            self.last_update = time.time()
                except Exception as e:
                    pass
        
        return updated
    
    def _parse_sentence(self, sentence):
        
        if not sentence.startswith('$'):
            return False

        if '*' in sentence:
            data, checksum = sentence.rsplit('*', 1)
            if not self._verify_checksum(data[1:], checksum):
                return False
        
        parts = sentence.split(',')
        sentence_type = parts[0]
        
        if sentence_type == '$GPGGA' or sentence_type == '$GNGGA':
            return self._parse_gga(parts)
        elif sentence_type == '$GPRMC' or sentence_type == '$GNRMC':
            return self._parse_rmc(parts)
        elif sentence_type == '$GPGSA' or sentence_type == '$GNGSA':
            return self._parse_gsa(parts)
        
        return False
    
    def _parse_gga(self, parts):
        """Parse GGA sentence (Global Positioning System Fix Data)"""
        try:
            if len(parts) < 15:
                return False
            
            self.fix_quality = int(parts[6]) if parts[6] else 0
            self.has_fix = self.fix_quality > 0
            
            if not self.has_fix:
                return False
            
            if parts[2] and parts[3]:
                self.latitude = self._convert_to_degrees(parts[2], parts[3])
            
            if parts[4] and parts[5]:
                self.longitude = self._convert_to_degrees(parts[4], parts[5])
            
            if parts[9]:
                self.altitude = float(parts[9])
            
            if parts[7]:
                self.satellites = int(parts[7])
                
            if parts[8]:
                self.hdop = float(parts[8])
            
            return True
            
        except (ValueError, IndexError):
            return False
    
    def _parse_rmc(self, parts):
        
        try:
            if len(parts) < 12:
                return False
            
            
            if parts[2] != 'A':
                self.has_fix = False
                return False
            
            self.has_fix = True
            
            
            if parts[3] and parts[4]:
                self.latitude = self._convert_to_degrees(parts[3], parts[4])
            
            
            if parts[5] and parts[6]:
                self.longitude = self._convert_to_degrees(parts[5], parts[6])
            
            
            if parts[7]:
                self.speed = float(parts[7]) * 1.852  
            
            
            if parts[8]:
                self.course = float(parts[8])
            
            
            if parts[9]:
                self.date = parts[9]

            
            if parts[1]:
                self.timestamp = parts[1]

            return True

        except (ValueError, IndexError):
            return False

    def _parse_gsa(self, parts):
        try:
            if len(parts) < 18:
                return False

            
            fix_type = int(parts[2]) if parts[2] else 1
            self.has_fix = fix_type > 1

            return True

        except (ValueError, IndexError):
            return False

    def _verify_checksum(self, data, checksum):
        try:
            calc_checksum = 0
            for char in data:
                calc_checksum ^= ord(char)
            return f"{calc_checksum:02X}" == checksum.upper()
        except:
            return False

    def _convert_to_degrees(self, raw_value, direction):
        if not raw_value:
            return None

        try:
            
            decimal_pos = raw_value.index('.')

            
            degrees = int(raw_value[:decimal_pos-2])
            minutes = float(raw_value[decimal_pos-2:])

            
            result = degrees + (minutes / 60.0)

            
            if direction in ['S', 'W']:
                result = -result

            return result
        except:
            return None

    def get_location(self):
    
        if not self.has_fix:
            return None

        return {
            'latitude': self.latitude,
            'longitude': self.longitude,
            'altitude': self.altitude,
            'satellites': self.satellites,
            'speed': self.speed,
            'course': self.course,
            'timestamp': self.timestamp,
            'date': self.date,
            'fix_quality': self.fix_quality,
            'hdop': self.hdop
        }

    def get_coordinates_string(self):
    
        if not self.has_fix or self.latitude is None or self.longitude is None:
            return "No GPS fix"

        return f"{self.latitude:.6f}, {self.longitude:.6f}"

    def get_google_maps_url(self):
    
        if not self.has_fix or self.latitude is None or self.longitude is None:
            return None

        return f"https://www.google.com/maps?q={self.latitude:.6f},{self.longitude:.6f}"

    def get_status(self):
    
        return {
            'has_fix': self.has_fix,
            'satellites': self.satellites,
            'fix_quality': self.fix_quality,
            'hdop': self.hdop,
            'last_update': self.last_update
        }

    def __str__(self):
        
        if not self.has_fix:
            return "GPS: No fix"

        return (f"GPS: {self.latitude:.6f}, {self.longitude:.6f} | "
                f"Alt: {self.altitude}m | Sats: {self.satellites} | "
                f"Speed: {self.speed:.1f}km/h" if self.speed else "GPS: No data")


