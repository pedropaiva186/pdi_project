/**
 * Converte um erro da camada de API em uma mensagem amigável em português.
 * Alguns códigos têm prioridade sobre `error.message`; para os demais, usa-se
 * a mensagem do backend (que já vem em português).
 *
 * @param {unknown} error
 * @returns {string}
 */
export function friendlyMessage(error) {
  const code = error?.code

  if (code === 'not_implemented') {
    return 'Processo ainda não implementado no backend.'
  }
  if (code === 'network_error') {
    return error?.message || 'Não foi possível conectar ao servidor. Verifique se o backend está rodando.'
  }
  if (code === 'unsupported_mode') {
    return 'Este processo não está disponível para o tipo da imagem atual.'
  }

  const message = typeof error?.message === 'string' ? error.message.trim() : ''
  return message || 'Ocorreu um erro inesperado.'
}

/** Erros que devem permanecer mais tempo no toast e mostrar a mensagem completa. */
export function isVerboseError(error) {
  return error?.code === 'processing_error' || error?.code === 'invalid_output'
}
