/** Rótulo legível do modo da imagem. */
export function modeLabel(mode) {
  if (mode === 'gray') return 'Cinza 8 bits'
  if (mode === 'rgb') return 'RGB 24 bits'
  return mode ?? ''
}

/** Formata dimensões no padrão `512 × 384`. */
export function dims(width, height) {
  if (width == null || height == null) return ''
  return `${width} × ${height}`
}

/** Remove a extensão de um nome de arquivo. */
export function stripExtension(filename) {
  if (!filename) return ''
  return filename.replace(/\.[^./\\]+$/, '')
}

/** Nome de arquivo ao salvar: `{entrada}_{processo}_{saida}.png`. */
export function outputFilename(inputName, processId, outputId) {
  return `${inputName}_${processId}_${outputId}.png`
}

/**
 * Formata um número para exibição em pt-BR: inteiros sem casas decimais e
 * floats com até duas casas (separador decimal vírgula).
 */
export function formatNumber(value) {
  if (typeof value !== 'number' || !Number.isFinite(value)) {
    return value == null ? '' : String(value)
  }
  if (Number.isInteger(value)) return value.toLocaleString('pt-BR')
  return value.toLocaleString('pt-BR', { maximumFractionDigits: 2 })
}
