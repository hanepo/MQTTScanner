<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;
use App\Services\MqttSensorService;

class ScanController extends Controller
{
    /**
     * Base URL for the Python Flask scanner API
     */
    private $scannerApiUrl = 'http://127.0.0.1:5000';

    /**
     * API key for authenticating with Flask API
     */
    private $apiKey;

    public function __construct()
    {
        $this->apiKey = env('FLASK_API_KEY', 'my-very-secret-flask-key-CHANGEME');
    }

    /**
     * Start a new scan job
     *
     * POST /scan/start
     * Body: {"target": "192.168.100.0/24", "creds": {"user": "...", "pass": "..."}}
     */
    public function start(Request $request)
    {
        $validated = $request->validate([
            'target' => 'required|string',
            'listen_duration' => 'sometimes|integer|min:1|max:10',
            'capture_all_topics' => 'sometimes|boolean',
            'creds' => 'sometimes|array',
            'creds.user' => 'sometimes|string',
            'creds.pass' => 'sometimes|string',
        ]);

        try {
            Log::info('Starting direct MQTT scan', [
                'target' => $validated['target'],
                'has_credentials' => isset($validated['creds']) && !empty($validated['creds']['user'])
            ]);

            // Use MqttSensorService for direct MQTT scanning
            $sensorService = new MqttSensorService();
            
            // Set credentials if provided, otherwise use null for anonymous
            if (isset($validated['creds']) && !empty($validated['creds']['user'])) {
                $sensorService->setCredentials(
                    $validated['creds']['user'],
                    $validated['creds']['pass'] ?? null
                );
                Log::info('Scanning with authentication', ['username' => $validated['creds']['user']]);
            } else {
                $sensorService->setCredentials(null, null);
                Log::info('Scanning in anonymous mode (no credentials)');
            }

            // Capture latest sensor data from both brokers
            $readings = $sensorService->captureLatestSensorData(
                true,  // scan secure (will fail if no credentials and auth required)
                true,  // scan insecure (should work without credentials)
                true   // force fresh
            );

            // Parse DHT11 specific data
            $dht11Data = $sensorService->parseDht11Data($readings);

            // Generate a simple job ID for compatibility with frontend
            $jobId = 'mqtt-scan-' . uniqid();

            Log::info('Direct MQTT scan completed', [
                'job_id' => $jobId,
                'secure_count' => count($readings['secure'] ?? []),
                'insecure_count' => count($readings['insecure'] ?? []),
                'secure_error' => isset($readings['secure']['error']) ? $readings['secure']['error'] : null
            ]);

            // Return response in format expected by frontend
            return response()->json([
                'job_id' => $jobId,
                'status' => 'completed',  // Mark as immediately completed
                'message' => 'MQTT scan completed',
                'progress' => 100,
                'results' => [
                    'readings' => $readings,
                    'dht11' => $dht11Data,
                    'brokers' => $this->formatBrokerResults($readings, $dht11Data)
                ]
            ], 201);

        } catch (\Exception $e) {
            Log::error('MQTT scan error: ' . $e->getMessage());
            return response()->json([
                'error' => 'Failed to scan MQTT brokers',
                'message' => $e->getMessage()
            ], 500);
        }
    }

    /**
     * Format broker results for display in scan results table
     */
    private function formatBrokerResults($readings, $dht11Data)
    {
        $results = [];

        // Secure broker (8883)
        if (!empty($readings['secure']) && !isset($readings['secure']['error'])) {
            // Deduplicate by topic - keep only the latest message per topic
            $secureTopicsMap = [];
            foreach ($readings['secure'] as $reading) {
                if (isset($reading['topic']) && isset($reading['message'])) {
                    // Use topic as key to automatically deduplicate
                    $secureTopicsMap[$reading['topic']] = [
                        'topic' => $reading['topic'],
                        'message' => $reading['message'],
                        'publisher' => 'ESP32',
                        'subscriber' => 'Dashboard/Web',
                        'retained' => true
                    ];
                }
            }

            // Create separate entries for each unique sensor topic on secure broker
            foreach ($secureTopicsMap as $topicData) {
                $sensorType = $this->identifySensorType($topicData['topic'], $topicData['message']);
                
                $results[] = [
                    'ip' => '127.0.0.1',
                    'port' => 8883,
                    'result' => 'connected',
                    'classification' => 'open_or_auth_ok',
                    'tls' => true,
                    'tls_details' => [
                        'enabled' => true,
                        'version' => 'TLS 1.2/1.3',
                        'encryption' => 'AES-256-GCM',
                        'certificate' => 'Self-signed CA',
                        'authentication' => 'Username/Password (testuser)'
                    ],
                    'publishers' => [[
                        'topic' => $topicData['topic'],
                        'publisher' => $topicData['publisher'],
                        'payload_sample' => json_encode($topicData['message'])
                    ]],
                    'subscribers' => [[
                        'client' => $topicData['subscriber'],
                        'subscribed_to' => $topicData['topic']
                    ]],
                    'sensor_type' => $sensorType['type'],
                    'sensor_data' => $sensorType['data'],
                    'timestamp' => now()->toIso8601String()
                ];
            }
        }

        // Insecure broker (1883) - check for PIR sensor
        if (!empty($readings['insecure']) && !isset($readings['insecure']['error'])) {
            // Deduplicate by topic - keep only the latest message per topic
            $insecureTopicsMap = [];
            foreach ($readings['insecure'] as $reading) {
                if (isset($reading['topic']) && isset($reading['message'])) {
                    // Use topic as key to automatically deduplicate
                    $insecureTopicsMap[$reading['topic']] = [
                        'topic' => $reading['topic'],
                        'message' => $reading['message'],
                        'publisher' => 'ESP32',
                        'subscriber' => 'Dashboard/Web',
                        'retained' => true
                    ];
                }
            }

            // Create entries for each unique insecure broker sensor
            foreach ($insecureTopicsMap as $topicData) {
                $sensorType = $this->identifySensorType($topicData['topic'], $topicData['message']);
                
                $results[] = [
                    'ip' => '127.0.0.1',
                    'port' => 1883,
                    'result' => 'connected',
                    'classification' => 'open_or_auth_ok',
                    'tls' => false,
                    'tls_details' => [
                        'enabled' => false,
                        'version' => 'None',
                        'encryption' => 'Plain text (unencrypted)',
                        'warning' => 'Data transmitted in plain text - not secure!'
                    ],
                    'publishers' => [[
                        'topic' => $topicData['topic'],
                        'publisher' => $topicData['publisher'],
                        'payload_sample' => json_encode($topicData['message'])
                    ]],
                    'subscribers' => [[
                        'client' => $topicData['subscriber'],
                        'subscribed_to' => $topicData['topic']
                    ]],
                    'sensor_type' => $sensorType['type'],
                    'sensor_data' => $sensorType['data'],
                    'timestamp' => now()->toIso8601String()
                ];
            }
        }

        return $results;
    }

