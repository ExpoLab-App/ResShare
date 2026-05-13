/**
 * Logger utility for consistent logging across the application
 * Only logs in development environment
 */

const isDevelopment = process.env.NODE_ENV === 'development';

export const logger = {
  debug: (label, data) => {
    if (isDevelopment) {
      console.log(`[DEBUG] [${label}]`, data);
    }
  },

  info: (label, data) => {
    if (isDevelopment) {
      console.info(`[INFO] [${label}]`, data);
    }
  },

  warn: (label, data) => {
    if (isDevelopment) {
      console.warn(`[WARN] [${label}]`, data);
    }
  },

  error: (label, error) => {
    if (isDevelopment) {
      console.error(`[ERROR] [${label}]`, error);
    }
  },

  api: (method, url, data) => {
    if (isDevelopment) {
      console.log(`[API] ${method} ${url}`, data);
    }
  }
};

export default logger;
