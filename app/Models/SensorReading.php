<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class SensorReading extends Model
{
    protected $fillable = [
        'device',
        'topic',
        'temperature',
        'humidity',
        'ldr_raw',
        'ldr_pct',
        'pir',
        'raw_payload'
    ];

    protected $casts = [
        'temperature' => 'decimal:2',
        'humidity' => 'decimal:2',
        'ldr_pct' => 'decimal:2',
        'pir' => 'boolean',
        'raw_payload' => 'array',
        'created_at' => 'datetime',
        'updated_at' => 'datetime',
    ];
}
