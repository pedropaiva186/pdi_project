import catalog from '@shared/processes.json'
import { ApiError } from './errors.js'
import { getDefaults, visibleParams } from '../utils/params.js'

const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

/** Catálogo do mock: tudo implementado, exceto `sobel` (para exercitar o selo). */
const MOCK_CATALOG = (() => {
  const clone = JSON.parse(JSON.stringify(catalog))
  clone.processes = clone.processes.map((process) => ({
    ...process,
    implemented: process.id !== 'sobel',
  }))
  return clone
})()

function isPngFile(file) {
  return file?.type === 'image/png' || /\.png$/i.test(file?.name ?? '')
}

function createCanvas(width, height) {
  const canvas = document.createElement('canvas')
  canvas.width = width
  canvas.height = height
  return canvas
}

/** Decodifica o PNG num canvas e devolve também os pixels. */
async function decodeFile(file) {
  let bitmap
  try {
    bitmap = await createImageBitmap(file)
  } catch {
    throw new ApiError(400, 'invalid_image', 'O arquivo não é um PNG válido.')
  }

  const { width, height } = bitmap
  const canvas = createCanvas(width, height)
  const context = canvas.getContext('2d', { willReadFrequently: true })
  context.drawImage(bitmap, 0, 0)
  if (typeof bitmap.close === 'function') bitmap.close()

  const data = context.getImageData(0, 0, width, height).data
  return { canvas, width, height, data }
}

/** Aproximação do mock: cinza quando R = G = B em todos os pixels. */
function isGrayPixels(data) {
  for (let i = 0; i < data.length; i += 4) {
    if (data[i] !== data[i + 1] || data[i + 1] !== data[i + 2]) return false
  }
  return true
}

function copyCanvas(source) {
  const canvas = createCanvas(source.width, source.height)
  canvas.getContext('2d').drawImage(source, 0, 0)
  return canvas
}

/** Cria uma imagem cinza com o valor de um canal (0 = R, 1 = G, 2 = B). */
function channelCanvas(source, channelIndex) {
  const canvas = createCanvas(source.width, source.height)
  const context = canvas.getContext('2d')
  const sourceData = source
    .getContext('2d')
    .getImageData(0, 0, source.width, source.height).data
  const image = context.createImageData(source.width, source.height)

  for (let i = 0; i < sourceData.length; i += 4) {
    const value = sourceData[i + channelIndex]
    image.data[i] = value
    image.data[i + 1] = value
    image.data[i + 2] = value
    image.data[i + 3] = 255
  }

  context.putImageData(image, 0, 0)
  return canvas
}

/** Cria uma imagem cinza com um dos canais HSV (H escalado para 0–255). */
function hsvCanvas(source, channel) {
  const canvas = createCanvas(source.width, source.height)
  const context = canvas.getContext('2d')
  const sourceData = source
    .getContext('2d')
    .getImageData(0, 0, source.width, source.height).data
  const image = context.createImageData(source.width, source.height)

  for (let i = 0; i < sourceData.length; i += 4) {
    const r = sourceData[i] / 255
    const g = sourceData[i + 1] / 255
    const b = sourceData[i + 2] / 255
    const max = Math.max(r, g, b)
    const min = Math.min(r, g, b)
    const delta = max - min

    let hue = 0
    if (delta !== 0) {
      if (max === r) hue = ((g - b) / delta) % 6
      else if (max === g) hue = (b - r) / delta + 2
      else hue = (r - g) / delta + 4
      hue *= 60
      if (hue < 0) hue += 360
    }
    const saturation = max === 0 ? 0 : delta / max
    const value = max

    let byte
    if (channel === 'h') byte = Math.round((hue / 360) * 255)
    else if (channel === 's') byte = Math.round(saturation * 255)
    else byte = Math.round(value * 255)

    image.data[i] = byte
    image.data[i + 1] = byte
    image.data[i + 2] = byte
    image.data[i + 3] = 255
  }

  context.putImageData(image, 0, 0)
  return canvas
}

/** Histograma de 256 posições do canal R (para cinza, R = G = B). */
function histogramOf(source) {
  const data = source
    .getContext('2d')
    .getImageData(0, 0, source.width, source.height).data
  const values = new Array(256).fill(0)
  for (let i = 0; i < data.length; i += 4) {
    values[data[i]] += 1
  }
  return values
}

function makeOutput({ id, label, role = 'main', canvas, mode }) {
  return {
    id,
    label,
    role,
    mode,
    width: canvas.width,
    height: canvas.height,
    image: canvas.toDataURL('image/png'),
  }
}

