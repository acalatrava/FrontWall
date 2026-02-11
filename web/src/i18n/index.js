import { createI18n } from 'vue-i18n'
import en from './en.json'
import es from './es.json'

const savedLocale = localStorage.getItem('frontwall-web-locale') || navigator.language?.slice(0, 2) || 'en'
const resolvedLocale = ['en', 'es'].includes(savedLocale) ? savedLocale : 'en'

const i18n = createI18n({
  legacy: false,
  locale: resolvedLocale,
  fallbackLocale: 'en',
  messages: { en, es },
})

export function setLocale(locale) {
  i18n.global.locale.value = locale
  localStorage.setItem('frontwall-web-locale', locale)
  document.documentElement.lang = locale
}

export default i18n
