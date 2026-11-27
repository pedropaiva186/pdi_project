/**
 * Converte uma data URL base64 em `Blob`.
 *
 * @param {string} dataUrl
 * @returns {Blob}
 */
export function dataUrlToBlob(dataUrl) {
  const comma = dataUrl.indexOf(',')
  const meta = comma === -1 ? '' : dataUrl.slice(0, comma)
  const base64 = comma === -1 ? dataUrl : dataUrl.slice(comma + 1)
  const mimeMatch = /data:([^;]+)/.exec(meta)
  const mime = mimeMatch ? mimeMatch[1] : 'image/png'

  const binary = atob(base64)
  const bytes = new Uint8Array(binary.length)
  for (let i = 0; i < binary.length; i += 1) {
    bytes[i] = binary.charCodeAt(i)
  }
  return new Blob([bytes], { type: mime })
}

/**
 * Converte uma data URL PNG em `File`, pronto para ser reenviado à API.
 *
 * @param {string} dataUrl
 * @param {string} filename
 * @returns {File}
 */
export function dataUrlToFile(dataUrl, filename) {
  const blob = dataUrlToBlob(dataUrl)
  return new File([blob], filename, { type: 'image/png' })
}
