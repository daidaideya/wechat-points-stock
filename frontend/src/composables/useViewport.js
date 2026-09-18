import { computed, onBeforeUnmount, onMounted, readonly, ref } from 'vue'

/**
 * Keep viewport breakpoints reactive without making individual pages manage
 * their own resize listeners.
 */
export function useViewport({ mobileMax = 900 } = {}) {
  const width = ref(typeof window === 'undefined' ? 0 : window.innerWidth)
  const isMobile = computed(() => width.value > 0 && width.value <= mobileMax)

  function updateWidth() {
    width.value = window.innerWidth
  }

  onMounted(() => {
    updateWidth()
    window.addEventListener('resize', updateWidth, { passive: true })
  })

  onBeforeUnmount(() => {
    window.removeEventListener('resize', updateWidth)
  })

  return {
    width: readonly(width),
    isMobile,
  }
}
