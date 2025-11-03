#!/usr/bin/env python3
"""
Test script to verify mixed security MQTT setup
Tests both anonymous and authenticated connections
"""
import subprocess
import json
import sys

def test_connection(description, host, port, username=None, password=None):
    """Test MQTT connection and return results"""
    print(f"\n{'='*60}")
    print(f"TEST: {description}")
    print(f"{'='*60}")
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Auth: {'Yes (' + username + ')' if username else 'No (anonymous)'}")
    print("-" * 60)
    
    # Build command
    cmd = ['python', 'quick_sub.py', host, str(port)]
    if username and password:
        cmd.extend([username, password])
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        output = result.stdout.strip()
        
        if not output:
            print("❌ FAILED: No output from script")
            return False
            
        data = json.loads(output)
        
        if 'error' in data:
            print(f"❌ FAILED: {data['error']}")
            return False
        
        messages = data.get('messages', [])
        count = len(messages)
        
        print(f"✅ SUCCESS: Connected and received {count} message(s)")
        
        if count > 0:
            print("\nMessages:")
            for msg in messages:
                print(f"  • {msg['topic']}: {json.dumps(msg['message'])}")
        else:
            print("  (No retained messages found)")
        
        return True
        
    except subprocess.TimeoutExpired:
        print("❌ FAILED: Connection timeout")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ FAILED: Invalid JSON response - {e}")
        print(f"Output was: {result.stdout}")
        return False
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False

def main():
    print("\n" + "="*60)
    print("  ESP32 Mixed Security MQTT Test Suite")
    print("="*60)
    print("\nThis will test 3 connection scenarios:")
    print("1. Secure broker WITHOUT credentials (should fail)")
    print("2. Secure broker WITH credentials (should succeed)")
    print("3. Insecure broker WITHOUT credentials (should succeed)")
    print("\nMake sure:")
    print("  ✓ Both MQTT brokers are running (docker compose up -d)")
    print("  ✓ ESP32 is connected and publishing data")
    
    input("\nPress Enter to start tests...")
    
    results = []
    
    # Test 1: Try to access SECURE broker without credentials (should fail)
    print("\n" + "🔒 SECURITY TEST: Can we access secure broker without password?")
    result1 = test_connection(
        "Secure Broker - Anonymous (SHOULD FAIL)",
        "192.168.100.140",
        8883
    )
    results.append(("Secure anonymous", not result1))  # Should fail, so success = not result1
    
    # Test 2: Access SECURE broker with valid credentials (should succeed)
    print("\n" + "🔑 AUTHENTICATION TEST: Can we access with correct password?")
    result2 = test_connection(
        "Secure Broker - Authenticated (SHOULD SUCCEED)",
        "192.168.100.140",
        8883,
        "testuser",
        "testpass"
    )
    results.append(("Secure authenticated", result2))
    
    # Test 3: Access INSECURE broker without credentials (should succeed)
    print("\n" + "🚨 VULNERABILITY TEST: Can anyone access insecure broker?")
    result3 = test_connection(
        "Insecure Broker - Anonymous (SHOULD SUCCEED)",
        "192.168.100.140",
        1883
    )
    results.append(("Insecure anonymous", result3))
    
    # Summary
    print("\n" + "="*60)
    print("  TEST SUMMARY")
    print("="*60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
        if not passed:
            all_passed = False
    
    print("="*60)
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED!")
        print("\nYour setup correctly demonstrates:")
        print("  ✅ Secure broker blocks anonymous access")
        print("  ✅ Secure broker allows authenticated access")
        print("  ✅ Insecure broker allows anyone to connect")
        print("\nYou can now test the dashboard:")
        print("  1. Scan WITHOUT credentials → Should see only PIR (1 sensor)")
        print("  2. Scan WITH credentials → Should see all 3 sensors")
    else:
        print("\n⚠️  SOME TESTS FAILED!")
        print("\nTroubleshooting:")
        print("  • Check if brokers are running: docker ps | grep mosquitto")
        print("  • Check if ESP32 is publishing: python check_retained.py")
        print("  • Restart brokers: cd mqtt-brokers && docker compose restart")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
