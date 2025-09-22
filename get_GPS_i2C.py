"""
Example usage of PA1010D GPS library for Raspberry Pi Pico (I2C Interface)
"""

from machine import I2C, Pin
from machine import Pin, PWM
import time
from PA1010D import PA1010D
from pimoroni_i2c import PimoroniI2C
from rgb_leds import set_color

PINS_BREAKOUT_GARDEN = {"sda": 4, "scl": 5}
PINS_PICO_EXPLORER = {"sda": 20, "scl": 21}

i2c = PimoroniI2C(**PINS_PICO_EXPLORER)
# Initialize GPS module with I2C
# Default: SCL=GP5, SDA=GP4, Address=0x10
gps = PA1010D(i2c=i2c, address=0x10)

# Alternative initialization methods:

# Using existing I2C object
# i2c = I2C(0, scl=Pin(5), sda=Pin(4), freq=400000)
# gps = PA1010D(i2c=i2c, address=0x10)

# Without enable pin
# gps = PA1010D(scl_pin=5, sda_pin=4, address=0x10)

# Different I2C pins (if needed)
# gps = PA1010D(scl_pin=9, sda_pin=8, address=0x10)

# Wait for GPS to initialize
print("Initializing I2C GPS...")
set_color(255,255,255)
time.sleep(2)

# Target location for distance/bearing calculation (example: London)
target_lat = 51.5074
target_lon = -0.1278

def check_i2c_connection():
    """Check I2C bus and GPS module connection"""
    print("Scanning I2C bus...")
    devices = gps.scan_i2c()
    
    if devices:
        print(f"I2C devices found: {[hex(addr) for addr in devices]}")
        if gps.address in devices:
            print(f"✓ GPS module found at address 0x{gps.address:02X}")
        else:
            print(f"✗ GPS module NOT found at expected address 0x{gps.address:02X}")
    else:
        print("No I2C devices found!")
        
    # Test connection
    if gps.is_connected():
        print("✓ GPS module is responding")
    else:
        print("✗ GPS module is not responding")

def main():
    """Main GPS monitoring loop"""
    print("PA1010D GPS Test (I2C Interface)")
    
    # Check I2C connection first
    check_i2c_connection()
    print("\nWaiting for GPS fix...")
    
    last_fix_status = False
    error_count = 0
    max_errors = 5
    
    while True:
        try:
            # Update GPS data
            if gps.update():
                error_count = 0  # Reset error counter on successful read
                
                # Check if we have a fix
                has_fix = gps.has_fix()
                
                # Print status change
                if has_fix != last_fix_status:
                    if has_fix:
                        print("\n*** GPS FIX ACQUIRED ***")
                        set_color(0,255,255)
                    else:
                        print("\n*** GPS FIX LOST ***")
                        set_color(255,128,0)
                    last_fix_status = has_fix
                
                if has_fix:
                    # Get location data
                    set_color(0,255,200)
                    
                    lat, lon = gps.get_location()
                    altitude = gps.get_altitude()
                    speed = gps.get_speed()
                    course = gps.get_course()
                    satellites = gps.get_satellites()
                    hdop = gps.get_hdop()
                    date, time_str = gps.get_datetime()
                    
                    print(f"\n--- GPS Data ---")
                    print(f"Position: {lat:.6f}°, {lon:.6f}°")
                    print(f"Altitude: {altitude}m" if altitude else "Altitude: N/A")
                    print(f"Speed: {speed:.1f} km/h" if speed else "Speed: N/A")
                    print(f"Course: {course:.1f}°" if course else "Course: N/A")
                    print(f"Satellites: {satellites}")
                    print(f"HDOP: {hdop:.1f}" if hdop else "HDOP: N/A")
                    print(f"Date/Time: {date} {time_str}" if date and time_str else "Date/Time: N/A")
                    
                    # Calculate distance and bearing to target
                    distance = gps.distance_to(target_lat, target_lon)
                    bearing = gps.bearing_to(target_lat, target_lon)
                    
                    if distance is not None and bearing is not None:
                        print(f"Distance to London: {distance/1000:.2f} km")
                        print(f"Bearing to London: {bearing:.1f}°")
                    
                else:
                    # No fix - show satellite count
                    satellites = gps.get_satellites()
                    print(f"Searching for satellites... ({satellites} visible)")
                    set_color(128,50,50)
                    time.sleep(0.5)
                    set_color(50,128,50)
                    time.sleep(0.5)
                    set_color(50,50,128)
                
                # Print last received sentence for debugging
                if gps.last_sentence:
                    print(f"Last: {gps.last_sentence}")
                    
            else:
                # No new data received
                if not gps.is_connected():
                    error_count += 1
                    print(f"I2C communication error ({error_count}/{max_errors})")
                    
                    if error_count >= max_errors:
                        print("Too many I2C errors. Checking connection...")
                        check_i2c_connection()
                        error_count = 0
                        time.sleep(2)
        
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Unexpected error: {e}")
            time.sleep(1)
            
        time.sleep(1)

