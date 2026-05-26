<?php

/**
 * ============================================================
 * AI Profile Routes (extracted from routes/employee.api.php)
 * ============================================================
 * All routes sit inside a route group with:
 *   prefix     → 'profile'
 *   namespace  → 'App\Http\Controllers\Employee'
 *   middleware → 'auth.can_empty:employees'  (allows unauthenticated but sets employee if token present)
 *
 * Full route prefix in production: /api/employee/profile/...
 * ============================================================
 *
 * Flow order:
 *   1. POST  validate_image          → upload & store source photo
 *   2. GET   ai_professional_attempts → check monthly quota
 *   3. POST  generate/professional_suit → generate AI images via Gemini
 *   4. GET   history                  → list all generated images
 *   5. POST  upload_ai_generated_image/{id}   → set profile pic to AI image
 *   6. POST  upload_original_profile_image/{id} → set profile pic back to original
 */

Route::group(['prefix' => 'profile', 'namespace' => 'Employee'], function () {

    // Step 1 — Validate & store the employee's source photo
    Route::post('/ai_professional_profile/validate_image', 'ProfileController@validateAiProfileImage')
        ->middleware('auth.can_empty:employees');

    // Step 2 — Check attempt quota (3 images/month soft cap)
    Route::get('/ai_professional_attempts', 'ProfileController@getAiProfessionalAttempts')
        ->middleware('auth.can_empty:employees');

    // Step 3 — Trigger Gemini generation
    //   Params: limit (int, default 4), offset (int, default 0), gender ('male'|'female')
    Route::post('/generate/professional_suit', 'ProfileController@generateProfessionalSuit')
        ->middleware('auth.can_empty:employees');

    // Step 4 — Retrieve full generation history
    Route::get('/ai_professional_profile/history', 'ProfileController@getAiProfessionalProfileHistory')
        ->middleware('auth.can_empty:employees');

    // Step 5a — Apply a chosen AI-generated image as profile picture
    Route::post('/upload_ai_generated_image/{id}', 'ProfileController@uploadAiGeneratedImage')
        ->middleware('auth.can_empty:employees');

    // Step 5b — Revert to the original uploaded image as profile picture
    Route::post('/upload_original_profile_image/{id}', 'ProfileController@UploadOriginalProfileImage')
        ->middleware('auth.can_empty:employees');
});
