import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../api'

export const useSitesStore = defineStore('sites', () => {
  const sites = ref([])
  const loading = ref(false)

  async function fetchSites() {
    loading.value = true
    try {
      const { data } = await api.get('/sites/')
      sites.value = data
    } finally {
      loading.value = false
    }
  }

  async function createSite(siteData) {
    const { data } = await api.post('/sites/', siteData)
    sites.value.unshift(data)
    return data
  }

  async function updateSite(siteId, siteData) {
    const { data } = await api.put(`/sites/${siteId}`, siteData)
    const idx = sites.value.findIndex((s) => s.id === siteId)
    if (idx !== -1) sites.value[idx] = data
    return data
  }

  async function deleteSite(siteId) {
    await api.delete(`/sites/${siteId}`)
    sites.value = sites.value.filter((s) => s.id !== siteId)
  }

  return { sites, loading, fetchSites, createSite, updateSite, deleteSite }
})
