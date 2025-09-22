"""
PA1010D GPS Module Library for MicroPython on Raspberry Pi Pico
Author: Assistant
Version: 1.0

This library provides an interface to communicate with the PA1010D GPS module
via UART and parse NMEA sentences to extract location data.
"""

import time
import math
from machine import UART, Pin

class PA1010D:
    """
    PA1010D GPS module driver for MicroPython
    
    Supports parsing of NMEA sentences including:
    - GPGGA (Global Positioning System Fix Data)
    - GPRMC (Recommended Minimum Course)
    - GPGSA (GPS DOP and active satellites)
    - GPGSV (GPS Satellites in view)
    """
    
    def __init__(self, uart_id=0, tx_pin=0, rx_pin=1, baudrate=9600, enable_pin=None):
        """
        Initialize PA1010D GPS module
        
        Args:
            uart_id (int): UART interface number (0 or 1)
            tx_pin (int): TX pin number
            rx_pin (int): RX pin number  
            baudrate (int): UART baudrate (default 9600)
            enable_pin (int): Optional enable pin for GPS module power control
        """
        self.uart = UART(uart_id, baudrate=baudrate, tx=Pin(tx_pin), rx=Pin(rx_pin))
        
        # Enable pin setup (optional)
        self.enable_pin = None
        if enable_pin is not None:
            self.enable_pin = Pin(enable_pin, Pin.OUT)
            self.enable_pin.value(1)  # Enable GPS module
            
        # GPS data storage
        self.latitude = None
        self.longitude = None
        self.altitude = None
        self.speed = None
        self.course = None
        self.satellites = None
        self.hdop = None
        self.fix_quality = 0
        self.timestamp = None
        self.date = None
        
        # Internal buffers
        self._buffer = ""
        self.last_sentence = ""
        
    def enable(self):
        """Enable GPS module if enable pin is configured"""
        if self.enable_pin:
            self.enable_pin.value(1)
            time.sleep_ms(100)
            
    def disable(self):
        """Disable GPS module if enable pin is configured"""
        if self.enable_pin:
            self.enable_pin.value(0)
            
    def _checksum_valid(self, sentence):
        """Verify NMEA sentence checksum"""
        if '*' not in sentence:
            return False
            
        data, checksum = sentence.split('*')
        calculated = 0
        for char in data[1:]:  # Skip the '$'
            calculated ^= ord(char)
            
        try:
            return calculated == int(checksum, 16)
        except ValueError:
            return False
            
    def _parse_coordinate(self, coord_str, direction):
        """Parse NMEA coordinate format (ddmm.mmmm) to decimal degrees"""
        if not coord_str or not direction:
            return None
            
        try:
            # Convert ddmm.mmmm to decimal degrees
            degrees = int(float(coord_str) / 100)
            minutes = float(coord_str) - (degrees * 100)
            decimal = degrees + minutes / 60.0
            
            # Apply direction (N/E positive, S/W negative)
            if direction in ['S', 'W']:
                decimal = -decimal
                
            return decimal
        except (ValueError, TypeError):
            return None
            
    def _parse_time(self, time_str):
        """Parse NMEA time format (hhmmss.sss)"""
        if not time_str or len(time_str) < 6:
            return None
            
        try:
            hours = int(time_str[0:2])
            minutes = int(time_str[2:4])
            seconds = float(time_str[4:])
            return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}"
        except (ValueError, IndexError):
            return None
            
    def _parse_date(self, date_str):
        """Parse NMEA date format (ddmmyy)"""
        if not date_str or len(date_str) < 6:
            return None
            
        try:
            day = int(date_str[0:2])
            month = int(date_str[2:4])
            year = 2000 + int(date_str[4:6])  # Assume 20xx
            return f"{year}-{month:02d}-{day:02d}"
        except (ValueError, IndexError):
            return None
            
    def _parse_gga(self, fields):
        """Parse GPGGA sentence (GPS Fix Data)"""
        if len(fields) < 15:
            return
            
        # Time
        self.timestamp = self._parse_time(fields[1])
        
        # Position
        self.latitude = self._parse_coordinate(fields[2], fields[3])
        self.longitude = self._parse_coordinate(fields[4], fields[5])
        
        # Fix quality (0=invalid, 1=GPS fix, 2=DGPS fix)
        try:
            self.fix_quality = int(fields[6]) if fields[6] else 0
        except ValueError:
            self.fix_quality = 0
            
        # Number of satellites
        try:
            self.satellites = int(fields[7]) if fields[7] else 0
        except ValueError:
            self.satellites = 0
            
        # Horizontal dilution of precision
        try:
            self.hdop = float(fields[8]) if fields[8] else None
        except ValueError:
            self.hdop = None
            
        # Altitude
        try:
            self.altitude = float(fields[9]) if fields[9] else None
        except ValueError:
            self.altitude = None
            
    def _parse_rmc(self, fields):
        """Parse GPRMC sentence (Recommended Minimum Course)"""
        if len(fields) < 12:
            return
            
        # Time
        self.timestamp = self._parse_time(fields[1])
        
        # Status (A=active, V=void)
        status = fields[2]
        if status != 'A':
            return  # Invalid data
            
        # Position
        self.latitude = self._parse_coordinate(fields[3], fields[4])
        self.longitude = self._parse_coordinate(fields[5], fields[6])
        
        # Speed (knots to km/h)
        try:
            speed_knots = float(fields[7]) if fields[7] else 0
            self.speed = speed_knots * 1.852  # Convert to km/h
        except ValueError:
            self.speed = None
            
        # Course
        try:
            self.course = float(fields[8]) if fields[8] else None
        except ValueError:
            self.course = None
            
        # Date
        self.date = self._parse_date(fields[9])
        
    def _parse_sentence(self, sentence):
        """Parse a complete NMEA sentence"""
        if not sentence.startswith('$') or not self._checksum_valid(sentence):
            return
            
        # Remove checksum
        if '*' in sentence:
            sentence = sentence.split('*')[0]
            
        fields = sentence.split(',')
        sentence_type = fields[0][3:]  # Remove '$GP' prefix
        
        if sentence_type == 'GGA':
            self._parse_gga(fields)
        elif sentence_type == 'RMC':
            self._parse_rmc(fields)
            
    def update(self):
        """
        Read and parse available GPS data
        
        Returns:
            bool: True if new data was processed, False otherwise
        """
        if not self.uart.any():
            return False
            
        # Read available data
        data = self.uart.read()
        if not data:
            return False
            
        # Add to buffer and process complete sentences
        self._buffer += data.decode('utf-8', 'ignore')
        
        processed = False
        while '\n' in self._buffer:
            line, self._buffer = self._buffer.split('\n', 1)
            line = line.strip()
            
            if line:
                self.last_sentence = line
                self._parse_sentence(line)
                processed = True
                
        return processed
        
    def has_fix(self):
        """
        Check if GPS has a valid fix
        
        Returns:
            bool: True if GPS has valid position data
        """
        return (self.fix_quality > 0 and 
                self.latitude is not None and 
                self.longitude is not None)
                
    def get_location(self):
        """
        Get current GPS location
        
        Returns:
            tuple: (latitude, longitude) or (None, None) if no fix
        """
        if self.has_fix():
            return (self.latitude, self.longitude)
        return (None, None)
        
    def get_altitude(self):
        """
        Get current altitude in meters
        
        Returns:
            float: Altitude in meters or None if unavailable
        """
        return self.altitude
        
    def get_speed(self):
        """
        Get current speed in km/h
        
        Returns:
            float: Speed in km/h or None if unavailable
        """
        return self.speed
        
    def get_course(self):
        """
        Get current course/heading in degrees
        
        Returns:
            float: Course in degrees (0-359.9) or None if unavailable
        """
        return self.course
        
    def get_satellites(self):
        """
        Get number of satellites in use
        
        Returns:
            int: Number of satellites or 0 if unavailable
        """
        return self.satellites or 0
        
    def get_datetime(self):
        """
        Get GPS date and time
        
        Returns:
            tuple: (date_string, time_string) or (None, None) if unavailable
        """
        return (self.date, self.timestamp)
        
    def distance_to(self, target_lat, target_lon):
        """
        Calculate distance to target coordinates using Haversine formula
        
        Args:
            target_lat (float): Target latitude
            target_lon (float): Target longitude
            
        Returns:
            float: Distance in meters or None if no current position
        """
        if not self.has_fix():
            return None
            
        # Haversine formula
        R = 6371000  # Earth radius in meters
        
        lat1_rad = math.radians(self.latitude)
        lat2_rad = math.radians(target_lat)
        delta_lat = math.radians(target_lat - self.latitude)
        delta_lon = math.radians(target_lon - self.longitude)
        
        a = (math.sin(delta_lat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * 
             math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
        
    def bearing_to(self, target_lat, target_lon):
        """
        Calculate bearing to target coordinates
        
        Args:
            target_lat (float): Target latitude
            target_lon (float): Target longitude
            
        Returns:
            float: Bearing in degrees (0-359.9) or None if no current position
        """
        if not self.has_fix():
            return None
            
        lat1_rad = math.radians(self.latitude)
        lat2_rad = math.radians(target_lat)
        delta_lon_rad = math.radians(target_lon - self.longitude)
        
        y = math.sin(delta_lon_rad) * math.cos(lat2_rad)
        x = (math.cos(lat1_rad) * math.sin(lat2_rad) - 
             math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(delta_lon_rad))
        
        bearing_rad = math.atan2(y, x)
        bearing_deg = math.degrees(bearing_rad)
        
        # Normalize to 0-359.9
        return (bearing_deg + 360) % 360
        
    def __str__(self):
        """String representation of GPS status"""
        if self.has_fix():
            return (f"GPS Fix: {self.latitude:.6f}, {self.longitude:.6f} "
                   f"Alt: {self.altitude}m Sats: {self.satellites}")
        else:
            return f"GPS: No Fix (Sats: {self.satellites or 0})"