    /**
     * Identify sensor type from topic and message
     */
    private function identifySensorType($topic, $message)
    {
        // DHT sensor (temperature + humidity)
        if (strpos($topic, 'dht') !== false || (isset($message['temp_c']) && isset($message['hum_pct']))) {
            return [
                'type' => 'DHT11 (Temperature & Humidity)',
                'data' => [
                    'temperature' => $message['temp_c'] ?? null,
                    'humidity' => $message['hum_pct'] ?? null,
                    'unit_temp' => '°C',
                    'unit_humidity' => '%'
                ]
            ];
        }
        
        // LDR sensor (light)
        if (strpos($topic, 'ldr') !== false || isset($message['ldr_pct'])) {
            return [
                'type' => 'LDR (Light Sensor)',
                'data' => [
                    'light_percent' => $message['ldr_pct'] ?? null,
                    'light_raw' => $message['ldr_raw'] ?? null,
                    'unit' => '%'
                ]
            ];
        }
        
        // PIR sensor (motion)
        if (strpos($topic, 'pir') !== false || isset($message['pir'])) {
            $pirValue = $message['pir'] ?? 0;
            return [
                'type' => 'PIR (Motion Sensor)',
                'data' => [
                    'motion' => $pirValue == 1 ? 'DETECTED' : 'None',
                    'motion_value' => $pirValue
                ]
            ];
        }

        // Default/unknown
        return [
            'type' => 'Unknown Sensor',
            'data' => $message
        ];
    }

    /**
     * Get scan job status
     *
     * GET /scan/status/{job_id}
     */
    public function status($jobId)
    {
        try {
            Log::debug('Getting scan status', ['job_id' => $jobId]);

            $response = Http::withHeaders([
                'X-API-Key' => $this->apiKey,
            ])->get($this->scannerApiUrl . "/api/scan/{$jobId}/status");

            if ($response->successful()) {
                return response()->json($response->json());
            }

            Log::error('Status check failed', [
                'job_id' => $jobId,
                'status' => $response->status(),
                'body' => $response->body()
            ]);

            return response()->json([
                'error' => 'Failed to get scan status',
                'details' => $response->json()
            ], $response->status());

        } catch (\Exception $e) {
            Log::error('Scan status error: ' . $e->getMessage());
            return response()->json([
                'error' => 'Failed to communicate with scanner API',
                'message' => $e->getMessage()
            ], 500);
        }
    }

    /**
     * Get scan job results
     *
     * GET /scan/results/{job_id}
     */
    public function results($jobId)
    {
        try {
            Log::debug('Getting scan results', ['job_id' => $jobId]);

            $response = Http::withHeaders([
                'X-API-Key' => $this->apiKey,
            ])->get($this->scannerApiUrl . "/api/scan/{$jobId}/results");

            Log::debug('Results response', [
                'job_id' => $jobId,
                'status' => $response->status(),
                'body_preview' => substr($response->body(), 0, 500)
            ]);

            if ($response->successful()) {
                return response()->json($response->json());
            }

            Log::error('Results fetch failed', [
                'job_id' => $jobId,
                'status' => $response->status(),
                'body' => $response->body()
            ]);

            return response()->json([
                'error' => 'Failed to get scan results',
                'details' => $response->json()
            ], $response->status());

        } catch (\Exception $e) {
            Log::error('Scan results error: ' . $e->getMessage());
            return response()->json([
                'error' => 'Failed to communicate with scanner API',
                'message' => $e->getMessage()
            ], 500);
        }
    }

    /**
     * Download scan results as CSV
     *
     * GET /scan/download/{job_id}
     */
    public function download($jobId)
    {
        try {
            $response = Http::withHeaders([
                'X-API-Key' => $this->apiKey,
            ])->get($this->scannerApiUrl . "/api/scan/{$jobId}/download");

            if ($response->successful()) {
                return response($response->body())
                    ->header('Content-Type', 'text/csv')
                    ->header('Content-Disposition', "attachment; filename=mqtt_scan_{$jobId}.csv");
            }

            return response()->json([
                'error' => 'Failed to download scan results',
                'details' => $response->json()
            ], $response->status());

        } catch (\Exception $e) {
            Log::error('Scan download error: ' . $e->getMessage());
            return response()->json([
                'error' => 'Failed to communicate with scanner API',
                'message' => $e->getMessage()
            ], 500);
        }
    }
}
