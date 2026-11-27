import { getDefaults } from '../utils/params.js'
import {
  CATALOG_ERROR,
  CATALOG_LOADED,
  CATALOG_LOADING,
  DISMISS_TOAST,
  IMAGE_LOADED,
  INSPECT_ERROR,
  INSPECT_START,
  PROCESS_ERROR,
  PROCESS_START,
  PROCESS_SUCCESS,
  PUSH_TOAST,
  RESET_PARAMS,
  RESTORE_ORIGINAL,
  SELECT_PROCESS,
  SET_ACTIVE_OUTPUT,
  SET_PARAM,
} from './actions.js'

export const initialState = {
  catalog: null,
  catalogStatus: 'loading',
  catalogError: null,
  input: null,
  original: null,
  selectedProcessId: null,
  paramsByProcess: {},
  result: null,
  activeOutputId: null,
  status: 'idle',
  requestId: 0,
  inspectId: 0,                  // id da abertura de arquivo mais recente
  toasts: [],
}

function findProcess(catalog, id) {
  if (!catalog || !id) return null
  return catalog.processes.find((process) => process.id === id) ?? null
}

/** Limpa a seleção se o processo não aceitar o modo da imagem atual. */
function revalidateSelection(state, image) {
  const selected = findProcess(state.catalog, state.selectedProcessId)
  if (!selected) return state.selectedProcessId
  if (!image || !selected.modes.includes(image.mode)) return null
  return state.selectedProcessId
}

function nextToastId(toasts) {
  return toasts.reduce((max, toast) => Math.max(max, toast.id), 0) + 1
}

export function appReducer(state, action) {
  switch (action.type) {
    case CATALOG_LOADING:
      return { ...state, catalogStatus: 'loading', catalogError: null }

    case CATALOG_LOADED: {
      const paramsByProcess = { ...state.paramsByProcess }
      for (const process of action.catalog.processes ?? []) {
        if (!paramsByProcess[process.id]) {
          paramsByProcess[process.id] = getDefaults(process)
        }
      }
      return {
        ...state,
        catalog: action.catalog,
        catalogStatus: 'ready',
        catalogError: null,
        paramsByProcess,
        selectedProcessId: findProcess(action.catalog, state.selectedProcessId)
          ? state.selectedProcessId
          : null,
      }
    }

    case CATALOG_ERROR:
      return { ...state, catalogStatus: 'error', catalogError: action.message }

    case INSPECT_START:
      return {
        ...state,
        status: 'inspecting',
        // Abrir outra imagem invalida o processamento em curso.
        requestId: state.requestId + 1,
        inspectId: action.inspectId,
      }

    case IMAGE_LOADED: {
      return {
        ...state,
        input: action.image,
        original: action.asOriginal ? action.image : state.original,
        result: null,
        activeOutputId: null,
        status: 'idle',
        // Invalida qualquer resposta de processamento em andamento.
        requestId: state.requestId + 1,
        selectedProcessId: revalidateSelection(state, action.image),
      }
    }

    case INSPECT_ERROR:
      return { ...state, status: 'idle' }

    case SELECT_PROCESS: {
      const process = findProcess(state.catalog, action.id)
      if (!process) return state
      if (!state.input || !process.modes.includes(state.input.mode)) return state
      return { ...state, selectedProcessId: action.id }
    }

    case SET_PARAM: {
      const process = findProcess(state.catalog, action.processId)
      if (!process) return state
      const current = state.paramsByProcess[action.processId] ?? getDefaults(process)
      return {
        ...state,
        paramsByProcess: {
          ...state.paramsByProcess,
          [action.processId]: { ...current, [action.paramId]: action.value },
        },
      }
    }

    case RESET_PARAMS: {
      const process = findProcess(state.catalog, action.processId)
      if (!process) return state
      return {
        ...state,
        paramsByProcess: {
          ...state.paramsByProcess,
          [action.processId]: getDefaults(process),
        },
      }
    }

    case PROCESS_START:
      return { ...state, status: 'processing', requestId: state.requestId + 1 }

    case PROCESS_SUCCESS: {
      if (action.requestId !== state.requestId) return state
      const firstMain = (action.result.outputs ?? []).find((output) => output.role === 'main')
      return {
        ...state,
        status: 'idle',
        result: action.result,
        activeOutputId: firstMain ? firstMain.id : null,
      }
    }

    case PROCESS_ERROR:
      if (action.requestId !== state.requestId) return state
      return { ...state, status: 'idle' }

    case SET_ACTIVE_OUTPUT:
      return { ...state, activeOutputId: action.id }

    case RESTORE_ORIGINAL: {
      if (!state.original) return state
      return {
        ...state,
        input: state.original,
        result: null,
        activeOutputId: null,
        status: 'idle',
        requestId: state.requestId + 1,
        selectedProcessId: revalidateSelection(state, state.original),
      }
    }

    case PUSH_TOAST: {
      const toast = {
        id: nextToastId(state.toasts),
        kind: action.toast.kind ?? 'info',
        message: action.toast.message,
        duration: action.toast.duration,
      }
      return { ...state, toasts: [...state.toasts, toast] }
    }

    case DISMISS_TOAST:
      return { ...state, toasts: state.toasts.filter((toast) => toast.id !== action.id) }

    default:
      return state
  }
}
