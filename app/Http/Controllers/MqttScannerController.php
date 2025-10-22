<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Http; // Laravel HTTP client
use Illuminate\Support\Facades\Log;

class MqttScannerController extends Controller
{
    // Show dashboard (server-side reads last results if exists)
    public function index()
    {
        // Optionally, you can request /mqtt/results server-side and pass to view
        $scans = [];
        // call local Laravel route to fetch results via Flask (below)
        try {
            $res = Http::get(route('mqtt.results.endpoint')); // calls internal route
            if ($res->ok()) {
                $scans = $res->json();
            }
        } catch (\Exception $e) {
            Log::error('Fetch MQTT results error: ' . $e->getMessage());
        }

        return view('dashboard', compact('scans'));
    }

    // Laravel server-side endpoint: calls Flask /api/scan
    public function scan(Request $request)
    {
        $target = $request->input('target', '127.0.0.1');
        $creds  = $request->input('creds', null); // optional array {user, pass}

        $flaskBase = env('FLASK_BASE', 'http://127.0.0.1:5000');
        $apiKey = env('FLASK_API_KEY', 'my-very-secret-flask-key-CHANGEME');

        try {
            $response = Http::withHeaders([
                'X-API-KEY' => $apiKey,
            ])->post($flaskBase . '/api/scan', [
                'target' => $target,
                'creds'  => $creds,
            ]);

            return response($response->body(), $response->status())
                   ->header('Content-Type', $response->header('Content-Type', 'application/json'));
        } catch (\Exception $e) {
            return response()->json(['error' => 'Failed to reach scanner: '.$e->getMessage()], 500);
        }
    }

    // Laravel server-side endpoint: calls Flask /api/results
    public function results()
    {
        $flaskBase = env('FLASK_BASE', 'http://127.0.0.1:5000');
        $apiKey = env('FLASK_API_KEY', 'my-very-secret-flask-key-CHANGEME');

        try {
            $response = Http::withHeaders([
                'X-API-KEY' => $apiKey,
            ])->get($flaskBase . '/api/results');

            return response($response->body(), $response->status())
                   ->header('Content-Type', $response->header('Content-Type', 'application/json'));
        } catch (\Exception $e) {
            return response()->json(['error' => 'Failed to fetch results: '.$e->getMessage()], 500);
        }
    }
}
