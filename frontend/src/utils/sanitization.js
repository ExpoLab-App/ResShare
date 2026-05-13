/**
 * Input sanitization utilities
 * Prevents XSS and injection attacks
 */

/**
 * Sanitize username input
 * Allows only alphanumeric characters, underscores, and hyphens
 * @param {string} username - Raw username input
 * @returns {string} Sanitized username
 */
export const sanitizeUsername = (username) => {
  if (!username || typeof username !== 'string') {
    return '';
  }
  return username.trim().replace(/[^a-zA-Z0-9_-]/g, '');
};

/**
 * Sanitize file/folder name
 * Removes invalid filesystem characters
 * @param {string} name - Raw name input
 * @returns {string} Sanitized name
 */
export const sanitizeFileName = (name) => {
  if (!name || typeof name !== 'string') {
    return '';
  }
  // Remove invalid filesystem characters
  return name.trim().replace(/[<>:"/\\|?*]/g, '');
};

/**
 * Sanitize path input
 * Ensures path doesn't contain directory traversal attempts
 * @param {string} path - Raw path input
 * @returns {string} Sanitized path
 */
export const sanitizePath = (path) => {
  if (!path || typeof path !== 'string') {
    return '';
  }
  // Remove directory traversal attempts and normalize slashes
  return path
    .trim()
    .replace(/\.\./g, '')
    .replace(/\\/g, '/')
    .replace(/\/+/g, '/');
};

/**
 * Safely parse JSON from localStorage
 * Prevents XSS from compromised localStorage
 * @param {string} key - localStorage key
 * @param {*} defaultValue - Default value if parse fails
 * @returns {*} Parsed value or default
 */
export const safeParseLocalStorage = (key, defaultValue = null) => {
  try {
    const item = localStorage.getItem(key);
    if (item === null) {
      return defaultValue;
    }
    return JSON.parse(item);
  } catch (error) {
    console.error(`Failed to parse localStorage key "${key}":`, error);
    return defaultValue;
  }
};

/**
 * Safely parse boolean from localStorage
 * @param {string} key - localStorage key
 * @param {boolean} defaultValue - Default boolean value
 * @returns {boolean} Parsed boolean or default
 */
export const safeParseBooleanFromStorage = (key, defaultValue = false) => {
  const value = safeParseLocalStorage(key, defaultValue);
  return typeof value === 'boolean' ? value : defaultValue;
};

/**
 * Escape HTML entities to prevent XSS
 * @param {string} text - Text to escape
 * @returns {string} Escaped text
 */
export const escapeHtml = (text) => {
  if (!text || typeof text !== 'string') {
    return '';
  }
  const map = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#x27;',
    '/': '&#x2F;'
  };
  return text.replace(/[&<>"'/]/g, (char) => map[char]);
};

const sanitization = {
  sanitizeUsername,
  sanitizeFileName,
  sanitizePath,
  safeParseLocalStorage,
  safeParseBooleanFromStorage,
  escapeHtml,
};

export default sanitization;
