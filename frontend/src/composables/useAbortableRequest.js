import { onBeforeUnmount } from 'vue'

/**
 * Keep one latest request per page section and abort it when the next request
 * starts or the component unmounts. Consumers can use isCurrent() to ignore
 * stale success/error/finally handlers after a refresh race.
 */
export function createAbortableRequestController() {
  let activeRequest = null

  function start() {
    activeRequest?.controller.abort()
    const request = {
      controller: new AbortController(),
    }
    activeRequest = request
    return {
      signal: request.controller.signal,
      isCurrent: () => activeRequest === request && !request.controller.signal.aborted,
      finish: () => {
        if (activeRequest === request) activeRequest = null
      },
    }
  }

  function cancel() {
    activeRequest?.controller.abort()
    activeRequest = null
  }

  return { start, cancel }
}

export function useAbortableRequest() {
  const controller = createAbortableRequestController()
  onBeforeUnmount(controller.cancel)
  return controller
}
