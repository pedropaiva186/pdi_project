import * as real from './client.js'
import * as mock from './mock.js'

export const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true'
export const api = USE_MOCK ? mock : real
export { ApiError } from './errors.js'
