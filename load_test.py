#!/usr/bin/env python3
"""
Load Test Script for SmartParcel API
Tests 20 concurrent requests to the /health endpoint
"""

import concurrent.futures
import requests
import time
import sys

BASE_URL = "http://3.106.211.152:8080"

def test_health(i):
    """Test the /health endpoint"""
    try:
        start = time.time()
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        elapsed = time.time() - start
        return {
            'request_id': i,
            'status_code': response.status_code,
            'response_time': round(elapsed, 3),
            'success': response.status_code == 200
        }
    except Exception as e:
        return {
            'request_id': i,
            'status_code': None,
            'response_time': None,
            'success': False,
            'error': str(e)
        }

def test_create_parcel(i):
    """Test the create parcel endpoint"""
    try:
        start = time.time()
        response = requests.post(
            f"{BASE_URL}/api/parcels",
            headers={
                "Content-Type": "application/json",
                "X-API-Key": "key-driver-001"
            },
            json={
                "sender": f"LoadTest{i}",
                "receiver": "Test",
                "address": "Dubai",
                "email": f"test{i}@example.com"
            },
            timeout=10
        )
        elapsed = time.time() - start
        return {
            'request_id': i,
            'status_code': response.status_code,
            'response_time': round(elapsed, 3),
            'success': response.status_code in [200, 201]
        }
    except Exception as e:
        return {
            'request_id': i,
            'status_code': None,
            'response_time': None,
            'success': False,
            'error': str(e)
        }

def run_load_test(test_function, test_name, num_requests=20):
    print(f"\n{'='*60}")
    print(f"Running load test: {test_name}")
    print(f"Concurrent requests: {num_requests}")
    print(f"{'='*60}\n")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_requests) as executor:
        results = list(executor.map(test_function, range(num_requests)))
    
    # Calculate statistics
    successful = sum(1 for r in results if r.get('success', False))
    failed = num_requests - successful
    response_times = [r['response_time'] for r in results if r.get('response_time')]
    
    print(f"Results:")
    print(f"  Successful: {successful}/{num_requests}")
    print(f"  Failed: {failed}/{num_requests}")
    print(f"  Success Rate: {(successful/num_requests)*100:.1f}%")
    
    if response_times:
        print(f"  Avg Response Time: {sum(response_times)/len(response_times):.3f}s")
        print(f"  Min Response Time: {min(response_times):.3f}s")
        print(f"  Max Response Time: {max(response_times):.3f}s")
    
    # Print individual results
    print("\nIndividual Results:")
    for r in results:
        if r.get('success', False):
            print(f"  Request {r['request_id']}: {r['status_code']} in {r['response_time']}s")
        else:
            error = r.get('error', 'Unknown error')
            print(f"  Request {r['request_id']}: FAILED - {error}")
    
    return successful == num_requests

if __name__ == "__main__":
    print("SmartParcel Load Test")
    print("Make sure your EC2 instance is running!")
    print(f"Target: {BASE_URL}")
    
    # First check if server is reachable
    try:
        health_check = requests.get(f"{BASE_URL}/health", timeout=5)
        if health_check.status_code != 200:
            print(f"\nERROR: Server returned status {health_check.status_code}")
            sys.exit(1)
        print("\nServer is reachable! Running load tests...\n")
    except Exception as e:
        print(f"\nERROR: Cannot reach server at {BASE_URL}")
        print(f"Error: {e}")
        sys.exit(1)
    
    # Run load tests
    test1_passed = run_load_test(test_health, "GET /health", 20)
    test2_passed = run_load_test(test_create_parcel, "POST /api/parcels", 20)
    
    print(f"\n{'='*60}")
    print("LOAD TEST SUMMARY")
    print(f"{'='*60}")
    print(f"GET /health: {'✓ PASSED' if test1_passed else '✗ FAILED'}")
    print(f"POST /api/parcels: {'✓ PASSED' if test2_passed else '✗ FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 ALL TESTS PASSED! Server handles 20+ concurrent requests!")
    else:
        print("\n⚠️ Some tests failed. Check server logs.")
