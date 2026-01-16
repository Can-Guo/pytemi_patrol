#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Example usage of Temi_Control_Def class
Demonstrates patrol control functionality
"""
from temi_control import Temi_Control_Def
import time


def example_single_navigation():
    """Example: Navigate to a single waypoint"""
    print("\n" + "="*60)
    print("Example 1: Single Waypoint Navigation")
    print("="*60 + "\n")
    
    # Create controller
    controller = Temi_Control_Def(
        broker_host="192.168.8.132",
        temi_serial="00121506569",
        silent=False
    )
    
    # Connect
    if not controller.connect():
        print("Failed to connect")
        return
    
    try:
        # Wait for ready
        if controller.wait_until_ready(timeout=10):
            # Navigate to waypoint
            controller.goto_waypoint("a6a")
            
            # Monitor navigation
            for i in range(20):
                time.sleep(1)
                status = controller.get_status()
                print(f"Status: {status['robot_status']} | Goto: {status['goto_status']}")
                
                if status['goto_status'] == 'complete':
                    print("✅ Navigation complete!")
                    break
    
    finally:
        controller.disconnect()


def example_patrol_from_file():
    """Example: Execute patrol from waypoint file"""
    print("\n" + "="*60)
    print("Example 2: Patrol from File")
    print("="*60 + "\n")
    
    # Create controller
    controller = Temi_Control_Def(
        broker_host="192.168.8.132",
        temi_serial="00121506569",
        silent=False
    )
    
    # Connect
    if not controller.connect():
        print("Failed to connect")
        return
    
    try:
        # Load waypoints from file
        waypoints = controller.load_waypoints_from_file(r"d:\0-YorkGUO\HKPC Project\Temi\pytemi\waypoints.txt")
        
        if not waypoints:
            print("No waypoints loaded")
            return
        
        print(f"\nLoaded waypoints: {waypoints}\n")
        
        # Wait for ready
        if controller.wait_until_ready(timeout=10):
            # Execute patrol with retry mechanism
            # - timeout: 30s per attempt
            # - max_retries: 1 (total 2 attempts per waypoint)
            success = controller.execute_patrol(
                wait_time=30, 
                check_interval=1,
                max_retries=1
            )
            
            if success:
                print("\n✅ Patrol completed successfully!")
            else:
                print("\n⚠️  Patrol completed with some waypoints skipped")
    
    finally:
        controller.disconnect()


def example_custom_patrol():
    """Example: Custom patrol with manual waypoint list"""
    print("\n" + "="*60)
    print("Example 3: Custom Patrol")
    print("="*60 + "\n")
    
    # Create controller
    controller = Temi_Control_Def(
        broker_host="192.168.8.132",
        temi_serial="00121506569",
        silent=False
    )
    
    # Connect
    if not controller.connect():
        print("Failed to connect")
        return
    
    try:
        # Set custom waypoints
        controller.patrol_waypoints = ["a13", "a12", "a2", "home base"]
        
        print(f"\nCustom waypoints: {controller.patrol_waypoints}\n")
        
        # Wait for ready
        if controller.wait_until_ready(timeout=10):
            # Execute patrol with retry mechanism
            controller.execute_patrol(
                wait_time=30,
                check_interval=1,
                max_retries=1
            )
    
    finally:
        controller.disconnect()


def example_status_monitoring():
    """Example: Continuous status monitoring"""
    print("\n" + "="*60)
    print("Example 4: Status Monitoring")
    print("="*60 + "\n")
    
    # Create controller
    controller = Temi_Control_Def(
        broker_host="192.168.8.132",
        temi_serial="00121506569",
        silent=False
    )
    
    # Connect
    if not controller.connect():
        print("Failed to connect")
        return
    
    try:
        print("Monitoring robot status (Press Ctrl+C to exit)...")
        
        while True:
            controller.print_status()
            time.sleep(5)
    
    except KeyboardInterrupt:
        print("\nExiting...")
    
    finally:
        controller.disconnect()


if __name__ == "__main__":
    # Choose which example to run
    print("\nTemi Control Examples")
    print("=" * 60)
    print("1. Single Waypoint Navigation")
    print("2. Patrol from File")
    print("3. Custom Patrol")
    print("4. Status Monitoring")
    print("=" * 60)
    
    choice = input("\nSelect example (1-4): ").strip()
    
    if choice == "1":
        example_single_navigation()
    elif choice == "2":
        example_patrol_from_file()
    elif choice == "3":
        example_custom_patrol()
    elif choice == "4":
        example_status_monitoring()
    else:
        print("Invalid choice")
