#!/usr/bin/env php
<?php

/**
 * ============================================================
 * AI Profile Prompt — Dev Runner
 * ============================================================
 * Runs AiProfileGenerateService::generate() from the CLI
 * without needing the full Laravel application.
 *
 * USAGE:
 *   php run.php --image=test-inputs/photo.png --gender=male
 *   php run.php --image=test-inputs/photo.png --gender=female --limit=4 --offset=0
 *   php run.php --image=test-inputs/photo.png --gender=male --dry-run
 *   php run.php --image=test-inputs/photo.png --gender=male --version=v2
 *
 * OPTIONS:
 *   --image     Path to the source photo (PNG recommended)
 *   --gender    male | female  (default: male)
 *   --limit     Number of images to generate (default: 4)
 *   --offset    Outfit variant offset 0-15 (default: 0)
 *   --version   Output subfolder: baseline | v2  (default: baseline)
 *   --dry-run   Print the prompts only — no API call, no cost
 * ============================================================
 */

require_once __DIR__ . '/bootstrap.php';

// ── Parse CLI arguments ───────────────────────────────────────────────────────
$opts = getopt('', [
    'image:',
    'gender::',
    'limit::',
    'offset::',
    'version::',
    'dry-run',
]);

$imagePath = $opts['image']   ?? null;
$gender    = $opts['gender']  ?? 'male';
$limit     = (int)($opts['limit']  ?? 4);
$offset    = (int)($opts['offset'] ?? 0);
$version   = $opts['version'] ?? 'baseline';
$dryRun    = array_key_exists('dry-run', $opts);


// ── Validate ──────────────────────────────────────────────────────────────────
if (!$imagePath) {
    echo <<<HELP
    Usage:
      php run.php --image=test-inputs/photo.png --gender=male
      php run.php --image=test-inputs/photo.png --gender=male --dry-run
      php run.php --image=test-inputs/photo.png --gender=female --limit=4 --offset=4 --version=v2

    Options:
      --image     Path to source photo (PNG recommended)
      --gender    male | female  (default: male)
      --limit     Number of images  (default: 4)
      --offset    Outfit offset 0–15  (default: 0)
      --version   baseline | v2  (default: baseline)
      --dry-run   Print prompts only, no API call

    HELP;
    exit(1);
}

if (!$dryRun && !file_exists($imagePath)) {
    fwrite(STDERR, "ERROR: Image not found: $imagePath\n");
    exit(1);
}

if (!in_array($gender, ['male', 'female'])) {
    fwrite(STDERR, "ERROR: --gender must be 'male' or 'female'\n");
    exit(1);
}

if (!config('services.google.key') && !$dryRun) {
    fwrite(STDERR, "ERROR: GOOGLE_API_KEY is not set in .env\n");
    exit(1);
}


// ── Expose protected getPrompts() via a thin subclass ────────────────────────
class DevAiProfileGenerateService extends \App\Services\AI\AiProfileGenerateService
{
    public function getPromptsPublic(string $gender, int $limit, int $offset, string $aspectRatio = '1:1'): array
    {
        return $this->getPrompts($gender, $limit, $offset, $aspectRatio);
    }
}


// ── Dry-run: print prompts only ───────────────────────────────────────────────
$service = new DevAiProfileGenerateService();

if ($dryRun) {
    $prompts = $service->getPromptsPublic($gender, $limit, $offset);
    echo str_repeat('─', 70) . PHP_EOL;
    echo "DRY RUN — Prompts that would be sent to Gemini" . PHP_EOL;
    echo "Gender: $gender | Limit: $limit | Offset: $offset" . PHP_EOL;
    echo str_repeat('─', 70) . PHP_EOL . PHP_EOL;
    foreach ($prompts as $i => $prompt) {
        echo "── Prompt " . ($i + 1) . " " . str_repeat('─', 60) . PHP_EOL;
        echo wordwrap($prompt, 80, PHP_EOL) . PHP_EOL . PHP_EOL;
    }
    echo str_repeat('─', 70) . PHP_EOL;
    echo "Total prompts: " . count($prompts) . PHP_EOL;
    exit(0);
}


// ── Real generation ───────────────────────────────────────────────────────────
$imageBasename = pathinfo($imagePath, PATHINFO_FILENAME);
$timestamp     = date('Y-m-d_His');
$outDir        = __DIR__ . "/outputs/$version/{$imageBasename}_{$timestamp}";

if (!mkdir($outDir, 0755, true)) {
    fwrite(STDERR, "ERROR: Could not create output directory: $outDir\n");
    exit(1);
}

echo str_repeat('─', 70) . PHP_EOL;
echo "AI Profile Generator — Dev Runner" . PHP_EOL;
echo str_repeat('─', 70) . PHP_EOL;
echo "Image   : $imagePath" . PHP_EOL;
echo "Gender  : $gender" . PHP_EOL;
echo "Limit   : $limit" . PHP_EOL;
echo "Offset  : $offset" . PHP_EOL;
echo "Version : $version" . PHP_EOL;
echo "Output  : $outDir" . PHP_EOL;
echo "Env     : " . app()->environment() . PHP_EOL;
echo str_repeat('─', 70) . PHP_EOL;
echo "Calling Gemini... (this can take 30–90s per image)" . PHP_EOL . PHP_EOL;

$start   = microtime(true);
$results = $service->generate($imagePath, $gender, $limit, $offset);
$elapsed = round(microtime(true) - $start, 1);

if (empty($results)) {
    fwrite(STDERR, "ERROR: No images returned. Check STDERR above for API errors.\n");
    exit(1);
}

// ── Save images ───────────────────────────────────────────────────────────────
$saved = [];
foreach ($results as $i => $base64String) {
    $n       = $i + 1;
    $outFile = "$outDir/output_{$n}.png";

    // Strip the data URL prefix if present: "data:image/png;base64,..."
    $raw = preg_replace('/^data:image\/\w+;base64,/', '', $base64String);

    // Handle the case where the non-prod path returns a URL string instead of base64
    if (filter_var($base64String, FILTER_VALIDATE_URL)) {
        file_put_contents($outFile, file_get_contents($base64String));
    } else {
        file_put_contents($outFile, base64_decode($raw));
    }

    $saved[] = $outFile;
    echo "  Saved: $outFile" . PHP_EOL;
}

echo PHP_EOL . str_repeat('─', 70) . PHP_EOL;
echo "Done. " . count($saved) . " image(s) saved in {$elapsed}s." . PHP_EOL;
echo "Folder: $outDir" . PHP_EOL;
echo str_repeat('─', 70) . PHP_EOL;
