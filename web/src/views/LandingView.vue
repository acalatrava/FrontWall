<template>
  <div class="min-h-screen bg-gray-950 text-white overflow-x-hidden">

    <!-- Nav -->
    <nav class="fixed top-0 inset-x-0 z-50 transition-all duration-300"
         :class="scrolled ? 'bg-gray-950/90 backdrop-blur-xl border-b border-gray-800/60 shadow-lg' : ''">
      <div class="max-w-7xl mx-auto flex items-center justify-between px-6 py-4">
        <a href="#" class="flex items-center gap-2.5 flex-shrink-0">
          <svg class="w-8 h-8 text-blue-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
            <path d="m9 12 2 2 4-4" stroke="#22c55e"/>
          </svg>
          <span class="text-lg font-bold tracking-widest uppercase font-heading">FrontWall</span>
        </a>

        <div class="hidden lg:flex items-center gap-7 text-sm text-gray-400">
          <a href="#features" class="hover:text-white transition-colors">{{ t('nav.features') }}</a>
          <a href="#how-it-works" class="hover:text-white transition-colors">{{ t('nav.howItWorks') }}</a>
          <a href="#protection" class="hover:text-white transition-colors">{{ t('nav.protection') }}</a>
          <a href="#install" class="hover:text-white transition-colors">{{ t('nav.install') }}</a>
        </div>

        <div class="flex items-center gap-2">
          <select
            :value="currentLocale"
            @change="switchLocale($event.target.value)"
            class="hidden sm:block w-9 h-9 bg-transparent border border-gray-700/60 rounded-lg text-xs text-gray-400 text-center focus:outline-none focus:ring-2 focus:ring-blue-500 hover:border-gray-600 transition-colors cursor-pointer"
            style="background-image: none; padding-right: 0;"
            :title="localeLabels[currentLocale]"
          >
            <option v-for="loc in locales" :key="loc" :value="loc">{{ loc.toUpperCase() }}</option>
          </select>
          <a href="https://github.com/acalatrava/FrontWall" target="_blank" rel="noopener" class="w-9 h-9 flex items-center justify-center border border-gray-700/60 rounded-lg text-gray-400 hover:text-white hover:border-gray-600 transition-colors" title="GitHub">
            <svg class="w-[18px] h-[18px]" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
          </a>
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
        <div class="inline-flex items-center gap-2 px-4 py-1.5 bg-blue-500/10 border border-blue-500/20 rounded-full text-blue-400 text-xs font-semibold tracking-wider uppercase font-heading mb-8 animate-fade-in-down">
          <span class="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-pulse"></span>
          {{ t('hero.badge') }}
        </div>

        <h1 class="text-5xl md:text-7xl font-extrabold leading-[1.05] tracking-tight mb-6 animate-fade-in-up">
          {{ t('hero.titleLine1') }}
          <br/>
          <span class="bg-gradient-to-r from-blue-400 via-blue-500 to-emerald-400 bg-clip-text text-transparent">{{ t('hero.titleLine2') }}</span>
        </h1>

        <p class="max-w-2xl mx-auto text-lg md:text-xl text-gray-400 leading-relaxed mb-10 animate-fade-in-up animation-delay-200">
          {{ t('hero.subtitle') }}
        </p>

        <div class="flex flex-col sm:flex-row items-center justify-center gap-4 animate-fade-in-up animation-delay-400">
          <a href="#install" class="group px-8 py-3.5 bg-blue-600 hover:bg-blue-500 text-base font-semibold rounded-xl transition-all hover:shadow-xl hover:shadow-blue-500/25 flex items-center gap-2">
            {{ t('hero.getStarted') }}
            <svg class="w-4 h-4 group-hover:translate-x-0.5 transition-transform" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
          </a>
          <a href="#how-it-works" class="px-8 py-3.5 border border-gray-700 hover:border-gray-500 text-base font-medium text-gray-300 hover:text-white rounded-xl transition-all">
            {{ t('hero.seeHowItWorks') }}
          </a>
        </div>

        <!-- Terminal visual -->
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
          <div class="text-sm text-gray-400 mt-1">{{ t('stats.staticServing') }}</div>
        </div>
        <div>
          <div class="text-3xl md:text-4xl font-extrabold text-white">0</div>
          <div class="text-sm text-gray-400 mt-1">{{ t('stats.noPhp') }}</div>
        </div>
        <div>
          <div class="text-3xl md:text-4xl font-extrabold text-white">7+</div>
          <div class="text-sm text-gray-400 mt-1">{{ t('stats.securityLayers') }}</div>
        </div>
        <div>
          <div class="text-3xl md:text-4xl font-extrabold text-white">&lt;5ms</div>
          <div class="text-sm text-gray-400 mt-1">{{ t('stats.responseTime') }}</div>
        </div>
      </div>
    </section>

    <!-- Features -->
    <section id="features" class="py-24 md:py-32">
      <div class="max-w-6xl mx-auto px-6">
        <div class="text-center mb-16">
          <h2 class="text-3xl md:text-4xl font-extrabold mb-4">{{ t('features.title') }}</h2>
          <p class="text-gray-400 max-w-2xl mx-auto">{{ t('features.subtitle') }}</p>
        </div>

        <div class="grid md:grid-cols-3 gap-6">
          <div v-for="(f, i) in featuresList" :key="i" class="group relative bg-gray-900/50 border border-gray-800/60 rounded-2xl p-7 hover:border-gray-700/80 transition-all duration-300 hover:-translate-y-1">
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
          <h2 class="text-3xl md:text-4xl font-extrabold mb-4">{{ t('howItWorks.title') }}</h2>
          <p class="text-gray-400 max-w-2xl mx-auto">{{ t('howItWorks.subtitle') }}</p>
        </div>

        <div class="grid md:grid-cols-3 gap-8">
          <div v-for="(s, i) in stepsList" :key="i" class="relative">
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
          <h2 class="text-3xl md:text-4xl font-extrabold mb-4">{{ t('protection.title') }}</h2>
          <p class="text-gray-400 max-w-2xl mx-auto">{{ t('protection.subtitle') }}</p>
        </div>

        <div class="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div v-for="(th, i) in threatsList" :key="i" class="bg-gray-900/40 border border-gray-800/50 rounded-xl px-5 py-4 flex items-start gap-3">
            <svg class="w-5 h-5 text-red-400 mt-0.5 flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
            <div>
              <div class="text-sm font-semibold text-white">{{ th.name }}</div>
              <div class="text-xs text-gray-500 mt-0.5">{{ th.detail }}</div>
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
          <h2 class="text-3xl md:text-4xl font-extrabold mb-4">{{ t('architecture.title') }}</h2>
          <p class="text-gray-400">{{ t('architecture.subtitle') }}</p>
        </div>

        <div class="flex flex-col md:flex-row items-center justify-center gap-4 md:gap-0">
          <div class="bg-gray-900 border border-gray-700 rounded-xl px-6 py-4 text-center flex-shrink-0">
            <div class="text-2xl mb-1">&#127760;</div>
            <div class="text-sm font-semibold">{{ t('architecture.visitors') }}</div>
            <div class="text-xs text-gray-500">{{ t('architecture.visitorsDesc') }}</div>
          </div>
          <div class="hidden md:block w-16 h-px bg-gradient-to-r from-gray-600 to-blue-500/50"></div>
          <div class="md:hidden h-8 w-px bg-gradient-to-b from-gray-600 to-blue-500/50"></div>
          <div class="bg-blue-600/10 border-2 border-blue-500/40 rounded-xl px-6 py-4 text-center flex-shrink-0 shadow-lg shadow-blue-500/10">
            <div class="text-2xl mb-1">&#128737;&#65039;</div>
            <div class="text-sm font-bold text-blue-400">{{ t('architecture.frontwall') }}</div>
            <div class="text-xs text-gray-400">{{ t('architecture.frontwallDesc') }}</div>
          </div>
          <div class="hidden md:block w-16 h-px bg-gradient-to-r from-blue-500/50 to-gray-600 relative">
            <span class="absolute -top-3 left-1/2 -translate-x-1/2 text-[10px] text-emerald-400 font-mono whitespace-nowrap">{{ t('architecture.postOnly') }}</span>
          </div>
          <div class="md:hidden h-8 w-px bg-gradient-to-b from-blue-500/50 to-gray-600 relative">
            <span class="absolute -right-10 top-1/2 -translate-y-1/2 text-[10px] text-emerald-400 font-mono">{{ t('architecture.postOnly') }}</span>
          </div>
          <div class="bg-gray-900 border border-gray-700 rounded-xl px-6 py-4 text-center flex-shrink-0 opacity-60">
            <div class="text-2xl mb-1">&#128220;</div>
            <div class="text-sm font-semibold">{{ t('architecture.wordpress') }}</div>
            <div class="text-xs text-gray-500">{{ t('architecture.wordpressDesc') }}</div>
          </div>
        </div>

        <div class="mt-10 grid grid-cols-3 gap-3 text-center text-xs max-w-md mx-auto">
          <div class="bg-emerald-500/10 border border-emerald-500/20 rounded-lg py-2 px-3 text-emerald-400">{{ t('architecture.getStatic') }}</div>
          <div class="bg-blue-500/10 border border-blue-500/20 rounded-lg py-2 px-3 text-blue-400">{{ t('architecture.postSanitized') }}</div>
          <div class="bg-red-500/10 border border-red-500/20 rounded-lg py-2 px-3 text-red-400">{{ t('architecture.attacksBlocked') }}</div>
        </div>
      </div>
    </section>

    <!-- Installation -->
    <section id="install" class="py-24 md:py-32 relative">
      <div class="absolute inset-0 bg-gradient-to-b from-blue-600/[0.02] via-transparent to-transparent"></div>
      <div class="relative max-w-4xl mx-auto px-6">
        <div class="text-center mb-16">
          <h2 class="text-3xl md:text-4xl font-extrabold mb-4">{{ t('install.title') }}</h2>
          <p class="text-gray-400 max-w-2xl mx-auto">{{ t('install.subtitle') }}</p>
        </div>

        <div class="space-y-6">
          <div class="bg-gray-900/80 border border-gray-800 rounded-2xl overflow-hidden">
            <div class="px-6 py-4 border-b border-gray-800 text-sm font-medium text-gray-300">
              1. {{ t('install.step1') }}
            </div>
            <div class="p-6 font-mono text-sm text-gray-300">
              <code class="text-emerald-400">$</code> git clone https://github.com/acalatrava/frontwall.git<br/>
              <code class="text-emerald-400">$</code> cd frontwall
            </div>
          </div>

          <div class="bg-gray-900/80 border border-gray-800 rounded-2xl overflow-hidden">
            <div class="px-6 py-4 border-b border-gray-800 text-sm font-medium text-gray-300">
              2. {{ t('install.step2') }}
            </div>
            <div class="p-6 font-mono text-sm text-gray-300">
              <code class="text-emerald-400">$</code> docker compose up -d
            </div>
          </div>

          <div class="bg-gray-900/80 border border-gray-800 rounded-2xl overflow-hidden">
            <div class="px-6 py-4 border-b border-gray-800 text-sm font-medium text-gray-300">
              3. {{ t('install.step3') }}
            </div>
            <div class="p-6 font-mono text-sm text-gray-300">
              <code class="text-emerald-400">$</code> open http://localhost:8000
            </div>
          </div>
        </div>

        <div class="text-center mt-10">
          <a href="https://github.com/acalatrava/frontwall#readme" target="_blank" rel="noopener" class="text-blue-400 hover:text-blue-300 text-sm transition-colors">
            {{ t('install.docsLink') }} &rarr;
          </a>
        </div>
      </div>
    </section>

    <!-- Contributing / Open Source CTA -->
    <section class="py-24 md:py-32">
      <div class="max-w-3xl mx-auto px-6 text-center">
        <div class="relative bg-gradient-to-b from-gray-900 to-gray-900/50 border border-gray-800 rounded-3xl p-12 md:p-16 overflow-hidden">
          <div class="absolute top-0 left-1/2 -translate-x-1/2 w-[500px] h-[300px] bg-blue-600/[0.06] rounded-full blur-[80px]"></div>
          <div class="relative">
            <h2 class="text-3xl md:text-4xl font-extrabold mb-4">{{ t('contributing.title') }}</h2>
            <p class="text-gray-400 mb-8 max-w-lg mx-auto">{{ t('contributing.subtitle') }}</p>
            <div class="flex flex-col sm:flex-row items-center justify-center gap-4">
              <a href="https://github.com/acalatrava/frontwall" target="_blank" rel="noopener" class="inline-flex items-center gap-2 px-8 py-3.5 bg-blue-600 hover:bg-blue-500 text-base font-semibold rounded-xl transition-all hover:shadow-xl hover:shadow-blue-500/25">
                <svg class="w-5 h-5" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
                {{ t('contributing.viewGithub') }}
              </a>
              <a href="https://github.com/acalatrava/frontwall/issues" target="_blank" rel="noopener" class="px-8 py-3.5 border border-gray-700 hover:border-gray-500 text-base font-medium text-gray-300 hover:text-white rounded-xl transition-all">
                {{ t('contributing.reportIssue') }}
              </a>
            </div>
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
        <p class="text-xs text-gray-600">{{ t('footer.tagline') }}</p>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { setLocale } from '../i18n'

