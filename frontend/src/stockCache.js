// Small in-memory cache shared by StockPage instances. Keeping only the
// requested page means navigation back to the stock view can paint immediately
// without putting thousands of product objects into localStorage.
let cacheEntry = null

export function readStockCache(key, ttlMs) {
  if (!cacheEntry || cacheEntry.key !== key) return null
  if (Date.now() - cacheEntry.timestamp > ttlMs) return null
  return cacheEntry.data
}

export function writeStockCache(key, data) {
  cacheEntry = {
    key,
    data,
    timestamp: Date.now(),
  }
}

export function invalidateStockCache() {
  cacheEntry = null
}
