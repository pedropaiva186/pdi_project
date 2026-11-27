import { useCallback, useEffect, useRef } from 'react'
import { api } from '../api/index.js'
import { PROCESS_ERROR, PROCESS_START, PROCESS_SUCCESS, PUSH_TOAST } from '../state/actions.js'
import { getDefaults, visibleParams } from '../utils/params.js'
import { friendlyMessage, isVerboseError } from '../utils/messages.js'

/**
 * Executa o processo selecionado. Respostas obsoletas (imagem trocada durante
 * o processamento) são descartadas pelo reducer via `requestId`.
 *
 * @param {object} options
 * @param {object} options.state
 * @param {React.Dispatch<object>} options.dispatch
 * @param {object|null} options.process
 * @param {boolean} options.canApply
 * @returns {() => Promise<void>}
 */
export function useProcessRunner({ state, dispatch, process, canApply }) {
  // Espelha o requestId do reducer: indica, ao chegar a resposta, se ela ainda
  // é a mais recente. Não há bloqueio global: o controle fica no reducer
  // (`status`/`requestId`) e o botão Aplicar já é desabilitado fora de 'idle'.
  const currentRequestId = useRef(state.requestId)

  useEffect(() => {
    currentRequestId.current = state.requestId
  }, [state.requestId])

  return useCallback(async () => {
    if (!canApply || !process || !state.input) return

    const requestId = state.requestId + 1
    currentRequestId.current = requestId
    dispatch({ type: PROCESS_START })

    const values = state.paramsByProcess[process.id] ?? getDefaults(process)
    const params = visibleParams(process, values)

    try {
      const result = await api.runProcess(process.id, state.input.file, params)
      dispatch({
        type: PROCESS_SUCCESS,
        requestId,
        result: { ...result, inputName: state.input.name },
      })
    } catch (error) {
      dispatch({ type: PROCESS_ERROR, requestId })
      if (currentRequestId.current === requestId) {
        dispatch({
          type: PUSH_TOAST,
          toast: {
            kind: 'error',
            message: friendlyMessage(error),
            duration: isVerboseError(error) ? 10000 : undefined,
          },
        })
      }
    }
  }, [canApply, process, state.input, state.requestId, state.paramsByProcess, dispatch])
}
