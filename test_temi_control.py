#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Automated test suite for Temi_Control_Def class
Validates all functionalities without robot movement
"""
from temi_control import Temi_Control_Def, RobotStatus
import time


def test_connection():
    """Test 1: Connection and status reading"""
    print("\n" + "="*70)
    print("TEST 1: Connection and Status Reading")
    print("="*70)
    
    controller = Temi_Control_Def(
        broker_host="192.168.8.132",
        temi_serial="00121506569",
        silent=False
    )
    
    # Test connection
    print("\n➤ Testing connection...")
    if controller.connect():
        print("✅ Connection successful")
        
        # Wait for status data
        time.sleep(5)
        
        # Test get_status()
        print("\n➤ Testing get_status()...")
        status = controller.get_status()
        print(f"   Robot Status: {status['robot_status']}")
        print(f"   Battery: {status['battery']}%")
        print(f"   Available Waypoints: {status['available_waypoints']}")
        
        # Test print_status()
        print("\n➤ Testing print_status()...")
        controller.print_status()
        
        controller.disconnect()
        print("✅ Test 1 PASSED")
        return True
    else:
        print("❌ Test 1 FAILED: Connection failed")
        return False


def test_waypoint_loading():
    """Test 2: Load waypoints from file"""
    print("\n" + "="*70)
    print("TEST 2: Waypoint Loading from File")
    print("="*70)
    
    controller = Temi_Control_Def(
        broker_host="192.168.8.132",
        temi_serial="00121506569",
        silent=False
    )
    
    if not controller.connect():
        print("❌ Test 2 FAILED: Connection failed")
        return False
    
    try:
        # Test loading from file
        print("\n➤ Testing load_waypoints_from_file()...")
        waypoints = controller.load_waypoints_from_file("waypoints.txt")
        
        if waypoints:
            print(f"✅ Loaded {len(waypoints)} waypoints:")
            for i, wp in enumerate(waypoints[:5], 1):
                print(f"   {i}. {wp}")
            if len(waypoints) > 5:
                print(f"   ... and {len(waypoints)-5} more")
            print("✅ Test 2 PASSED")
            return True
        else:
            print("❌ Test 2 FAILED: No waypoints loaded")
            return False
            
    finally:
        controller.disconnect()


def test_status_enum():
    """Test 3: Robot status enumeration"""
    print("\n" + "="*70)
    print("TEST 3: Robot Status Enumeration")
    print("="*70)
    
    print("\n➤ Testing RobotStatus enum...")
    print(f"   STANDBY: {RobotStatus.STANDBY.value}")
    print(f"   NAVIGATING: {RobotStatus.NAVIGATING.value}")
    print(f"   ERROR: {RobotStatus.ERROR.value}")
    
    print("✅ Test 3 PASSED")
    return True


def test_api_methods():
    """Test 4: API methods availability"""
    print("\n" + "="*70)
    print("TEST 4: API Methods")
    print("="*70)
    
    controller = Temi_Control_Def(
        broker_host="192.168.8.132",
        temi_serial="00121506569",
        silent=True
    )
    
    print("\n➤ Checking class methods...")
    methods = [
        'connect', 'disconnect', 'get_status', 'print_status',
        'goto_waypoint', 'load_waypoints_from_file', 
        'execute_patrol', 'wait_until_ready'
    ]
    
    for method in methods:
        if hasattr(controller, method):
            print(f"   ✅ {method}()")
        else:
            print(f"   ❌ {method}() - MISSING")
            return False
    
    print("✅ Test 4 PASSED")
    return True


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*70)
    print("TEMI CONTROL SYSTEM - AUTOMATED TEST SUITE")
    print("="*70)
    
    tests = [
        ("Status Enumeration", test_status_enum),
        ("API Methods", test_api_methods),
        ("Connection and Status", test_connection),
        ("Waypoint Loading", test_waypoint_loading),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Test '{name}' crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
        
        time.sleep(1)  # Pause between tests
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print("-"*70)
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed")
    
    print("="*70 + "\n")
    
    return passed == total


if __name__ == "__main__":
    try:
        success = run_all_tests()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        exit(1)
