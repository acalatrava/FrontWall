<template>
  <div class="min-h-screen bg-gray-950 text-white overflow-x-hidden">

    <!-- Nav -->
    <nav class="fixed top-0 inset-x-0 z-50 transition-all duration-300"
         :class="scrolled ? 'bg-gray-950/90 backdrop-blur-xl border-b border-gray-800/60 shadow-lg' : ''">
      <div class="max-w-7xl mx-auto flex items-center justify-between px-6 py-4">
        <div class="flex items-center gap-3">
          <div class="relative">
            <div class="absolute inset-0 bg-blue-500/20 rounded-full blur-md animate-pulse-slow"></div>
            <svg class="relative w-9 h-9 text-blue-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
              <path d="m9 12 2 2 4-4" stroke="#22c55e"/>
            </svg>
          </div>
          <span class="text-xl font-bold tracking-tight">FrontWall</span>
        </div>
        <div class="hidden md:flex items-center gap-8 text-sm text-gray-400">
          <a href="#features" class="hover:text-white transition-colors">Features</a>
          <a href="#how-it-works" class="hover:text-white transition-colors">How It Works</a>
          <a href="#protection" class="hover:text-white transition-colors">Protection</a>
        </div>
        <div class="flex items-center gap-3">
          <router-link to="/login" class="px-4 py-2 text-sm text-gray-300 hover:text-white transition-colors">Sign In</router-link>
          <router-link to="/login" class="px-5 py-2 bg-blue-600 hover:bg-blue-500 text-sm font-semibold rounded-lg transition-all hover:shadow-lg hover:shadow-blue-500/25">
            Get Started
          </router-link>
        </div>
      </div>
    </nav>

    <!-- Hero -->
    <section class="relative min-h-screen flex items-center justify-center pt-20 overflow-hidden">
      <div class="absolute inset-0">
        <div class="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[900px] h-[900px] bg-blue-600/[0.07] rounded-full blur-[120px]"></div>
        <div class="absolute bottom-0 left-0 w-[500px] h-[500px] bg-emerald-600/[0.05] rounded-full blur-[100px]"></div>
        <div class="absolute top-1/3 right-0 w-[400px] h-[400px] bg-purple-600/[0.04] rounded-full blur-[80px]"></div>
        <div class="hero-grid absolute inset-0 opacity-[0.03]"></div>
      </div>

      <div class="relative z-10 max-w-5xl mx-auto px-6 text-center">
        <div class="inline-flex items-center gap-2 px-4 py-1.5 bg-blue-500/10 border border-blue-500/20 rounded-full text-blue-400 text-xs font-medium mb-8 animate-fade-in-down">
          <span class="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-pulse"></span>
          Enterprise-grade WordPress protection
        </div>

        <h1 class="text-5xl md:text-7xl font-extrabold leading-[1.05] tracking-tight mb-6 animate-fade-in-up">
          Your WordPress.
          <br/>
          <span class="bg-gradient-to-r from-blue-400 via-blue-500 to-emerald-400 bg-clip-text text-transparent">Armored.</span>
        </h1>

        <p class="max-w-2xl mx-auto text-lg md:text-xl text-gray-400 leading-relaxed mb-10 animate-fade-in-up animation-delay-200">
          FrontWall sits in front of your WordPress site, caches everything as static content and serves it through a hardened security layer. Zero attack surface. Full functionality.
        </p>

        <div class="flex flex-col sm:flex-row items-center justify-center gap-4 animate-fade-in-up animation-delay-400">
          <router-link to="/login" class="group px-8 py-3.5 bg-blue-600 hover:bg-blue-500 text-base font-semibold rounded-xl transition-all hover:shadow-xl hover:shadow-blue-500/25 flex items-center gap-2">
            Deploy Your Shield
            <svg class="w-4 h-4 group-hover:translate-x-0.5 transition-transform" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
          </router-link>
          <a href="#how-it-works" class="px-8 py-3.5 border border-gray-700 hover:border-gray-500 text-base font-medium text-gray-300 hover:text-white rounded-xl transition-all">
            See How It Works
          </a>
        </div>

        <!-- Hero visual -->
        <div class="relative mt-20 mx-auto max-w-3xl animate-fade-in-up animation-delay-600">
          <div class="absolute -inset-4 bg-gradient-to-b from-blue-500/10 to-transparent rounded-2xl blur-2xl"></div>
          <div class="relative bg-gray-900/80 backdrop-blur border border-gray-800 rounded-2xl p-1 shadow-2xl">
            <div class="bg-gray-900 rounded-xl overflow-hidden">
              <div class="flex items-center gap-2 px-4 py-3 border-b border-gray-800">
                <span class="w-3 h-3 rounded-full bg-red-500/80"></span>
                <span class="w-3 h-3 rounded-full bg-yellow-500/80"></span>
                <span class="w-3 h-3 rounded-full bg-green-500/80"></span>
                <span class="ml-3 text-xs text-gray-500 font-mono">frontwall — shield active</span>
              </div>
              <div class="p-6 font-mono text-xs md:text-sm leading-relaxed text-left">
                <p><span class="text-emerald-400">&#10003;</span> <span class="text-gray-400">WordPress site crawled:</span> <span class="text-white">247 pages, 1,823 assets</span></p>
                <p><span class="text-emerald-400">&#10003;</span> <span class="text-gray-400">Static cache built:</span> <span class="text-white">42.6 MB optimized</span></p>
                <p><span class="text-emerald-400">&#10003;</span> <span class="text-gray-400">WAF rules loaded:</span> <span class="text-white">12 attack patterns active</span></p>
                <p><span class="text-emerald-400">&#10003;</span> <span class="text-gray-400">POST rules configured:</span> <span class="text-white">3 forms protected</span></p>
                <p><span class="text-emerald-400">&#10003;</span> <span class="text-gray-400">CSP generated:</span> <span class="text-white">58 trusted origins</span></p>
                <p><span class="text-emerald-400">&#10003;</span> <span class="text-gray-400">GeoIP blocking:</span> <span class="text-white">8 high-risk countries filtered</span></p>
                <p class="mt-3"><span class="text-blue-400">&#9670;</span> <span class="text-blue-300">Shield deployed on port 8080</span> <span class="text-emerald-400 animate-pulse">&#9679;</span></p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Stats bar -->
    <section class="relative py-16 border-y border-gray-800/60">
      <div class="max-w-6xl mx-auto px-6 grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
        <div>
          <div class="text-3xl md:text-4xl font-extrabold text-white">100%</div>
          <div class="text-sm text-gray-400 mt-1">Static serving</div>
        </div>
        <div>
          <div class="text-3xl md:text-4xl font-extrabold text-white">0</div>
          <div class="text-sm text-gray-400 mt-1">PHP execution on frontend</div>
        </div>
        <div>
          <div class="text-3xl md:text-4xl font-extrabold text-white">7+</div>
          <div class="text-sm text-gray-400 mt-1">Security layers</div>
        </div>
        <div>
          <div class="text-3xl md:text-4xl font-extrabold text-white">&lt;5ms</div>
          <div class="text-sm text-gray-400 mt-1">Response time</div>
        </div>
      </div>
    </section>

    <!-- Features -->
    <section id="features" class="py-24 md:py-32">
      <div class="max-w-6xl mx-auto px-6">
        <div class="text-center mb-16">
          <h2 class="text-3xl md:text-4xl font-extrabold mb-4">Defense in Depth</h2>
          <p class="text-gray-400 max-w-2xl mx-auto">Every layer adds protection. Every request is verified. Your WordPress stays hidden behind an impenetrable wall.</p>
        </div>

        <div class="grid md:grid-cols-3 gap-6">
          <div v-for="(f, i) in features" :key="i" class="group relative bg-gray-900/50 border border-gray-800/60 rounded-2xl p-7 hover:border-gray-700/80 transition-all duration-300 hover:-translate-y-1">
            <div class="w-12 h-12 rounded-xl flex items-center justify-center mb-5" :class="f.iconBg">
              <div v-html="f.icon" class="w-6 h-6"></div>
            </div>
            <h3 class="text-lg font-bold mb-2">{{ f.title }}</h3>
            <p class="text-sm text-gray-400 leading-relaxed">{{ f.desc }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- How it works -->
    <section id="how-it-works" class="py-24 md:py-32 relative">
      <div class="absolute inset-0 bg-gradient-to-b from-blue-600/[0.02] via-transparent to-transparent"></div>
      <div class="relative max-w-5xl mx-auto px-6">
        <div class="text-center mb-16">
          <h2 class="text-3xl md:text-4xl font-extrabold mb-4">How It Works</h2>
          <p class="text-gray-400 max-w-2xl mx-auto">Three simple steps to transform your WordPress from a liability into a fortress.</p>
        </div>

        <div class="grid md:grid-cols-3 gap-8">
          <div v-for="(s, i) in steps" :key="i" class="relative">
            <div class="flex items-center gap-4 mb-4">
              <div class="w-10 h-10 rounded-full bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400 text-sm font-bold flex-shrink-0">
                {{ i + 1 }}
              </div>
              <div v-if="i < 2" class="hidden md:block flex-1 h-px bg-gradient-to-r from-blue-500/30 to-transparent"></div>
            </div>
            <h3 class="text-lg font-bold mb-2">{{ s.title }}</h3>
            <p class="text-sm text-gray-400 leading-relaxed">{{ s.desc }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- Protection layers -->
    <section id="protection" class="py-24 md:py-32">
      <div class="max-w-6xl mx-auto px-6">
        <div class="text-center mb-16">
          <h2 class="text-3xl md:text-4xl font-extrabold mb-4">What We Block</h2>
          <p class="text-gray-400 max-w-2xl mx-auto">FrontWall protects against the most common and dangerous WordPress attack vectors.</p>
        </div>

        <div class="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div v-for="(t, i) in threats" :key="i" class="bg-gray-900/40 border border-gray-800/50 rounded-xl px-5 py-4 flex items-start gap-3">
            <svg class="w-5 h-5 text-red-400 mt-0.5 flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
            <div>
              <div class="text-sm font-semibold text-white">{{ t.name }}</div>
              <div class="text-xs text-gray-500 mt-0.5">{{ t.detail }}</div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Architecture diagram -->
    <section class="py-24 md:py-32 border-t border-gray-800/60 relative">
      <div class="absolute inset-0 bg-gradient-to-t from-emerald-600/[0.02] via-transparent to-transparent"></div>
      <div class="relative max-w-4xl mx-auto px-6">
        <div class="text-center mb-16">
          <h2 class="text-3xl md:text-4xl font-extrabold mb-4">Architecture</h2>
          <p class="text-gray-400">Your WordPress never sees the internet. FrontWall handles everything.</p>
        </div>

        <div class="flex flex-col md:flex-row items-center justify-center gap-4 md:gap-0">
          <div class="bg-gray-900 border border-gray-700 rounded-xl px-6 py-4 text-center flex-shrink-0">
            <div class="text-2xl mb-1">&#127760;</div>
            <div class="text-sm font-semibold">Visitors</div>
            <div class="text-xs text-gray-500">Internet traffic</div>
          </div>
          <div class="hidden md:block w-16 h-px bg-gradient-to-r from-gray-600 to-blue-500/50"></div>
          <div class="md:hidden h-8 w-px bg-gradient-to-b from-gray-600 to-blue-500/50"></div>
          <div class="bg-blue-600/10 border-2 border-blue-500/40 rounded-xl px-6 py-4 text-center flex-shrink-0 shadow-lg shadow-blue-500/10">
            <div class="text-2xl mb-1">&#128737;&#65039;</div>
            <div class="text-sm font-bold text-blue-400">FrontWall</div>
            <div class="text-xs text-gray-400">WAF + Static Cache</div>
          </div>
          <div class="hidden md:block w-16 h-px bg-gradient-to-r from-blue-500/50 to-gray-600 relative">
            <span class="absolute -top-3 left-1/2 -translate-x-1/2 text-[10px] text-emerald-400 font-mono whitespace-nowrap">POST only</span>
          </div>
          <div class="md:hidden h-8 w-px bg-gradient-to-b from-blue-500/50 to-gray-600 relative">
            <span class="absolute -right-10 top-1/2 -translate-y-1/2 text-[10px] text-emerald-400 font-mono">POST only</span>
          </div>
          <div class="bg-gray-900 border border-gray-700 rounded-xl px-6 py-4 text-center flex-shrink-0 opacity-60">
            <div class="text-2xl mb-1">&#128220;</div>
            <div class="text-sm font-semibold">WordPress</div>
            <div class="text-xs text-gray-500">Hidden origin</div>
          </div>
        </div>

        <div class="mt-10 grid grid-cols-3 gap-3 text-center text-xs max-w-md mx-auto">
          <div class="bg-emerald-500/10 border border-emerald-500/20 rounded-lg py-2 px-3 text-emerald-400">GET &rarr; Static</div>
          <div class="bg-blue-500/10 border border-blue-500/20 rounded-lg py-2 px-3 text-blue-400">POST &rarr; Sanitized</div>
          <div class="bg-red-500/10 border border-red-500/20 rounded-lg py-2 px-3 text-red-400">Attacks &rarr; Blocked</div>
        </div>
      </div>
    </section>

    <!-- CTA -->
    <section class="py-24 md:py-32">
      <div class="max-w-3xl mx-auto px-6 text-center">
        <div class="relative bg-gradient-to-b from-gray-900 to-gray-900/50 border border-gray-800 rounded-3xl p-12 md:p-16 overflow-hidden">
          <div class="absolute top-0 left-1/2 -translate-x-1/2 w-[500px] h-[300px] bg-blue-600/[0.06] rounded-full blur-[80px]"></div>
          <div class="relative">
            <h2 class="text-3xl md:text-4xl font-extrabold mb-4">Ready to protect your site?</h2>
            <p class="text-gray-400 mb-8 max-w-lg mx-auto">Deploy FrontWall in minutes. No code changes needed. Your WordPress stays exactly as it is.</p>
            <router-link to="/login" class="inline-flex items-center gap-2 px-8 py-3.5 bg-blue-600 hover:bg-blue-500 text-base font-semibold rounded-xl transition-all hover:shadow-xl hover:shadow-blue-500/25">
              Access Dashboard
              <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
            </router-link>
          </div>
        </div>
      </div>
    </section>

    <!-- Footer -->
    <footer class="border-t border-gray-800/60 py-10">
      <div class="max-w-6xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-4">
        <div class="flex items-center gap-2">
          <svg class="w-5 h-5 text-blue-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
          </svg>
          <span class="text-sm font-semibold text-gray-400">FrontWall</span>
        </div>
        <p class="text-xs text-gray-600">WordPress security reverse proxy. Built with security-first principles.</p>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const scrolled = ref(false)

function handleScroll() {
  scrolled.value = window.scrollY > 40
}

onMounted(() => window.addEventListener('scroll', handleScroll))
onUnmounted(() => window.removeEventListener('scroll', handleScroll))

const features = [
  {
    title: 'Static Caching',
    desc: 'Your entire WordPress site is crawled, cached, and served as pure static files. No PHP, no database queries, no vulnerabilities.',
    icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M13 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V9z"/><polyline points="13 2 13 9 20 9"/></svg>',
    iconBg: 'bg-emerald-500/10 text-emerald-400',
  },
  {
    title: 'Web Application Firewall',
    desc: 'Multi-layer WAF blocks SQL injection, XSS, path traversal, bot scanners, and known attack patterns before they reach anything.',
    icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
    iconBg: 'bg-blue-500/10 text-blue-400',
  },
  {
    title: 'POST Sanitization',
    desc: 'Contact forms and AJAX requests are validated against strict rules, sanitized for injection attacks, then forwarded to your WordPress.',
    icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>',
    iconBg: 'bg-purple-500/10 text-purple-400',
  },
  {
    title: 'GeoIP Blocking',
    desc: 'Block entire countries known for high attack volumes. Uses Cloudflare headers for zero-latency detection with optional GeoIP fallback.',
    icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 014 10 15.3 15.3 0 01-4 10 15.3 15.3 0 01-4-10 15.3 15.3 0 014-10z"/></svg>',
    iconBg: 'bg-amber-500/10 text-amber-400',
  },
  {
    title: 'Rate Limiting',
    desc: 'Per-IP token bucket rate limiting prevents brute force, DDoS, and resource exhaustion. Static assets bypass limits intelligently.',
    icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
    iconBg: 'bg-cyan-500/10 text-cyan-400',
  },
  {
    title: 'Security Analytics',
    desc: 'Real-time dashboard with threat detection, attacker IP tracking, event timelines, and severity breakdowns for full visibility.',
    icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>',
    iconBg: 'bg-rose-500/10 text-rose-400',
  },
  {
    title: 'Dynamic CSP',
    desc: 'Content Security Policy is auto-generated from your site\'s actual resources. Learn mode discovers external origins automatically.',
    icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0110 0v4"/></svg>',
    iconBg: 'bg-indigo-500/10 text-indigo-400',
  },
  {
    title: 'Learn Mode',
    desc: 'Automatically discover POST rules, CSP origins, and missing assets. FrontWall learns your site\'s needs, then locks down.',
    icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 3h6a4 4 0 014 4v14a3 3 0 00-3-3H2z"/><path d="M22 3h-6a4 4 0 00-4 4v14a3 3 0 013-3h7z"/></svg>',
    iconBg: 'bg-teal-500/10 text-teal-400',
  },
  {
    title: 'Multi-Site Support',
    desc: 'Protect multiple WordPress sites from a single FrontWall instance, each with independent security configurations and ports.',
    icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"/><path d="M16 21V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v16"/></svg>',
    iconBg: 'bg-orange-500/10 text-orange-400',
  },
]

const steps = [
  {
    title: 'Add Your Site',
    desc: 'Enter your WordPress URL and configure crawler settings. FrontWall automatically discovers all pages, assets, and forms.',
  },
  {
    title: 'Crawl & Configure',
    desc: 'The spider captures your entire site. Review cached pages, set up POST rules for forms, and fine-tune security settings.',
  },
  {
    title: 'Deploy the Shield',
    desc: 'One click deploys a hardened reverse proxy. All traffic is served from cache. Attacks are blocked. Your WordPress is invisible.',
  },
]

const threats = [
  { name: 'SQL Injection', detail: 'Database manipulation attempts' },
  { name: 'XSS Attacks', detail: 'Cross-site scripting payloads' },
  { name: 'Path Traversal', detail: 'Directory escape attempts' },
  { name: 'Brute Force', detail: 'Login credential stuffing' },
  { name: 'Bot Scanners', detail: 'SQLMap, Nikto, Nmap, etc.' },
  { name: 'LFI / RFI', detail: 'Local and remote file inclusion' },
  { name: 'wp-admin Access', detail: 'Admin panel exposure' },
  { name: 'xmlrpc.php', detail: 'XML-RPC amplification attacks' },
  { name: 'Null Byte Injection', detail: 'File system manipulation' },
  { name: 'Double Encoding', detail: 'WAF bypass attempts' },
  { name: 'Payload Overflow', detail: 'Oversized request bodies' },
  { name: 'Geo Threats', detail: 'High-risk country traffic' },
]
</script>

<style scoped>
.hero-grid {
  background-image:
    linear-gradient(rgba(255,255,255,.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,.04) 1px, transparent 1px);
  background-size: 80px 80px;
}

@keyframes fade-in-down {
  from { opacity: 0; transform: translateY(-16px); }
  to { opacity: 1; transform: translateY(0); }
}
@keyframes fade-in-up {
  from { opacity: 0; transform: translateY(24px); }
  to { opacity: 1; transform: translateY(0); }
}

.animate-fade-in-down {
  animation: fade-in-down 0.8s ease-out both;
}
.animate-fade-in-up {
  animation: fade-in-up 0.8s ease-out both;
}
.animation-delay-200 {
  animation-delay: 0.2s;
}
.animation-delay-400 {
  animation-delay: 0.4s;
}
.animation-delay-600 {
  animation-delay: 0.6s;
}

.animate-pulse-slow {
  animation: pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}
</style>
