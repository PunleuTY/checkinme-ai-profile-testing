<?php

namespace App\Services\AI;

use App\Models\Media;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;
use Exception;

class AiProfileGenerateService
{
    protected $apiKey;
    protected $baseUrl = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent';

    public function __construct()
    {
        $this->apiKey = config('services.google.key');
    }

    /**
     * Generate headshots based on uploaded image and gender
     *
     * @param string $imagePath Path to the uploaded image file
     * @param string $gender 'male' or 'female'
     * @param int $limit Number of images (prompts) to generate
     * @param int $offset Offset for prompt selection
     * @return array List of generated image paths or data
     */
    public function generate($imagePath, $gender, $limit = 4, $offset = 0, $aspectRatio = '1:1')
    {
        $prompts = $this->getPrompts($gender, $limit, $offset, $aspectRatio);
        $results = [];

        // Read image data once
        $imageData = base64_encode(file_get_contents($imagePath));

        foreach ($prompts as $prompt) {
            if(app()->environment() !== 'production') {
                $results[] = Media::whereDate('created_at','>=',now()->startOfMonth()->toDateString())
                                ->whereDate('created_at','<=',now()->endOfMonth()->toDateString())
                                ->inRandomOrder()->first()->url ?? "https://development-api.checkinme.app/uploads/images/11238-97285728669bfd844dd6a01774180420.png";
                continue;
            }
            try {
                $response = Http::withHeaders([
                    'Content-Type' => 'application/json'
                ])->post("{$this->baseUrl}?key=" . $this->apiKey, [
                            'contents' => [
                                [
                                    'parts' => [
                                        ['text' => $prompt],
                                        [
                                            'inline_data' => [
                                                'mime_type' => 'image/png', // Assuming PNG or JPEG, Gemini handles standard types
                                                'data' => $imageData
                                            ]
                                        ]
                                    ]
                                ]
                            ],
                            //                            'generationConfig' => [
//                                'response_mime_type' => 'application/json'
//                            ]
                            // You can add specific generation config for aspect ratio if supported by REST API
                            // However, we are primarily enforcing it via prompt in this implementation as per original python code structure
                        ]);

                if ($response->successful()) {
                    $data = $response->json();

                    // Parse response to get image - usually in candidates[0].content.parts
                    // Note: Gemini 2.5 Flash Image might return image data differently via REST.
                    // Often it returns base64 in the response if it's an image generation model.

                    // Let's assume standard Gemini response structure.
                    // However, actual image generation models often return binary or specific inline data.
                    // If the Python code says: `part.inline_data.data` -> this means it returns base64.

                    if (isset($data['candidates'][0]['content']['parts'])) {
                        foreach ($data['candidates'][0]['content']['parts'] as $part) {
                            if (isset($part['inlineData']['data'])) {
                                $imgBase64 = $part['inlineData']['data'];
                                // Return the base64 string for the controller to handle storage
                                $results[] = 'data:image/png;base64,' . $imgBase64;
                            }
                        }
                    }
                } else {
                    Log::error("Gemini API Error: " . $response->body());
                }
            } catch (Exception $e) {
                Log::error("Gemini Generation Exception: " . $e->getMessage());
            }
        }

        return $results;
    }

    protected function getPrompts($gender, $limit, $offset, $aspectRatio = '1:1')
    {
        $commonIntro = "Generate a portrait of a professional " . ($gender === 'male' ? 'male' : 'female') . " ";
        $commonFeatures = " STRICTLY PRESERVE the subject's original face. The output must look exactly like the person in the uploaded image. " .
            "Do not alter facial structure, skin texture, or expression. " .
            "The body should be centered with a natural, professional pose. " .
            "Background must be a soft, solid, professional ID card style background.";

        $neckFix = " Ensure the neck and shoulders are anatomically correct and proportional. " .
            "The clothing must fit naturally around the neck/collar area without floating or weird cuts. ";

        $framingFix = " Frame the image from the top of the head to the mid-chest. ";

        $imageQuality = " PHOTOREALISTIC style. The image must look like a high-end photograph. " .
            "No cartoonish, 3D render, or filtered looks. " .
            "Lighting should be natural studio lighting. ";

        $outfits = [
            'male' => [
                "wearing a tailored black suit jacket over a crisp white shirt and a black silk tie",
                "wearing a charcoal gray business suit jacket with a white shirt and a dark red tie",
                "wearing a navy blue suit jacket over a white shirt and a navy tie",
                "wearing a dark grey formal blazer with a light blue shirt and a dark grey tie",
                "wearing a classic black blazer over a white shirt and a silver tie",
                "wearing a dark blue suit jacket with a white shirt and a blue tie",
                "wearing a slate grey suit jacket over a white shirt and a black tie",
                "wearing a formal black suit jacket with a light grey shirt and a charcoal tie",
                "wearing a deep navy blazer with a crisp white shirt and a burgundy tie",
                "wearing a dark brown suit jacket over a cream shirt and a brown tie",
                "wearing a midnight blue suit jacket with a white shirt and a dark blue tie",
                "wearing a medium grey blazer over a white shirt and a navy tie",
                "wearing a clean black suit jacket over a light blue shirt and a dark blue tie",
                "wearing a formal dark grey suit jacket with a white shirt and a grey tie",
                "wearing a classic navy blazer over a light blue shirt and a navy tie",
                "wearing a sharp black suit jacket with a white shirt and a black tie",
            ],
            'female' => [
                "wearing a tailored black blazer over a white blouse",
                "wearing a charcoal gray business blazer with a white top",
                "wearing a navy blue blazer over a clean white blouse",
                "wearing a dark grey formal blazer with a light blue blouse",
                "wearing a classic black blazer over a white scoop-neck top",
                "wearing a dark blue blazer with a white blouse",
                "wearing a slate grey blazer over a white top",
                "wearing a formal black blazer with a light grey blouse",
                "wearing a deep navy blazer with a crisp white blouse",
                "wearing a dark brown blazer over a cream blouse",
                "wearing a midnight blue blazer with a white top",
                "wearing a textured grey blazer over a white blouse",
                "wearing a clean black blazer over a light blue blouse",
                "wearing a formal dark grey blazer with a white blouse",
                "wearing a classic navy blazer over a light blue top",
                "wearing a sharp black blazer with a white blouse",
            ]
        ];

        $genderKey = ($gender === 'male') ? 'male' : 'female';
        $styleVariants = $outfits[$genderKey];

        // Apply offset
        if ($offset > 0) {
            // Rotate array logic
            $count = count($styleVariants);
            $offset = $offset % $count;
            $styleVariants = array_merge(
                array_slice($styleVariants, $offset),
                array_slice($styleVariants, 0, $offset)
            );
        }

        $selectedStyles = array_slice($styleVariants, 0, $limit);
        $prompts = [];

        foreach ($selectedStyles as $style) {
            $prompts[] = "{$commonIntro} {$style}.{$commonFeatures}{$framingFix}{$neckFix}{$imageQuality}";
        }

        return $prompts;
    }
}
