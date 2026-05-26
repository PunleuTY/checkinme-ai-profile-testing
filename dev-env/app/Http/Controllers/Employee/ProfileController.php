<?php

namespace App\Http\Controllers\Employee;

use App\Models\EmployeeAiProfessionalProfileImage;
use App\Models\Media;
use App\Services\AI\AiProfileGenerateService;
use App\Http\Controllers\Controller;
use Illuminate\Http\Request;

/**
 * ============================================================
 * CONTEXT FILE — AI Profile methods only (read reference)
 * ============================================================
 * Stripped to the 6 AI profile methods from the full
 * ProfileController. All unrelated methods (updateLocation,
 * update, card, eNameCard, etc.) are excluded.
 *
 * Stubs used below (not replicated here):
 *   MediaHelper::storeImageAndGet($base64)  → stores base64 image, returns Media model
 *   getBase64ImageDimensions($base64)        → returns [width, height]
 *   success($data)                           → Laravel JSON success helper
 *   fail($msg, $code)                        → Laravel JSON error helper
 * ============================================================
 */
class ProfileController extends Controller
{
    /**
     * STEP 1 — Upload & validate the source photo.
     *
     * - Checks monthly attempt limit via getAiProfessionalAttempts()
     * - Stores the uploaded image → Media record
     * - Creates EmployeeAiProfessionalProfileImage with original_image_id
     * - Returns image dimensions + attempt counts + is_show_button_generate flag
     *
     * Route: POST /ai_professional_profile/validate_image
     */
    public function validateAiProfileImage()
    {
        $employee = auth('employees')->user();

        $checkAttempts = $this->getAiProfessionalAttempts();
        if ($checkAttempts->status() != 200) {
            return json_decode($checkAttempts->content(), true);
        }

        $checkAttemptsContent = json_decode($checkAttempts->content(), true);

        if (!request('image')) {
            return fail('Image is required', 400);
        }

        // MediaHelper::storeImageAndGet() — stores base64 image, returns Media model
        $media = MediaHelper::storeImageAndGet(request('image'));

        EmployeeAiProfessionalProfileImage::create([
            'employee_id'       => $employee->id,
            'original_image_id' => $media->id ?? null,
        ]);

        $width  = getBase64ImageDimensions(request('image'))[0];
        $height = getBase64ImageDimensions(request('image'))[1];

        return success([
            'width'                => $width ?? null,
            'height'               => $height ?? null,
            'original_image'       => $media,
            'attempts'             => $checkAttemptsContent['data']['attempts'] ?? 0,
            'remaining_attempts'   => $checkAttemptsContent['data']['remaining_attempts'] ?? 0,
            'latest_item_attempts' => $checkAttemptsContent['data']['latest_item_attempts'] ?? 0,
            'is_show_button_generate' => $checkAttemptsContent['data']['remaining_attempts'] > 0
        ]);
    }

    /**
     * STEP 2 — Generate AI professional images.
     *
     * - Re-checks attempt limit (hard cap: 12 images per EmployeeAiProfessionalProfileImage record)
     * - Fetches original image from Media table
     * - Calls AiProfileGenerateService::generate() → array of base64 images
     * - Stores each base64 result as a new Media record
     * - Appends new Media IDs to EmployeeAiProfessionalProfileImage.data (JSON array)
     * - Returns generated images + updated attempt counts
     *
     * Route: POST /generate/professional_suit
     * Params: limit (default 4), offset (default 0), gender (default employee.gender)
     */
    public function generateProfessionalSuit()
    {
        $employee = auth('employees')->user();

        $checkAttempts = $this->getAiProfessionalAttempts();
        if ($checkAttempts->status() != 200) {
            return json_decode($checkAttempts->content(), true);
        }

        $checkAttemptsContent = json_decode($checkAttempts->content(), true);

        // Hard cap: max 12 images per single EmployeeAiProfessionalProfileImage session
        if ($checkAttemptsContent['data']['latest_item_attempts'] >= 12) {
            return abort(fail('You have reached the maximum attempts', 400));
        }

        $latestAiProfile = $employee->latestAiProfile;

        if (!$latestAiProfile) {
            abort(fail('Please validate your image first', 400));
        }

        $original_image = Media::where('id', $latestAiProfile->original_image_id)->first();

        $data = file_get_contents($original_image->url);
        $original_image_base64 = $original_image
            ? 'data:image/jpeg;base64,' . base64_encode($data)
            : null;

        [$width, $height] = getBase64ImageDimensions($original_image_base64);

        $limit  = request('limit') ?? 4;
        $offset = request('offset') ?? 0;
        $gender = request('gender') ?? $employee->gender;

        // ── Core AI call ─────────────────────────────────────────────────
        $geminiService = new AiProfileGenerateService();
        $results = $geminiService->generate($original_image->url, $gender, $limit, $offset);
        // ─────────────────────────────────────────────────────────────────

        $generated_media_id = [];
        $resultImages       = [];

        foreach ($results as $base64Image) {
            $media = MediaHelper::storeImageAndGet($base64Image);
            $generated_media_id[] = $media->id;
            $resultImages[] = [
                'id'        => $media->id,
                'url'       => $media->url,
                'file_name' => $media->file_name
            ];
        }

        // Persist generated Media IDs into the profile record's data JSON array
        $existingData = json_decode($latestAiProfile->data, true);
        $latestAiProfile->update([
            'data' => json_encode(
                $existingData ? array_merge($existingData, $generated_media_id) : $generated_media_id
            )
        ]);

        $countData         = count($generated_media_id);
        $attempts          = $checkAttemptsContent['data']['attempts'] + $countData;
        $remaining         = max(0, $checkAttemptsContent['data']['remaining_attempts'] - $countData);
        $latestItemAttempts = $checkAttemptsContent['data']['latest_item_attempts'] + $countData;

        return success((object) [
            'images'               => $resultImages,
            'width'                => $width,
            'height'               => $height,
            'attempts'             => $attempts,
            'remaining_attempts'   => $remaining,
            'latest_item_attempts' => $latestItemAttempts,
            'is_show_button_generate' => $remaining > 0
        ]);
    }

