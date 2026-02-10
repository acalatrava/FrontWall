<template>
  <div>
    <h1 class="text-2xl font-bold text-white mb-6">Security Settings</h1>

    <div class="space-y-6">
      <div class="bg-gray-900 border border-gray-800 rounded-xl p-6">
        <h2 class="text-lg font-semibold text-white mb-4">WAF (Web Application Firewall)</h2>
        <p class="text-sm text-gray-400 mb-4">
          The WAF is automatically active when the shield is deployed. It provides the following protections:
        </p>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div v-for="feature in wafFeatures" :key="feature.name" class="flex items-start gap-3 bg-gray-800/50 rounded-lg p-4">
            <span class="mt-0.5 w-5 h-5 rounded-full bg-green-500/20 text-green-400 flex items-center justify-center text-xs">&#10003;</span>
            <div>
              <div class="text-sm font-medium text-white">{{ feature.name }}</div>
              <div class="text-xs text-gray-400 mt-0.5">{{ feature.description }}</div>
            </div>
          </div>
        </div>
      </div>

      <div class="bg-gray-900 border border-gray-800 rounded-xl p-6">
        <h2 class="text-lg font-semibold text-white mb-4">Security Headers</h2>
        <p class="text-sm text-gray-400 mb-4">
          These headers are automatically injected into every response from the shield server.
        </p>
        <div class="space-y-2">
          <div v-for="header in securityHeaders" :key="header.name" class="bg-gray-800/50 rounded-lg px-4 py-3">
            <div class="text-sm font-mono text-blue-400">{{ header.name }}</div>
            <div class="text-xs text-gray-500 font-mono mt-1 break-all">{{ header.value }}</div>
          </div>
        </div>
      </div>

      <div class="bg-gray-900 border border-gray-800 rounded-xl p-6">
        <h2 class="text-lg font-semibold text-white mb-4">Blocked Patterns</h2>
        <p class="text-sm text-gray-400 mb-4">
          Requests matching these patterns in the path or query string are automatically blocked.
        </p>
        <div class="flex flex-wrap gap-2">
          <span v-for="pattern in blockedPatterns" :key="pattern" class="px-3 py-1.5 bg-red-500/10 text-red-400 rounded-lg text-xs font-mono">
            {{ pattern }}
          </span>
        </div>
      </div>

      <div class="bg-gray-900 border border-gray-800 rounded-xl p-6">
        <h2 class="text-lg font-semibold text-white mb-4">Input Sanitization</h2>
        <p class="text-sm text-gray-400 mb-4">
          All POST form data is processed through multiple sanitization layers before forwarding.
        </p>
        <div class="space-y-3">
          <div v-for="step in sanitizationSteps" :key="step.name" class="flex items-start gap-3">
            <span class="mt-1 w-6 h-6 rounded-full bg-blue-500/20 text-blue-400 flex items-center justify-center text-xs font-bold">{{ step.order }}</span>
            <div>
              <div class="text-sm font-medium text-white">{{ step.name }}</div>
              <div class="text-xs text-gray-400 mt-0.5">{{ step.description }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
const wafFeatures = [
  { name: 'Rate Limiting', description: 'Token bucket per-IP rate limiting with configurable thresholds' },
  { name: 'Bot Detection', description: 'Blocks known malicious scanners (SQLMap, Nikto, Nessus, etc.)' },
  { name: 'Path Traversal Protection', description: 'Blocks ../ and encoded path traversal attempts' },
  { name: 'WordPress Path Blocking', description: 'Blocks wp-admin, wp-login, xmlrpc.php, wp-config access' },
  { name: 'Request Size Limits', description: 'Configurable max body size (default: 1MB)' },
  { name: 'IP Blacklist / Whitelist', description: 'Block or allow specific IP addresses' },
  { name: 'Suspicious Query Blocking', description: 'Inspects query strings for injection patterns' },
  { name: 'Blocked File Extensions', description: 'Denies access to .php, .env, .sql, .git, and other dangerous extensions' },
]

const securityHeaders = [
  { name: 'Content-Security-Policy', value: "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; frame-ancestors 'none'" },
  { name: 'X-Content-Type-Options', value: 'nosniff' },
  { name: 'X-Frame-Options', value: 'DENY' },
  { name: 'X-XSS-Protection', value: '1; mode=block' },
  { name: 'Strict-Transport-Security', value: 'max-age=63072000; includeSubDomains; preload' },
  { name: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
  { name: 'Permissions-Policy', value: 'camera=(), microphone=(), geolocation=(), payment=()' },
  { name: 'Cross-Origin-Opener-Policy', value: 'same-origin' },
]

const blockedPatterns = [
  'wp-admin', 'wp-login.php', 'xmlrpc.php', 'wp-config',
  '.env', '.git/', 'phpmyadmin', 'wp-includes/',
  '../', '%2e%2e', '/etc/passwd', '/proc/self',
]

const sanitizationSteps = [
  { order: 1, name: 'Field Whitelist', description: 'Only explicitly declared fields are allowed through; unknown fields are stripped' },
  { order: 2, name: 'Unicode Normalization', description: 'All input is normalized to NFC form and null bytes are removed' },
  { order: 3, name: 'HTML Stripping', description: 'All HTML tags are removed using bleach with double-pass cleaning' },
  { order: 4, name: 'SQL Injection Detection', description: 'Patterns like UNION SELECT, OR 1=1, comment sequences are blocked' },
  { order: 5, name: 'XSS Detection', description: 'Script tags, event handlers, javascript: URIs, and other XSS vectors are blocked' },
  { order: 6, name: 'Type Validation', description: 'Fields are validated against their declared type (email, phone, url, etc.)' },
  { order: 7, name: 'Length Enforcement', description: 'Per-field max length limits are enforced' },
  { order: 8, name: 'Custom Regex', description: 'Optional per-field regex validation for custom patterns' },
]
</script>
