<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Run the migrations.
     */
    public function up(): void
    {
        Schema::create('sensor_readings', function (Blueprint $table) {
            $table->id();
            $table->string('device')->default('esp32-multi-sensor');
            $table->string('topic')->index();
            $table->decimal('temperature', 5, 2)->nullable();
            $table->decimal('humidity', 5, 2)->nullable();
            $table->integer('ldr_raw')->nullable();
            $table->decimal('ldr_pct', 5, 2)->nullable();
            $table->boolean('pir')->default(false);
            $table->json('raw_payload')->nullable();
            $table->timestamps();

            // Index for efficient querying
            $table->index('created_at');
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('sensor_readings');
    }
};
