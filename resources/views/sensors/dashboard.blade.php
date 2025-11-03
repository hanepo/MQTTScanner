<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="csrf-token" content="{{ csrf_token() }}">
    <title>ESP32 Sensor Monitoring - MQTT Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }
        .status-connected {
            animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }
    </style>
</head>
<body class="bg-gray-50 min-h-screen">
    <!-- Navigation Bar -->
    <nav class="bg-white shadow-sm border-b border-gray-200">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between items-center h-16">
                <div class="flex items-center">
                    <svg class="w-8 h-8 text-blue-600 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
                    </svg>
                    <span class="text-xl font-bold text-gray-900">MQTT Sensor Monitoring</span>
                </div>
                <div class="flex items-center space-x-4">
                    <a href="/dashboard" class="text-sm text-gray-700 hover:text-blue-600 transition">
                        Scanner Dashboard
                    </a>
                </div>
            </div>
        </div>
    </nav>

    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">

        <!-- Page Header -->
        <div class="mb-6">
            <div class="bg-white shadow-sm rounded-lg border-l-4 border-blue-500 p-6">
                <div class="flex justify-between items-start">
                    <div>
                        <h1 class="text-2xl font-bold text-gray-900 mb-1">ESP32 Multi-Sensor Monitor (Secure MQTT)</h1>
                        <p class="text-sm text-gray-600">Real-time MQTT broker scanning and sensor data monitoring</p>
                        <div class="mt-3 flex items-center space-x-4 text-sm text-gray-500">
                            <div class="flex items-center">
                                <svg class="w-4 h-4 text-green-600 mr-1" fill="currentColor" viewBox="0 0 20 20">
                                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
                                </svg>
                                <span id="total-readings">{{ $stats['total_readings'] ?? 0 }} results found</span>
                            </div>
                            <div class="flex items-center">
                                <svg class="w-4 h-4 text-yellow-600 mr-1" fill="currentColor" viewBox="0 0 20 20">
                                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clip-rule="evenodd"></path>
                                </svg>
                                <span id="last-updated">Last updated: {{ $latestReading ? $latestReading->created_at->format('M j, Y g:i A') : 'Never' }}</span>
                            </div>
                        </div>
                    </div>
                    <div id="connection-status" class="flex items-center space-x-2 px-4 py-2 rounded-lg">
                        <div id="status-dot" class="w-3 h-3 rounded-full"></div>
                        <span id="status-text" class="font-medium text-sm">Checking...</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Statistics Cards - 4 Boxes -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div class="bg-white rounded-lg shadow-sm p-4">
                <div class="flex items-center">
                    <div class="p-2 bg-green-100 rounded-lg">
                        <svg class="w-6 h-6 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                            <path d="M9 6a3 3 0 11-6 0 3 3 0 016 0zM17 6a3 3 0 11-6 0 3 3 0 016 0zM12.93 17c.046-.327.07-.66.07-1a6.97 6.97 0 00-1.5-4.33A5 5 0 0119 16v1h-6.07zM6 11a5 5 0 015 5v1H1v-1a5 5 0 015-5z"></path>
                        </svg>
                    </div>
                    <div class="ml-4">
                        <p class="text-xs font-medium text-gray-600">Temperature</p>
                        <p id="stat-temp" class="text-xl font-semibold text-gray-900">{{ $latestReading ? number_format($latestReading->temperature, 1) . '°C' : '--' }}</p>
                    </div>
                </div>
            </div>

            <div class="bg-white rounded-lg shadow-sm p-4">
                <div class="flex items-center">
                    <div class="p-2 bg-blue-100 rounded-lg">
                        <svg class="w-6 h-6 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z" clip-rule="evenodd"></path>
                        </svg>
                    </div>
                    <div class="ml-4">
                        <p class="text-xs font-medium text-gray-600">Humidity</p>
                        <p id="stat-hum" class="text-xl font-semibold text-gray-900">{{ $latestReading ? number_format($latestReading->humidity, 1) . '%' : '--' }}</p>
                    </div>
                </div>
            </div>

            <div class="bg-white rounded-lg shadow-sm p-4">
                <div class="flex items-center">
                    <div class="p-2 bg-yellow-100 rounded-lg">
                        <svg class="w-6 h-6 text-yellow-600" fill="currentColor" viewBox="0 0 20 20">
                            <path d="M11 3a1 1 0 10-2 0v1a1 1 0 102 0V3zM15.657 5.757a1 1 0 00-1.414-1.414l-.707.707a1 1 0 001.414 1.414l.707-.707zM18 10a1 1 0 01-1 1h-1a1 1 0 110-2h1a1 1 0 011 1zM5.05 6.464A1 1 0 106.464 5.05l-.707-.707a1 1 0 00-1.414 1.414l.707.707zM5 10a1 1 0 01-1 1H3a1 1 0 110-2h1a1 1 0 011 1zM8 16v-1h4v1a2 2 0 11-4 0zM12 14c.015-.34.208-.646.477-.859a4 4 0 10-4.954 0c.27.213.462.519.476.859h4.002z"></path>
                        </svg>
                    </div>
                    <div class="ml-4">
                        <p class="text-xs font-medium text-gray-600">Light Level</p>
                        <p id="stat-light" class="text-xl font-semibold text-gray-900">{{ $latestReading ? number_format($latestReading->ldr_pct, 1) . '%' : '--' }}</p>
                    </div>
                </div>
            </div>

            <div class="bg-white rounded-lg shadow-sm p-4">
                <div class="flex items-center">
                    <div class="p-2 bg-purple-100 rounded-lg">
                        <svg class="w-6 h-6 text-purple-600" fill="currentColor" viewBox="0 0 20 20">
                            <path d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z"></path>
                        </svg>
                    </div>
                    <div class="ml-4">
                        <p class="text-xs font-medium text-gray-600">Motion</p>
                        <p id="stat-motion" class="text-xl font-semibold text-gray-900">{{ $latestReading && $latestReading->pir ? 'DETECTED' : 'No Motion' }}</p>
                    </div>
                </div>
            </div>
        </div>

        <!-- Sensor Readings Table -->
        <div class="bg-white shadow-sm rounded-lg overflow-hidden mb-6">
            <div class="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
                <div>
                    <h2 class="text-lg font-semibold text-gray-900">MQTT Sensor Readings</h2>
                    <p class="text-sm text-gray-600 mt-1">Real-time sensor data from ESP32 devices</p>
                </div>
                <div class="flex space-x-2">
                    <button id="securityDetailsBtn" class="inline-flex items-center px-4 py-2 bg-purple-600 text-white text-sm font-medium rounded-md hover:bg-purple-700 transition-colors">
                        <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"></path>
                        </svg>
                        Security Details
                    </button>
                    <button id="refreshBtn" class="inline-flex items-center px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 transition-colors">
                        <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
                        </svg>
                        Refresh Data
                    </button>
                </div>
            </div>

            <div class="overflow-x-auto">
                <table class="min-w-full divide-y divide-gray-200">
                    <thead class="bg-gray-50">
                        <tr>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">TEMPERATURE</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">HUMIDITY</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">LIGHT (RAW)</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">LIGHT (%)</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">MOTION</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">TIMESTAMP</th>
                        </tr>
                    </thead>
                    <tbody id="sensorTableBody" class="bg-white divide-y divide-gray-200">
                        @if($latestReading)
                            <tr class="hover:bg-gray-50 transition-colors">
                                <td class="px-6 py-4 whitespace-nowrap">
                                    <div class="flex items-center">
                                        <svg class="w-5 h-5 text-orange-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                                            <path d="M10 2a6 6 0 00-6 6v3.586l-.707.707A1 1 0 004 14h12a1 1 0 00.707-1.707L16 11.586V8a6 6 0 00-6-6zM10 18a3 3 0 01-3-3h6a3 3 0 01-3 3z"/>
                                        </svg>
                                        <span class="text-sm font-medium text-gray-900">{{ number_format($latestReading->temperature, 1) }}°C</span>
                                    </div>
                                </td>
                                <td class="px-6 py-4 whitespace-nowrap">
                                    <div class="flex items-center">
                                        <svg class="w-5 h-5 text-blue-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                                            <path fill-rule="evenodd" d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z" clip-rule="evenodd"></path>
                                        </svg>
                                        <span class="text-sm font-medium text-gray-900">{{ number_format($latestReading->humidity, 1) }}%</span>
                                    </div>
                                </td>
                                <td class="px-6 py-4 whitespace-nowrap">
                                    <span class="text-sm text-gray-700">{{ $latestReading->ldr_raw }}</span>
                                </td>
                                <td class="px-6 py-4 whitespace-nowrap">
                                    <div class="flex items-center">
                                        <div class="w-16 bg-gray-200 rounded-full h-2 mr-2">
                                            <div class="bg-yellow-500 h-2 rounded-full" style="width: {{ $latestReading->ldr_pct }}%"></div>
                                        </div>
                                        <span class="text-sm font-medium text-gray-900">{{ number_format($latestReading->ldr_pct, 1) }}%</span>
                                    </div>
                                </td>
                                <td class="px-6 py-4 whitespace-nowrap">
                                    @if($latestReading->pir)
                                        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                                            <svg class="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                                                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM7 9a1 1 0 000 2h6a1 1 0 100-2H7z" clip-rule="evenodd"></path>
                                            </svg>
                                            Motion
                                        </span>
                                    @else
                                        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                            <svg class="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                                                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
                                            </svg>
                                            No Motion
                                        </span>
                                    @endif
                                </td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                    {{ $latestReading->created_at->format('M j, Y g:i:s A') }}
                                </td>
                            </tr>
                        @else
                            <tr>
                                <td colspan="6" class="px-6 py-12 text-center">
                                    <div class="text-gray-500">
                                        <svg class="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"></path>
                                        </svg>
                                        <p class="text-sm font-medium">No sensor data available.</p>
                                        <p class="text-xs mt-1 text-gray-400">Start the MQTT subscriber to receive sensor readings.</p>
                                    </div>
                                </td>
                            </tr>
                        @endif
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Footer Info -->
        <div class="bg-white rounded-lg shadow-sm p-6">
            <div class="flex items-center justify-center text-sm text-gray-500">
                <svg class="w-4 h-4 mr-2 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"></path>
                </svg>
                Data from Flask Backend - MQTT Subscriber Service
            </div>
        </div>
    </div>

    <!-- Include Security Modal -->
    @include('sensors.security-modal')

    <script>
        // Auto-refresh connection status
        async function updateConnectionStatus() {
            try {
                const response = await fetch('/sensors/status');
                const data = await response.json();

                const statusDot = document.getElementById('status-dot');
                const statusText = document.getElementById('status-text');
                const connectionStatus = document.getElementById('connection-status');

                if (data.connected) {
                    statusDot.className = 'w-3 h-3 rounded-full bg-green-500 status-connected';
                    statusText.textContent = 'Connected';
                    connectionStatus.className = 'flex items-center space-x-2 px-4 py-2 rounded-lg bg-green-100 text-green-800';
                } else {
                    statusDot.className = 'w-3 h-3 rounded-full bg-red-500';
                    statusText.textContent = 'Disconnected';
                    connectionStatus.className = 'flex items-center space-x-2 px-4 py-2 rounded-lg bg-red-100 text-red-800';
                }
            } catch (error) {
                console.error('Error checking connection status:', error);
            }
        }

        // Auto-refresh latest sensor data
        async function updateLatestData() {
            try {
                const response = await fetch('/sensors/latest');
                const result = await response.json();

                if (result.status === 'ok' && result.data) {
                    const data = result.data;

                    // Safely parse numeric values
                    const temp = parseFloat(data.temperature);
                    const hum = parseFloat(data.humidity);
                    const light = parseFloat(data.ldr_pct);

                    // Update stat boxes
                    document.getElementById('stat-temp').textContent = !isNaN(temp) ? temp.toFixed(1) + '°C' : '--';
                    document.getElementById('stat-hum').textContent = !isNaN(hum) ? hum.toFixed(1) + '%' : '--';
                    document.getElementById('stat-light').textContent = !isNaN(light) ? light.toFixed(1) + '%' : '--';
                    document.getElementById('stat-motion').textContent = data.pir ? 'DETECTED' : 'No Motion';

                    // Update table row
                    const tbody = document.getElementById('sensorTableBody');
                    const tempIcon = `<svg class="w-5 h-5 text-orange-500 mr-2" fill="currentColor" viewBox="0 0 20 20"><path d="M10 2a6 6 0 00-6 6v3.586l-.707.707A1 1 0 004 14h12a1 1 0 00.707-1.707L16 11.586V8a6 6 0 00-6-6zM10 18a3 3 0 01-3-3h6a3 3 0 01-3 3z"/></svg>`;
                    const humIcon = `<svg class="w-5 h-5 text-blue-500 mr-2" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z" clip-rule="evenodd"></path></svg>`;

                    const motionBadge = data.pir
                        ? '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800"><svg class="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM7 9a1 1 0 000 2h6a1 1 0 100-2H7z" clip-rule="evenodd"></path></svg>Motion</span>'
                        : '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800"><svg class="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path></svg>No Motion</span>';

                    const timestamp = new Date(data.timestamp).toLocaleString('en-US', {
                        month: 'short',
                        day: 'numeric',
                        year: 'numeric',
                        hour: 'numeric',
                        minute: '2-digit',
                        second: '2-digit',
                        hour12: true
                    });

                    tbody.innerHTML = `
                        <tr class="hover:bg-gray-50 transition-colors">
                            <td class="px-6 py-4 whitespace-nowrap">
                                <div class="flex items-center">
                                    ${tempIcon}
                                    <span class="text-sm font-medium text-gray-900">${!isNaN(temp) ? temp.toFixed(1) + '°C' : '--'}</span>
                                </div>
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap">
                                <div class="flex items-center">
                                    ${humIcon}
                                    <span class="text-sm font-medium text-gray-900">${!isNaN(hum) ? hum.toFixed(1) + '%' : '--'}</span>
                                </div>
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap">
                                <span class="text-sm text-gray-700">${data.ldr_raw || '--'}</span>
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap">
                                <div class="flex items-center">
                                    <div class="w-16 bg-gray-200 rounded-full h-2 mr-2">
                                        <div class="bg-yellow-500 h-2 rounded-full" style="width: ${!isNaN(light) ? light : 0}%"></div>
                                    </div>
                                    <span class="text-sm font-medium text-gray-900">${!isNaN(light) ? light.toFixed(1) + '%' : '--'}</span>
                                </div>
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap">
                                ${motionBadge}
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                ${timestamp}
                            </td>
                        </tr>
                    `;

                    // Update last updated text
                    document.getElementById('last-updated').textContent = 'Last updated: ' + timestamp;
                }
            } catch (error) {
                console.error('Error fetching latest data:', error);
            }
        }

        // Refresh button handler
        document.getElementById('refreshBtn').addEventListener('click', function() {
            const btn = this;
            const icon = btn.querySelector('svg');

            // Add spin animation
            icon.classList.add('animate-spin');
            btn.disabled = true;

            // Update data
            Promise.all([updateConnectionStatus(), updateLatestData()])
                .finally(() => {
                    setTimeout(() => {
                        icon.classList.remove('animate-spin');
                        btn.disabled = false;
                    }, 500);
                });
        });

        // Auto-refresh intervals
        setInterval(updateConnectionStatus, 5000); // Check connection every 5 seconds
        setInterval(updateLatestData, 3000); // Update sensor data every 3 seconds

        // Initial updates
        updateConnectionStatus();
        updateLatestData();
    </script>
</body>
</html>
