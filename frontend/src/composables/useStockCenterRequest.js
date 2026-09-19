import { onBeforeUnmount } from 'vue'
import { readStockCache, writeStockCache } from '../stockCache.js'
import { createAbortableRequestController } from './useAbortableRequest.js'

export const STOCK_CACHE_TTL = 60 * 1000

/**
 * Keep the stock-center cache, in-flight de-duplication and cancellation in
 * one boundary. The page still owns loading state and response projection;
 * this controller owns only the transport lifecycle.
 */
export function createStockCenterRequestController({
  apiClient,
  requestController = createAbortableRequestController(),
  cacheReader = readStockCache,
  cacheWriter = writeStockCache,
  cacheTtl = STOCK_CACHE_TTL,
} = {}) {
  let activeRequest = null

  function clearActive(request) {
    if (activeRequest !== request) return
    activeRequest = null
    request.context.finish()
  }

  function fetch(params, forceRefresh = false) {
    const key = JSON.stringify(params)
    if (!forceRefresh && params.page === 1) {
      const cached = cacheReader(key, cacheTtl)
      if (cached) return Promise.resolve({ data: cached, fromCache: true })
    }

    if (!forceRefresh && activeRequest && activeRequest.key === key) {
      return activeRequest.promise.then((data) => ({ data, fromCache: false }))
    }

    if (activeRequest) {
      requestController.cancel()
      activeRequest = null
    }

    const context = requestController.start()
    const request = {
      key,
      context,
      promise: apiClient.get('/stock/center', { params, signal: context.signal }).then(({ data }) => {
        if (params.page === 1) cacheWriter(key, data)
        return data
      }),
    }
    activeRequest = request
    request.promise.then(
      () => clearActive(request),
      () => clearActive(request),
    )
    return request.promise.then((data) => ({ data, fromCache: false }))
  }

  function cancel() {
    requestController.cancel()
    activeRequest = null
  }

  return { fetch, cancel }
}

export function useStockCenterRequest(options) {
  const controller = createStockCenterRequestController(options)
  onBeforeUnmount(controller.cancel)
  return controller
}