/** Espera 150 ms e devolve um clone do catálogo. */
export async function getProcesses() {
  await wait(150)
  return JSON.parse(JSON.stringify(MOCK_CATALOG))
}

/** Inspeciona o PNG no canvas (aproximação do backend). */
export async function inspectImage(file) {
  if (!isPngFile(file)) {
    throw new ApiError(400, 'invalid_image', 'O arquivo não é um PNG válido.')
  }

  const decoded = await decodeFile(file)
  const gray = isGrayPixels(decoded.data)

  return {
    mode: gray ? 'gray' : 'rgb',
    width: decoded.width,
    height: decoded.height,
    source_mode: gray ? 'L' : 'RGB',
    filename: file.name,
  }
}

/**
 * Simula a execução de um processo: espera 400 ms, valida modo/processo e
 * devolve o mesmo formato de resposta da API real.
 */
export async function runProcess(processId, file, params = {}) {
  await wait(400)

  const process = MOCK_CATALOG.processes.find((item) => item.id === processId)
  if (!process) {
    throw new ApiError(404, 'process_not_found', `Processo "${processId}" não encontrado.`)
  }

  if (!isPngFile(file)) {
    throw new ApiError(400, 'invalid_image', 'O arquivo não é um PNG válido.')
  }

  const decoded = await decodeFile(file)
  const mode = isGrayPixels(decoded.data) ? 'gray' : 'rgb'

  if (!process.modes.includes(mode)) {
    const imageKind = mode === 'gray' ? 'em escala de cinza' : 'coloridas (RGB)'
    throw new ApiError(
      422,
      'unsupported_mode',
      `Este processo não está disponível para imagens ${imageKind}.`,
    )
  }

  if (process.id === 'sobel') {
    throw new ApiError(
      501,
      'not_implemented',
      'O processo "Gradiente de Sobel" ainda não foi implementado.',
    )
  }

  const startedAt = performance.now()
  const outputs = []
  const histograms = []

  if (process.id === 'rgb_split') {
    outputs.push(
      makeOutput({ id: 'r', label: 'Canal R', canvas: channelCanvas(decoded.canvas, 0), mode: 'gray' }),
      makeOutput({ id: 'g', label: 'Canal G', canvas: channelCanvas(decoded.canvas, 1), mode: 'gray' }),
      makeOutput({ id: 'b', label: 'Canal B', canvas: channelCanvas(decoded.canvas, 2), mode: 'gray' }),
    )
  } else if (process.id === 'hsv_split') {
    outputs.push(
      makeOutput({ id: 'h', label: 'Canal H', canvas: hsvCanvas(decoded.canvas, 'h'), mode: 'gray' }),
      makeOutput({ id: 's', label: 'Canal S', canvas: hsvCanvas(decoded.canvas, 's'), mode: 'gray' }),
      makeOutput({ id: 'v', label: 'Canal V', canvas: hsvCanvas(decoded.canvas, 'v'), mode: 'gray' }),
    )
  } else if (process.id === 'histogram_equalization') {
    outputs.push(
      makeOutput({
        id: 'equalized',
        label: 'Imagem equalizada',
        canvas: copyCanvas(decoded.canvas),
        mode,
      }),
    )
    const values = histogramOf(decoded.canvas)
    histograms.push(
      { id: 'before', label: 'Histograma original', channel: 'gray', values },
      { id: 'after', label: 'Histograma equalizado', channel: 'gray', values: values.slice() },
    )
  } else if (process.id === 'laplacian_sharpen') {
    outputs.push(
      makeOutput({
        id: 'result',
        label: 'Imagem realçada',
        canvas: copyCanvas(decoded.canvas),
        mode,
      }),
      makeOutput({
        id: 'laplacian',
        label: 'Laplaciano ajustado',
        role: 'aux',
        canvas: copyCanvas(decoded.canvas),
        mode,
      }),
    )
  } else {
    outputs.push(
      makeOutput({
        id: 'result',
        label: 'Resultado (simulado)',
        canvas: copyCanvas(decoded.canvas),
        mode,
      }),
    )
  }

  const elapsed = Number((performance.now() - startedAt).toFixed(2))
  const merged = { ...getDefaults(process), ...params }

  return {
    process_id: process.id,
    params: visibleParams(process, merged),
    input: { mode, width: decoded.width, height: decoded.height },
    outputs,
    histograms,
    metrics: [{ label: 'Tempo de processamento', value: elapsed, unit: 'ms' }],
    elapsed_ms: elapsed,
  }
}
