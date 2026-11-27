import { useCallback, useEffect } from 'react'
import { api } from '../api/index.js'
import { CATALOG_ERROR, CATALOG_LOADED, CATALOG_LOADING } from '../state/actions.js'
import { friendlyMessage } from '../utils/messages.js'

/**
 * Carrega o catálogo de processos ao montar e expõe `retry`.
 *
 * @param {React.Dispatch<object>} dispatch
 * @returns {{ retry: () => Promise<void> }}
 */
export function useCatalog(dispatch) {
  const load = useCallback(async () => {
    dispatch({ type: CATALOG_LOADING })
    try {
      const catalog = await api.getProcesses()
      dispatch({ type: CATALOG_LOADED, catalog })
    } catch (error) {
      dispatch({ type: CATALOG_ERROR, message: friendlyMessage(error) })
    }
  }, [dispatch])

  useEffect(() => {
    load()
  }, [load])

  return { retry: load }
}
