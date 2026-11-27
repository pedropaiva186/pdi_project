/**
 * Utilitários puros para os parâmetros declarados em `shared/processes.json`.
 * Nenhuma função aqui acessa estado global ou a API.
 */

/**
 * Conta as casas decimais de um passo (`step`) numérico.
 * Ex.: `0.01 → 2`, `0.1 → 1`, `1 → 0`.
 *
 * @param {number|string} step
 * @returns {number}
 */
export function decimalsOf(step) {
  if (step === null || step === undefined) return 0
  const text = String(step)
  const expMatch = /e-(\d+)$/i.exec(text)
  if (expMatch) {
    const mantissa = text.slice(0, expMatch.index)
    const mantissaDecimals = mantissa.includes('.') ? mantissa.split('.')[1].length : 0
    return mantissaDecimals + Number(expMatch[1])
  }
  const dot = text.indexOf('.')
  return dot === -1 ? 0 : text.length - dot - 1
}

/**
 * Limita um número ao intervalo [min, max]. Limites ausentes são ignorados.
 *
 * @param {number} value
 * @param {number|undefined} min
 * @param {number|undefined} max
 * @returns {number}
 */
function clamp(value, min, max) {
  let result = value
  if (typeof min === 'number' && result < min) result = min
  if (typeof max === 'number' && result > max) result = max
  return result
}

/**
 * Extrai os valores default de todos os parâmetros de um processo.
 *
 * @param {object} process
 * @returns {Record<string, unknown>}
 */
export function getDefaults(process) {
  const values = {}
  for (const param of process?.params ?? []) {
    values[param.id] = param.default
  }
  return values
}

/**
 * Indica se um parâmetro está visível para o conjunto de valores atual.
 * Sem `visible_if`, o parâmetro é sempre visível.
 *
 * @param {object} param
 * @param {Record<string, unknown>} values
 * @returns {boolean}
 */
export function isVisible(param, values) {
  if (!param?.visible_if) return true
  return values?.[param.visible_if.param] === param.visible_if.equals
}

/**
 * Retorna apenas os parâmetros visíveis, já com os valores informados (ou o
 * default quando ausente). É este objeto que vai para a API.
 *
 * @param {object} process
 * @param {Record<string, unknown>} values
 * @returns {Record<string, unknown>}
 */
export function visibleParams(process, values) {
  const result = {}
  for (const param of process?.params ?? []) {
    if (!isVisible(param, values)) continue
    result[param.id] = values?.[param.id] ?? param.default
  }
  return result
}

/**
 * Normaliza um valor bruto de acordo com o tipo e as restrições do parâmetro:
 * - `int`: arredonda, limita a [min, max] e, com `odd`, força o ímpar mais próximo;
 * - `float`: converte, limita e arredonda para as casas de `step`;
 * - `bool`: converte para booleano;
 * - `select`: se o valor não estiver entre as opções, usa o default.
 *
 * @param {object} param
 * @param {unknown} raw
 * @returns {unknown}
 */
export function normalizeValue(param, raw) {
  if (!param) return raw

  switch (param.type) {
    case 'int': {
      let value = Math.round(Number(raw))
      if (Number.isNaN(value)) value = param.default
      value = clamp(value, param.min, param.max)
      if (param.odd && value % 2 === 0) {
        if (typeof param.max !== 'number' || value + 1 <= param.max) value += 1
        else value -= 1
      }
      return value
    }
    case 'float': {
      let value = Number(raw)
      if (Number.isNaN(value)) value = param.default
      value = clamp(value, param.min, param.max)
      const decimals = decimalsOf(param.step)
      return Number(value.toFixed(decimals))
    }
    case 'bool':
      return Boolean(raw)
    case 'select': {
      const options = param.options ?? []
      const allowed = options.some((option) => option.value === raw)
      return allowed ? raw : param.default
    }
    default:
      return raw
  }
}

/**
 * Verifica as restrições entre parâmetros e devolve as mensagens violadas.
 * Hoje só existe a regra `less_equal`; regras desconhecidas são ignoradas com
 * um aviso no console. A restrição só é avaliada quando os dois parâmetros
 * envolvidos estão visíveis.
 *
 * @param {object} process
 * @param {Record<string, unknown>} values
 * @returns {string[]}
 */
export function checkConstraints(process, values) {
  const messages = []
  const params = process?.params ?? []

  for (const constraint of process?.constraints ?? []) {
    if (constraint.rule !== 'less_equal') {
      console.warn(`Regra de restrição desconhecida: ${constraint.rule}`)
      continue
    }

    const [leftId, rightId] = constraint.params ?? []
    const leftParam = params.find((param) => param.id === leftId)
    const rightParam = params.find((param) => param.id === rightId)
    if (!leftParam || !rightParam) continue
    if (!isVisible(leftParam, values) || !isVisible(rightParam, values)) continue

    const left = Number(values?.[leftId])
    const right = Number(values?.[rightId])
    if (Number.isNaN(left) || Number.isNaN(right)) continue
    if (left > right) messages.push(constraint.message)
  }

  return messages
}
