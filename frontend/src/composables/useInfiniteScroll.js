import { onBeforeUnmount, unref } from 'vue'

export function createInfiniteScrollController({
  target,
  onLoadMore,
  canLoadMore = () => true,
  root = null,
  rootMargin = '0px 0px 320px 0px',
  threshold = 0,
}) {
  let observer = null

  function disconnect() {
    if (observer) {
      observer.disconnect()
      observer = null
    }
  }

  function observe() {
    disconnect()
    const element = unref(target)
    if (!element || !canLoadMore() || typeof IntersectionObserver === 'undefined') return

    observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry?.isIntersecting)) {
          void onLoadMore()
        }
      },
      { root, rootMargin, threshold },
    )
    observer.observe(element)
  }

  return { observe, disconnect }
}

export function useInfiniteScroll(options) {
  const controller = createInfiniteScrollController(options)
  onBeforeUnmount(controller.disconnect)
  return controller
}
