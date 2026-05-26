<?php

namespace Illuminate\Support\Facades;

/**
 * Minimal Log facade stub — writes to stderr so errors are visible
 * in the terminal without polluting stdout (where image paths are printed).
 */
class Log
{
    public static function error(string $message): void
    {
        fwrite(STDERR, "[ERROR] " . $message . PHP_EOL);
    }

    public static function info(string $message): void
    {
        fwrite(STDERR, "[INFO]  " . $message . PHP_EOL);
    }

    public static function warning(string $message): void
    {
        fwrite(STDERR, "[WARN]  " . $message . PHP_EOL);
    }
}
