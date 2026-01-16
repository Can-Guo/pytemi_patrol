#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Quick navigation test - sends goto command and monitors status
"""
from temi_control import Temi_Control_Def
import time

print("="*60)
print("Quick Navigation Test")
print("="*60)

controller = Temi_Control_Def(
    broker_host="192.168.8.132",
    temi_serial="00121506569",
    silent=False
)

if not controller.connect():
    print("Failed to connect")
    exit(1)

try:
    # Print initial status
    controller.print_status()
    
    # Send goto command
    target = "a6a"
    print(f"\n➤ Sending goto command to: {target}")
    controller.goto_waypoint(target)
    
    # Monitor for 30 seconds
    print(f"\n➤ Monitoring navigation (30 seconds)...")
    for i in range(30):
        time.sleep(1)
        status = controller.get_status()
        
        # Print status every 2 seconds
        if i % 2 == 0:
            print(f"[{i+1}s] Robot: {status['robot_status']} | "
                  f"Goto: {status['goto_location']} - {status['goto_status']}")
        
        # Check if completed
        if status['goto_status'] == 'complete':
            print(f"\n✅ Navigation completed to {target}!")
            break
        elif status['goto_status'] == 'abort':
            print(f"\n⚠️  Navigation aborted!")
            break
    
    # Final status
    print("\n➤ Final status:")
    controller.print_status()
    
finally:
    controller.disconnect()
    print("\n✅ Test complete")
