"""
Example usage of PA1010D GPS library for Raspberry Pi Pico
"""

import time
from pA1010D_GPS import PA1010D

# Initialize GPS module
# Default pins: TX=GP0, RX=GP1, UART0
# Optional enable pin on GP2
gps = PA1010D(uart_id=0, tx_pin=0, rx_pin=1, enable_pin=2)

# Alternative initialization without enable pin
# gps = PA1010D(uart_id=0, tx_pin=0, rx_pin=1)

# Wait for GPS to initialize
print("Initializing GPS...")
time.sleep(2)

# Target location for distance/bearing calculation (example: London)
target_lat = 51.5074
target_lon = -0.1278

def main():
    print("PA1010D GPS Test")
    print("Waiting for GPS fix...")
    
    last_fix_status = False
    
    while True:
        # Update GPS data
        if gps.update():
            # Check if we have a fix
            has_fix = gps.has_fix()
            
            # Print status change
            if has_fix != last_fix_status:
                if has_fix:
                    print("\n*** GPS FIX ACQUIRED ***")
                else:
                    print("\n*** GPS FIX LOST ***")
                last_fix_status = has_fix
            
            if has_fix:
                # Get location data
                lat, lon = gps.get_location()
                altitude = gps.get_altitude()
                speed = gps.get_speed()
                course = gps.get_course()
                satellites = gps.get_satellites()
                date, time_str = gps.get_datetime()
                
                print(f"\n--- GPS Data ---")
                print(f"Position: {lat:.6f}°, {lon:.6f}°")
                print(f"Altitude: {altitude}m" if altitude else "Altitude: N/A")
                print(f"Speed: {speed:.1f} km/h" if speed else "Speed: N/A")
                print(f"Course: {course:.1f}°" if course else "Course: N/A")
                print(f"Satellites: {satellites}")
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
        
        # Print last received sentence for debugging
        if gps.last_sentence:
            print(f"Last: {gps.last_sentence}")
        
        time.sleep(1)

# Advanced example showing continuous tracking
def tracking_example():
    """Example of continuous GPS tracking with waypoint navigation"""
    
    # Define waypoints (example path)
    waypoints = [
        (51.5074, -0.1278),  # London
        (48.8566, 2.3522),   # Paris
        (41.9028, 12.4964),  # Rome
    ]
    
    current_waypoint = 0
    
    print("Starting GPS tracking...")
    
    while True:
        if gps.update() and gps.has_fix():
            lat, lon = gps.get_location()
            
            if current_waypoint < len(waypoints):
                target_lat, target_lon = waypoints[current_waypoint]
                distance = gps.distance_to(target_lat, target_lon)
                bearing = gps.bearing_to(target_lat, target_lon)
                
                print(f"Current: {lat:.6f}, {lon:.6f}")
                print(f"Waypoint {current_waypoint + 1}: {distance/1000:.2f}km @ {bearing:.1f}°")
                
                # Check if we've reached the waypoint (within 100m)
                if distance < 100:
                    print(f"Reached waypoint {current_waypoint + 1}!")
                    current_waypoint += 1
                    
                    if current_waypoint >= len(waypoints):
                        print("Journey complete!")
                        break
        
        time.sleep(2)

# Simple example for basic location reading
def simple_example():
    """Simple example that just prints location when available"""
    
    while True:
        gps.update()
        
        if gps.has_fix():
            lat, lon = gps.get_location()
            print(f"Location: {lat:.6f}, {lon:.6f}")
        else:
            print("Waiting for GPS fix...")
            
        time.sleep(3)

if __name__ == "__main__":
    try:
        # Run the main example
        main()
        
        # Uncomment to run other examples:
        # simple_example()
        # tracking_example()
        
    except KeyboardInterrupt:
        print("\nShutting down...")
        gps.disable()  # Turn off GPS if enable pin is used