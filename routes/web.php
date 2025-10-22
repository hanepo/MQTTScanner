<?php

use Illuminate\Support\Facades\Route;
use App\Http\Controllers\MqttScannerController;

// Redirect root (/) to dashboard page
Route::get('/', function () {
    return redirect('/dashboard');
});

// MQTT Scanner Dashboard Route
Route::get('/dashboard', [MqttScannerController::class, 'index'])->name('mqtt.dashboard');

// MQTT Scanner API Routes
Route::post('/mqtt/scan', [MqttScannerController::class, 'scan'])->name('mqtt.scan');
Route::get('/mqtt/results', [MqttScannerController::class, 'results'])->name('mqtt.results.endpoint');
