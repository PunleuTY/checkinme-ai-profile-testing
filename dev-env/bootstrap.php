<?php

/**
 * Bootstrap — replaces the Laravel container for standalone CLI use.
 *
 * Provides:
 *   1. .env loader
 *   2. config() global shim  → reads from .env
 *   3. app()    global shim  → returns environment string
 *   4. PSR-style autoloader  → maps App\* and Illuminate\* to local files
 */

// ── 1. Load .env ──────────────────────────────────────────────────────────────
$_ENV_FILE = __DIR__ . '/.env';
if (!file_exists($_ENV_FILE)) {
    fwrite(STDERR, "ERROR: .env file not found.\n");
    fwrite(STDERR, "       Run: cp .env.example .env  then add your GOOGLE_API_KEY.\n");
    exit(1);
}

// Custom parser — parse_ini_file rejects special chars like ( ) in comment lines.
$_RAW_ENV = [];
foreach (file($_ENV_FILE, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES) as $line) {
    $line = trim($line);
    if ($line === '' || $line[0] === '#') continue;    // skip comments
    if (!str_contains($line, '=')) continue;            // skip non-assignment lines
    [$key, $val]        = explode('=', $line, 2);
    $_RAW_ENV[trim($key)] = trim($val);
}


// ── 2. config() shim ─────────────────────────────────────────────────────────
function config(string $key): mixed
{
    global $_RAW_ENV;
    return match ($key) {
        'services.google.key' => $_RAW_ENV['GOOGLE_API_KEY'] ?? null,
        default               => null,
    };
}


// ── 3. app() shim ────────────────────────────────────────────────────────────
function app(): object
{
    global $_RAW_ENV;
    $env = $_RAW_ENV['ENVIRONMENT'] ?? 'production';
    return new class($env) {
        public function __construct(private string $env) {}
        public function environment(): string { return $this->env; }
    };
}


// ── 4. Autoloader ────────────────────────────────────────────────────────────
spl_autoload_register(function (string $class): void {
    $base = __DIR__;

    if (str_starts_with($class, 'App\\')) {
        // App\Services\AI\AiProfileGenerateService → app/Services/AI/AiProfileGenerateService.php
        $relative = str_replace('\\', '/', substr($class, 4));
        $path     = "$base/app/$relative.php";

    } elseif (str_starts_with($class, 'Illuminate\\')) {
        // Illuminate\Support\Facades\Http → src/stubs/Support/Facades/Http.php
        $relative = str_replace('\\', '/', substr($class, 11));
        $path     = "$base/src/stubs/$relative.php";

    } else {
        return;
    }

    if (file_exists($path)) {
        require_once $path;
    }
});
