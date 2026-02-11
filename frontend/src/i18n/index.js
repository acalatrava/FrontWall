import { createI18n } from 'vue-i18n'
import en from './en.json'
import es from './es.json'

const savedLocale = localStorage.getItem('frontwall-locale') || 'en'

const i18n = createI18n({
  legacy: false,
  locale: savedLocale,
  fallbackLocale: 'en',
  messages: { en, es },
})

export function setLocale(locale) {
  i18n.global.locale.value = locale
  localStorage.setItem('frontwall-locale', locale)
  document.documentElement.lang = locale
}

export default i18n
