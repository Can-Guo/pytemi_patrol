#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test Position Tracking Mechanism
Validates the waypoint arrival verification system
"""
from temi_control import Temi_Control_Def
import time

def test_position_tracking():
    """Test position tracking with waypoint verification"""
    print("="*60)
    print("Position Tracking Verification Test")
    print("="*60)
    print("\nThis test validates:")
    print("  1. Position status tracking (NaN/moving/current_waypoint_XXX)")
    print("  2. Target waypoint verification")
    print("  3. Confirmed arrival detection")
    print("="*60 + "\n")
    
    # Create controller
    controller = Temi_Control_Def(
        broker_host="192.168.8.132",
        temi_serial="00121506569",
        silent=False
    )
    
    # Connect
    if not controller.connect():
        print("❌ Failed to connect")
        return
    
    try:
        print(f"\n📍 Initial Position Status:")
        print(f"   Current Position: {controller.current_position or 'NaN'}")
        print(f"   Position Status: {controller.position_status}")
        print(f"   Target Waypoint: {controller.target_waypoint or 'None'}\n")
        
        # Wait for robot ready
        if not controller.wait_until_ready(timeout=10):
            print("❌ Robot not ready")
            return
        
        # Test 1: Navigate to a12
        print("\n" + "="*60)
        print("Test 1: Single Waypoint Navigation (a12)")
        print("="*60)
        
        controller.goto_waypoint("a12")
        print(f"\n➤ Target set to: {controller.target_waypoint}")
        
        # Monitor for 20 seconds
        for i in range(20):
            time.sleep(1)
            print(f"[{i+1}s] Position: {controller.position_status} | "
                  f"Current: {controller.current_position or 'NaN'} | "
                  f"Target: {controller.target_waypoint}")
            
            # Check if arrived
            if controller.position_status.startswith("current_waypoint_"):
                if controller.current_position == controller.target_waypoint:
                    print(f"\n✅ SUCCESS: Confirmed arrival at {controller.current_position}")
                    print(f"   Position Status: {controller.position_status}")
                    break
        
        time.sleep(2)
        
        # Test 2: Navigate to another waypoint
        print("\n" + "="*60)
        print("Test 2: Second Waypoint Navigation (a13)")
        print("="*60)
        
        controller.goto_waypoint("a13")
        print(f"\n➤ Target set to: {controller.target_waypoint}")
        
        # Monitor for 30 seconds
        for i in range(30):
            time.sleep(1)
            print(f"[{i+1}s] Position: {controller.position_status} | "
                  f"Current: {controller.current_position or 'NaN'} | "
                  f"Target: {controller.target_waypoint}")
            
            # Check if arrived
            if controller.position_status.startswith("current_waypoint_"):
                if controller.current_position == controller.target_waypoint:
                    print(f"\n✅ SUCCESS: Confirmed arrival at {controller.current_position}")
                    print(f"   Position Status: {controller.position_status}")
                    break
        
        # Final status
        print("\n" + "="*60)
        print("Final Status Report")
        print("="*60)
        controller.print_status()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n🔌 Disconnecting...")
        controller.disconnect()

if __name__ == "__main__":
    test_position_tracking()
