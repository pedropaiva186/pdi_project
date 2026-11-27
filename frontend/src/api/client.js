import { ApiError } from './errors.js'

const BASE = '/api'

const NETWORK_ERROR_MESSAGE =
  'Não foi possível conectar ao servidor. Verifique se o backend está rodando.'

/** Status típicos de gateway/proxy quando o backend está fora do ar. */
const GATEWAY_STATUSES = new Set([500, 502, 503, 504])

/**
 * Executa uma requisição e converte falhas no formato de `ApiError`.
 *
 * @param {string} url
 * @param {RequestInit} [options]
 * @returns {Promise<any>}
 */
async function request(url, options) {
  let response
  try {
    response = await fetch(url, options)
  } catch {
    throw new ApiError(0, 'network_error', NETWORK_ERROR_MESSAGE)
  }

  if (!response.ok) {
    let payload = null
    try {
      payload = await response.json()
    } catch {
      payload = null
    }

    if (payload?.error?.code) {
      throw new ApiError(
        response.status,
        payload.error.code,
        payload.error.message,
        payload.error.details,
      )
    }
    // Sem corpo de erro da API em 5xx: quase sempre é o proxy do Vite sem backend.
    if (GATEWAY_STATUSES.has(response.status)) {
      throw new ApiError(
        response.status,
        'network_error',
        NETWORK_ERROR_MESSAGE,
      )
    }
    throw new ApiError(
      response.status,
      'http_error',
      `Erro inesperado do servidor (HTTP ${response.status}).`,
    )
  }

  return response.json()
}

/** Busca o catálogo de processos (com a flag `implemented`). */
export function getProcesses() {
  return request(`${BASE}/processes`)
}

/**
 * Inspeciona um PNG e devolve modo e dimensões.
 *
 * @param {File} file
 */
export function inspectImage(file) {
  const body = new FormData()
  body.append('file', file)
  return request(`${BASE}/images/inspect`, { method: 'POST', body })
}

/**
 * Executa um processo sobre o PNG enviado.
 *
 * @param {string} processId
 * @param {File} file
 * @param {Record<string, unknown>} params
 */
export function runProcess(processId, file, params) {
  const body = new FormData()
  body.append('file', file)
  body.append('params', JSON.stringify(params ?? {}))
  return request(`${BASE}/process/${encodeURIComponent(processId)}`, {
    method: 'POST',
    body,
  })
}
