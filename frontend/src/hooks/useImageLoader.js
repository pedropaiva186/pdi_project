import { useCallback, useRef } from 'react'
import { api } from '../api/index.js'
import {
  IMAGE_LOADED,
  INSPECT_ERROR,
  INSPECT_START,
  PUSH_TOAST,
} from '../state/actions.js'
import { stripExtension } from '../utils/format.js'
import { friendlyMessage } from '../utils/messages.js'

function isPng(file) {
  return file?.type === 'image/png' || /\.png$/i.test(file?.name ?? '')
}

/**
 * Abre um PNG: valida, inspeciona na API e monta o `ImageRef`.
 * Abrir pelo botão ou por arrastar usa `asOriginal: true`; "Usar como entrada"
 * usa `asOriginal: false` para preservar a imagem original.
 *
 * @param {React.Dispatch<object>} dispatch
 * @returns {(file: File, options?: { asOriginal?: boolean }) => Promise<void>}
 */
export function useImageLoader(dispatch) {
  // Só a abertura mais recente pode alterar o estado: quando duas aberturas
  // se sobrepõem, a anterior é descartada em vez de vencer a que termina por último.
  const latestInspectId = useRef(0)

  return useCallback(
    async (file, { asOriginal = true } = {}) => {
      if (!file) return

      if (!isPng(file)) {
        dispatch({
          type: PUSH_TOAST,
          toast: { kind: 'error', message: 'Selecione um arquivo PNG.' },
        })
        return
      }

      const inspectId = latestInspectId.current + 1
      latestInspectId.current = inspectId
      dispatch({ type: INSPECT_START, inspectId })

      try {
        const info = await api.inspectImage(file)
        if (inspectId !== latestInspectId.current) return

        const image = {
          file,
          url: URL.createObjectURL(file),
          name: stripExtension(file.name),
          filename: file.name,
          mode: info.mode,
          width: info.width,
          height: info.height,
          sourceMode: info.source_mode,
        }
        dispatch({ type: IMAGE_LOADED, image, asOriginal })
      } catch (error) {
        if (inspectId !== latestInspectId.current) return
        dispatch({ type: INSPECT_ERROR })
        dispatch({
          type: PUSH_TOAST,
          toast: { kind: 'error', message: friendlyMessage(error) },
        })
      }
    },
    [dispatch],
  )
}
