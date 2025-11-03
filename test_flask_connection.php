<?php
/**
 * Simple test script to verify Flask MQTT scanner connectivity
 * Run with: php test_flask_connection.php
 */

require_once 'vendor/autoload.php';

// Test Flask connectivity
function testFlaskConnection() {
    $flaskBase = 'http://127.0.0.1:5000';
    $apiKey = 'my-very-secret-flask-key-CHANGEME';
    
    echo "🔍 Testing Flask MQTT Scanner Connection...\n\n";
    
    // Test 1: Check if Flask is running
    echo "1. Testing Flask server availability...\n";
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $flaskBase);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_TIMEOUT, 5);
    curl_setopt($ch, CURLOPT_NOBODY, true);
    
    $response = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    
    if ($httpCode == 200 || $httpCode == 302) {
        echo "   ✅ Flask server is running at $flaskBase\n\n";
    } else {
        echo "   ❌ Flask server is not accessible at $flaskBase (HTTP: $httpCode)\n";
        echo "   🔧 Make sure to run: python app.py\n\n";
        return false;
    }
    
    // Test 2: Try to start a scan job
    echo "2. Testing job-based scan API...\n";
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $flaskBase . '/api/scan');
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_HTTPHEADER, [
        'Content-Type: application/json',
        'X-API-KEY: ' . $apiKey
    ]);
    curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode([
        'target' => '127.0.0.1',
        'listen_duration' => 3,
        'capture_all_topics' => true
    ]));
    curl_setopt($ch, CURLOPT_TIMEOUT, 10);
    
    $response = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    
    if ($httpCode == 201) {
        $data = json_decode($response, true);
        if (isset($data['job_id'])) {
            echo "   ✅ Scan job started successfully\n";
            echo "   📝 Job ID: " . $data['job_id'] . "\n";
            echo "   📊 Status: " . $data['status'] . "\n\n";
            
            // Test 3: Check job status
            echo "3. Testing job status API...\n";
            sleep(2); // Wait a bit for job to process
            
            $ch = curl_init();
            curl_setopt($ch, CURLOPT_URL, $flaskBase . '/api/scan/' . $data['job_id'] . '/status');
            curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
            curl_setopt($ch, CURLOPT_HTTPHEADER, [
                'X-API-KEY: ' . $apiKey
            ]);
            curl_setopt($ch, CURLOPT_TIMEOUT, 5);
            
            $statusResponse = curl_exec($ch);
            $statusCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
            curl_close($ch);
            
            if ($statusCode == 200) {
                $statusData = json_decode($statusResponse, true);
                echo "   ✅ Job status retrieved successfully\n";
                echo "   📊 Status: " . $statusData['status'] . "\n";
                echo "   📈 Progress: " . $statusData['progress'] . "%\n";
                echo "   💬 Message: " . $statusData['message'] . "\n\n";
                
                return $data['job_id'];
            } else {
                echo "   ❌ Failed to get job status (HTTP: $statusCode)\n\n";
                return false;
            }
        }
    } else {
        echo "   ❌ Failed to start scan job (HTTP: $httpCode)\n";
        echo "   📄 Response: $response\n\n";
        return false;
    }
}

// Test Laravel routes
function testLaravelRoutes() {
    echo "🔍 Testing Laravel Integration...\n\n";
    
    $baseUrl = 'http://127.0.0.1:8000'; // Default Laravel dev server
    
    // Test Laravel scan start route
    echo "1. Testing Laravel scan start route...\n";
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $baseUrl . '/scan/start');
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_HTTPHEADER, [
        'Content-Type: application/json',
        'Accept: application/json'
    ]);
    curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode([
        'target' => '127.0.0.1'
    ]));
    curl_setopt($ch, CURLOPT_TIMEOUT, 10);
    
    $response = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    
    if ($httpCode == 201) {
        echo "   ✅ Laravel scan route working\n";
        $data = json_decode($response, true);
        echo "   📝 Job ID: " . ($data['job_id'] ?? 'N/A') . "\n\n";
    } else {
        echo "   ❌ Laravel scan route failed (HTTP: $httpCode)\n";
        echo "   📄 Response: $response\n";
        echo "   🔧 Make sure Laravel server is running: php artisan serve\n\n";
    }
}

// Main execution
echo "=== MQTT Scanner Integration Test ===\n\n";

$jobId = testFlaskConnection();
if ($jobId) {
    echo "✅ Flask integration is working!\n\n";
    testLaravelRoutes();
    echo "🎉 All tests completed!\n";
    echo "🌐 Visit: http://127.0.0.1:8000/dashboard to use the web interface\n";
} else {
    echo "❌ Flask integration failed. Please check Flask setup.\n";
    echo "🔧 Make sure to:\n";
    echo "   1. cd mqtt-scanner\n";
    echo "   2. python app.py\n";
    echo "   3. Check if port 5000 is available\n";
}