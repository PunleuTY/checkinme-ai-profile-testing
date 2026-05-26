<?php

namespace Illuminate\Support\Facades;

/**
 * Minimal Http facade stub — backs Illuminate\Support\Facades\Http
 * with a plain cURL implementation so AiProfileGenerateService
 * can run outside Laravel.
 *
 * Implements only what the service actually calls:
 *   Http::withHeaders([...])->post($url, $data)
 *   $response->successful()
 *   $response->body()
 *   $response->json()
 */
class Http
{
    private array $headers = [];

    public static function withHeaders(array $headers): static
    {
        $instance = new static();
        $instance->headers = $headers;
        return $instance;
    }

    public function post(string $url, array $data): HttpResponse
    {
        $json = json_encode($data);

        $curlHeaders = array_map(
            fn($k, $v) => "$k: $v",
            array_keys($this->headers),
            array_values($this->headers)
        );

        $ch = curl_init($url);
        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_POST           => true,
            CURLOPT_POSTFIELDS     => $json,
            CURLOPT_HTTPHEADER     => $curlHeaders,
            CURLOPT_TIMEOUT        => 120,
            CURLOPT_SSL_VERIFYPEER => true,
        ]);

        $body     = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $error    = curl_error($ch);
        curl_close($ch);

        if ($body === false) {
            fwrite(STDERR, "[Http] cURL error: $error\n");
            return new HttpResponse(0, '');
        }

        return new HttpResponse($httpCode, $body);
    }
}

class HttpResponse
{
    public function __construct(
        private int    $statusCode,
        private string $rawBody
    ) {}

    public function successful(): bool
    {
        return $this->statusCode >= 200 && $this->statusCode < 300;
    }

    public function body(): string
    {
        return $this->rawBody;
    }

    public function json(): array
    {
        return json_decode($this->rawBody, true) ?? [];
    }

    public function status(): int
    {
        return $this->statusCode;
    }
}
