<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

/**
 * Migration 2/2 — Adds two reserved columns.
 *
 * masked_image_id   → FK to media table (nullable) — intended for a face-masked/anonymised version
 * modified_image_id → FK to media table (nullable) — intended for post-processed/edited version
 *
 * Both are currently unused in the active generation flow. Added for future
 * preprocessing pipeline (e.g., face masking before sending to Gemini).
 */
class AddMoreColumnsOnEmployeeAiProfessionalProfileImagesTable extends Migration
{
    public function up()
    {
        Schema::table('employee_ai_professional_profile_images', function (Blueprint $table) {
            $table->foreignId('masked_image_id')->nullable();
            $table->foreignId('modified_image_id')->nullable();
        });
    }

    public function down()
    {
        Schema::table('employee_ai_professional_profile_images', function (Blueprint $table) {
            $table->dropColumn('masked_image_id');
            $table->dropColumn('modified_image_id');
        });
    }
}
