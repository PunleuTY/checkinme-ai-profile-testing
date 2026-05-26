<?php

/**
 * ============================================================
 * AI Config — professional_profile block only
 * ============================================================
 * The full config/ai.php also contains: face_recognition,
 * speech_to_text, ai_assistant, aws.rekognition, google.vision.
 * Only the professional_profile block is relevant here.
 *
 * Note: The Python microservice URLs below are for the OLD flow
 * (AIService.php). The current Gemini flow (AiProfileGenerateService)
 * uses config('services.google.key') from config/services.php instead.
 * ============================================================
 */

return [

    /**
     * Legacy Python microservice (AIService.php — old flow, not used for Gemini generation).
     * Kept here for reference only.
     *
     * Env vars:
     *   AI_PROFESSIONAL_PROFILE_URL      → base URL of the Python server
     *   AI_PROFESSIONAL_PROFILE_GENERATE → /generate-image endpoint
     *   AI_PROFESSIONAL_PROFILE_VALIDATE → /validate-image endpoint
     *   AI_PROFESSIONAL_PROFILE_DELETE   → /delete-image endpoint
     */
    'professional_profile' => [
        'base_url'  => env('AI_PROFESSIONAL_PROFILE_URL', 'http://143.198.213.82'),
        'endpoints' => [
            'generate' => env('AI_PROFESSIONAL_PROFILE_GENERATE', '/generate-image'),
            'validate' => env('AI_PROFESSIONAL_PROFILE_VALIDATE', '/validate-image'),
            'delete'   => env('AI_PROFESSIONAL_PROFILE_DELETE', '/delete-image'),
        ],
    ],

    /**
     * Gemini API key is NOT here — it lives in config/services.php:
     *   config('services.google.key')  →  env('GOOGLE_API_KEY')
     *
     * Gemini endpoint used by AiProfileGenerateService:
     *   https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent
     */

];