def i2c_diagnostic():
    """Run I2C diagnostic tests"""
    print("=== I2C GPS Diagnostic ===")
    
    # Check I2C bus
    check_i2c_connection()
    
    # Test continuous reading
    print(f"\nTesting continuous I2C reads from 0x{gps.address:02X}...")
    for i in range(10):
        connected = gps.is_connected()
        print(f"Read {i+1}: {'OK' if connected else 'FAIL'}")
        time.sleep(0.5)
    
    # Monitor raw data
    print("\nMonitoring raw NMEA data (10 seconds)...")
    start_time = time.time()
    
    while time.time() - start_time < 10:
        if gps.update():
            if gps.last_sentence:
                print(f"NMEA: {gps.last_sentence}")
        time.sleep(0.1)

def simple_example():
    """Simple example that just prints location when available"""
    
    print("Simple I2C GPS Example")
    print("Press Ctrl+C to stop\n")
    
    while True:
        try:
            gps.update()
            
            if gps.has_fix():
                lat, lon = gps.get_location()
                sats = gps.get_satellites()
                print(f"Location: {lat:.6f}, {lon:.6f} (Sats: {sats})")
            else:
                sats = gps.get_satellites()
                print(f"Waiting for GPS fix... (Sats: {sats})")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")
            
        time.sleep(3)

def waypoint_navigation():
    """Example of waypoint navigation using I2C GPS"""
    
    # Define waypoints (example coordinates)
    waypoints = [
        (51.5074, -0.1278, "London"),
        (48.8566, 2.3522, "Paris"), 
        (41.9028, 12.4964, "Rome"),
        (40.7128, -74.0060, "New York")
    ]
    
    current_waypoint = 0
    waypoint_radius = 1000  # 1km radius to consider "reached"
    
    print("I2C GPS Waypoint Navigation")
    print("=" * 30)
    
    while current_waypoint < len(waypoints):
        try:
            if gps.update() and gps.has_fix():
                lat, lon = gps.get_location()
                target_lat, target_lon, name = waypoints[current_waypoint]
                
                distance = gps.distance_to(target_lat, target_lon)
                bearing = gps.bearing_to(target_lat, target_lon)
                speed = gps.get_speed() or 0
                
                print(f"\nCurrent Position: {lat:.6f}, {lon:.6f}")
                print(f"Target: {name}")
                print(f"Distance: {distance/1000:.2f} km")
                print(f"Bearing: {bearing:.1f}°")
                print(f"Speed: {speed:.1f} km/h")
                
                # Check if waypoint reached
                if distance < waypoint_radius:
                    print(f"*** Reached {name}! ***")
                    current_waypoint += 1
                    
                    if current_waypoint >= len(waypoints):
                        print("Journey complete!")
                        break
                        
            else:
                print("Waiting for GPS fix...")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Navigation error: {e}")
            
        time.sleep(2)

if __name__ == "__main__":
    try:
        # Run the main example
        main()
        
        # Uncomment to run other examples:
        # simple_example()
        # i2c_diagnostic()
        # waypoint_navigation()
        
    except KeyboardInterrupt:
        print("\nShutting down...")
        gps.disable()  # Turn off GPS if enable pin is used
    finally:
        print("GPS module disabled.")