const { t, locale: currentLocale } = useI18n()
const locales = ['en', 'es']
const localeLabels = { en: 'English', es: 'Español' }
const scrolled = ref(false)

function switchLocale(loc) {
  setLocale(loc)
}

function handleScroll() {
  scrolled.value = window.scrollY > 40
}

onMounted(() => window.addEventListener('scroll', handleScroll))
onUnmounted(() => window.removeEventListener('scroll', handleScroll))

const featuresList = computed(() => [
  { title: t('features.staticCaching'), desc: t('features.staticCachingDesc'), icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M13 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V9z"/><polyline points="13 2 13 9 20 9"/></svg>', iconBg: 'bg-emerald-500/10 text-emerald-400' },
  { title: t('features.waf'), desc: t('features.wafDesc'), icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>', iconBg: 'bg-blue-500/10 text-blue-400' },
  { title: t('features.postSanitization'), desc: t('features.postSanitizationDesc'), icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>', iconBg: 'bg-purple-500/10 text-purple-400' },
  { title: t('features.geoip'), desc: t('features.geoipDesc'), icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 014 10 15.3 15.3 0 01-4 10 15.3 15.3 0 01-4-10 15.3 15.3 0 014-10z"/></svg>', iconBg: 'bg-amber-500/10 text-amber-400' },
  { title: t('features.rateLimit'), desc: t('features.rateLimitDesc'), icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>', iconBg: 'bg-cyan-500/10 text-cyan-400' },
  { title: t('features.analytics'), desc: t('features.analyticsDesc'), icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>', iconBg: 'bg-rose-500/10 text-rose-400' },
  { title: t('features.csp'), desc: t('features.cspDesc'), icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0110 0v4"/></svg>', iconBg: 'bg-indigo-500/10 text-indigo-400' },
  { title: t('features.learnMode'), desc: t('features.learnModeDesc'), icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 3h6a4 4 0 014 4v14a3 3 0 00-3-3H2z"/><path d="M22 3h-6a4 4 0 00-4 4v14a3 3 0 013-3h7z"/></svg>', iconBg: 'bg-teal-500/10 text-teal-400' },
  { title: t('features.multiSite'), desc: t('features.multiSiteDesc'), icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"/><path d="M16 21V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v16"/></svg>', iconBg: 'bg-orange-500/10 text-orange-400' },
])

const stepsList = computed(() => [
  { title: t('howItWorks.step1Title'), desc: t('howItWorks.step1Desc') },
  { title: t('howItWorks.step2Title'), desc: t('howItWorks.step2Desc') },
  { title: t('howItWorks.step3Title'), desc: t('howItWorks.step3Desc') },
])

const threatsList = computed(() => [
  { name: t('protection.sqlInjection'), detail: t('protection.sqlInjectionDetail') },
  { name: t('protection.xss'), detail: t('protection.xssDetail') },
  { name: t('protection.pathTraversal'), detail: t('protection.pathTraversalDetail') },
  { name: t('protection.bruteForce'), detail: t('protection.bruteForceDetail') },
  { name: t('protection.botScanners'), detail: t('protection.botScannersDetail') },
  { name: t('protection.lfi'), detail: t('protection.lfiDetail') },
  { name: t('protection.wpAdmin'), detail: t('protection.wpAdminDetail') },
  { name: t('protection.xmlrpc'), detail: t('protection.xmlrpcDetail') },
  { name: t('protection.nullByte'), detail: t('protection.nullByteDetail') },
  { name: t('protection.doubleEncoding'), detail: t('protection.doubleEncodingDetail') },
  { name: t('protection.overflow'), detail: t('protection.overflowDetail') },
  { name: t('protection.geoThreats'), detail: t('protection.geoThreatsDetail') },
])
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
