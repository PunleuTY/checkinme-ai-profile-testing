<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

/**
 * Migration 1/2 — Initial table creation.
 *
 * Core columns:
 *   employee_id       → FK to employees table
 *   original_image_id → FK to media table (the photo the employee uploaded)
 *   data              → JSON array of generated Media IDs (appended on each generate call)
 *
 * addCreateUpdateDeleteBy() is a custom macro that adds:
 *   created_by, updated_by, deleted_by (nullable FK to users)
 */
class CreateEmployeeAiProfessionalProfileImagesTable extends Migration
{
    public function up()
    {
        Schema::create('employee_ai_professional_profile_images', function (Blueprint $table) {
            $table->id();
            $table->foreignId('employee_id');
            $table->foreignId('original_image_id')->nullable();
            $table->longText('data')->nullable();  // JSON array of Media IDs
            $table->addCreateUpdateDeleteBy();
            $table->softDeletes();
            $table->timestamps();
        });
    }

    public function down()
    {
        Schema::dropIfExists('employee_ai_professional_profile_images');
    }
}