    /**
     * Attempt counter — enforces the 3 images/month soft cap.
     *
     * Logic:
     *   1. Collect all EmployeeAiProfessionalProfileImage records for the employee
     *   2. Flatten all Media IDs from their data JSON arrays
     *   3. Filter to only Media records created this calendar month
     *   4. Count = attempts used; 3 - count = remaining
     *
     * Route: GET /ai_professional_attempts
     */
    public function getAiProfessionalAttempts()
    {
        $employee = auth('employees')->user();

        $allAiProfiles   = $employee->aiProfiles()->orderByDesc('created_at')->get();
        $latestAiProfile = $employee->latestAiProfile()->first();

        // Count of images in the latest record (used for the per-record 12-image hard cap)
        $latestItemData     = $latestAiProfile && is_array(json_decode($latestAiProfile->data, true))
            ? json_decode($latestAiProfile->data, true)
            : [];
        $latestAttempts = count($latestItemData);

        // Flatten all Media IDs across all records
        $allMediaIds = [];
        foreach ($allAiProfiles as $profile) {
            $items = json_decode($profile->data, true);
            if (is_array($items)) {
                $allMediaIds = array_merge($allMediaIds, $items);
            }
        }

        // Filter to this month only (the actual monthly quota check)
        if (count($allMediaIds) > 0) {
            $allMediaIds = Media::whereIn('id', $allMediaIds)
                ->whereBetween('created_at', [now()->startOfMonth(), now()->endOfMonth()])
                ->select('id')
                ->get()
                ->pluck('id')
                ->toArray();
        }

        $countData = count($allMediaIds);

        return success([
            'attempts'             => $countData,
            'remaining_attempts'   => max(0, 3 - $countData),  // monthly soft cap = 3
            'latest_item_attempts' => $latestAttempts,
        ]);
    }

    /**
     * STEP 2b — History view.
     *
     * Returns all generated images across all EmployeeAiProfessionalProfileImage
     * records (not filtered by month), plus the latest original image.
     *
     * Route: GET /ai_professional_profile/history
     */
    public function getAiProfessionalProfileHistory()
    {
        $employee = auth('employees')->user();

        $checkAttempts = $this->getAiProfessionalAttempts();
        if ($checkAttempts->status() != 200) {
            return json_decode($checkAttempts->content(), true);
        }

        $allAiProfiles   = $employee->aiProfiles;
        $latestAiProfile = $employee->latestAiProfile;

        if ($allAiProfiles->isEmpty()) {
            return success([
                'data'                 => [],
                'original_image'       => null,
                'attempts'             => 0,
                'latest_item_attempts' => 0,
                'remaining_attempts'   => 3,
                'is_show_button_generate' => true
            ]);
        }

        // Flatten all Media IDs across all profile records
        $allMediaIds = [];
        foreach ($allAiProfiles as $profile) {
            if ($profile->data) {
                $allMediaIds = array_merge($allMediaIds, json_decode($profile->data, true));
            }
        }

        $mediaRecords = (is_array($allMediaIds) && count($allMediaIds) > 0)
            ? Media::whereIn('id', $allMediaIds)->get()
            : [];

        $checkAttemptsContent = json_decode($checkAttempts->content(), true);
        $original_image       = Media::find($latestAiProfile->original_image_id);

        return success([
            'data'                 => $mediaRecords,
            'original_image'       => $original_image,
            'attempts'             => $checkAttemptsContent['data']['attempts'] ?? 0,
            'remaining_attempts'   => $checkAttemptsContent['data']['remaining_attempts'] ?? 0,
            'latest_item_attempts' => $checkAttemptsContent['data']['latest_item_attempts'] ?? 0,
            'is_show_button_generate' => $checkAttemptsContent['data']['remaining_attempts'] > 0
        ]);
    }

    /**
     * STEP 3a — Set employee profile picture to a chosen AI-generated image.
     *
     * Validates that the given $id is in the employee's AI profile history
     * before updating employee.media_id.
     *
     * Route: POST /upload_ai_generated_image/{id}
     */
    public function uploadAiGeneratedImage($id)
    {
        $employee = auth('employees')->user();

        $history        = $this->getAiProfessionalProfileHistory();
        $historyContent = json_decode($history->content());
        $data           = $historyContent->data->data;

        if (!$data || !is_array($data) || !in_array($id, array_column($data, 'id'))) {
            return fail('Image not found in AI Profile history', 404);
        }

        $employee->update(['media_id' => (int) $id]);

        return success(true);
    }

    /**
     * STEP 3b — Set employee profile picture back to the original uploaded image.
     *
     * Validates that $id matches the original_image_id on latestAiProfile.
     *
     * Route: POST /upload_original_profile_image/{id}
     */
    public function UploadOriginalProfileImage($id)
    {
        $employee = auth('employees')->user();

        if (!$employee->latestAiProfile) {
            return fail('AI Profile not found', 404);
        }

        if ($id != $employee->latestAiProfile->original_image_id) {
            return fail('Employee ID does not match with AI Profile', 400);
        }

        $employee->update(['media_id' => $id]);

        return success(true);
    }
}
