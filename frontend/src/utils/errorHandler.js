/**
 * Centralized error handling utility
 * Provides consistent error messages across the application
 */

// Map backend ErrorCode enum values to user-friendly messages
const BackendErrorMessages = {
  // Authentication errors
  USER_NOT_FOUND: 'User not found. Please check your username and try again.',
  INCORRECT_PASSWORD: 'Incorrect password. Please try again.',
  USER_EXISTS: 'Username already exists. Please choose a different username.',
  INVALID_USERNAME: 'Invalid username. Username must be 3-20 characters and contain only letters, numbers, and underscores.',
  INVALID_PASSWORD: 'Invalid password. Password must be at least 8 characters long and meet complexity requirements.',
  NOT_LOGGED_IN: 'You are not logged in. Please log in to continue.',
  
  // File/Folder errors
  NODE_NOT_FOUND: 'File or folder not found.',
  FILE_NOT_FOUND: 'File not found.',
  DUPLICATE_NAME: 'A file or folder with that name already exists in this location.',
  INVALID_PATH: 'Invalid path. Please check the path and try again.',
  DELETE_NONE_EXIST_NODE: 'Cannot delete: item does not exist.',
  DELETE_ROOT_DIRECTORY: 'Cannot delete the root directory.',
  ADD_CHILD_TO_FILE_NODE: 'Cannot add items to a file. Please select a folder.',
  ONLY_ACCEPT_FOLDER: 'This operation only works with folders.',
  
  // Sharing errors
  SHARE_ROOT: 'Cannot share the root directory.',
  ALREADY_SHARED: 'This item is already shared with the specified user.',
  
  // Request errors
  INVALID_REQUEST: 'Invalid request. Please check your input and try again.',
  
  // System errors
  IPFS_ERROR: 'File storage error. Please try again later.',
  EXCEED_MAX_FILE_SIZE: 'File size exceeds the maximum limit of 1 MB.',
  UNKNOWN_ERROR: 'An unexpected error occurred. Please try again.',
  
  // Success (shouldn't be shown as error, but included for completeness)
  SUCCESS: 'Operation completed successfully.'
};

export const ErrorMessages = {
  NETWORK_ERROR: 'Network error. Please check your connection and try again.',
  AUTHENTICATION_ERROR: 'You are not logged in or your session has expired. Please log in to continue.',
  PERMISSION_DENIED: 'You do not have permission to perform this action.',
  RESOURCE_NOT_FOUND: 'The requested resource was not found.',
  DUPLICATE_RESOURCE: 'A resource with that name already exists.',
  SERVER_ERROR: 'An unexpected server error occurred. Please try again.',
  VALIDATION_ERROR: 'Please check your input and try again.',
  FILE_TOO_LARGE: 'File size exceeds the maximum limit.',
  INVALID_FILE_TYPE: 'This file type is not supported.',
  UNKNOWN_ERROR: 'An unexpected error occurred. Please try again.'
};

/**
 * Get user-friendly error message from error object
 * @param {Error} error - The error object
 * @param {string} context - Optional context for more specific messages
 * @returns {string} User-friendly error message
 */
export const getErrorMessage = (error, context = '') => {
  // First, check if we have a backend error code in the response data
  if (error.response && error.response.data) {
    const data = error.response.data;
    // Check both 'message' and 'result' fields (backend uses both inconsistently)
    const errorCode = data.message || data.result;
    
    if (errorCode && BackendErrorMessages[errorCode]) {
      return BackendErrorMessages[errorCode];
    }
  }

  // Check error.message for backend error codes (from handleResponse in api.js)
  if (error.message) {
    // Check if error.message is a backend error code
    if (BackendErrorMessages[error.message]) {
      return BackendErrorMessages[error.message];
    }
    
    // Handle network errors
    if (error.message === 'Network Error' || error.message === 'Failed to fetch') {
      return ErrorMessages.NETWORK_ERROR;
    }
    
    // If it's not a known error code, use it as-is (might be a custom message)
    // Add context if provided
    if (context) {
      return `${context}: ${error.message}`;
    }
    return error.message;
  }

  // Handle API response errors with status codes (fallback)
  if (error.response) {
    const status = error.response.status;
    switch (status) {
      case 401:
        return ErrorMessages.AUTHENTICATION_ERROR;
      case 403:
        return ErrorMessages.PERMISSION_DENIED;
      case 404:
        return ErrorMessages.RESOURCE_NOT_FOUND;
      case 409:
        return ErrorMessages.DUPLICATE_RESOURCE;
      case 413:
        return ErrorMessages.FILE_TOO_LARGE;
      case 500:
      case 502:
      case 503:
        return ErrorMessages.SERVER_ERROR;
      default:
        break;
    }
  }

  // Default fallback
  return context ? `${context}: ${ErrorMessages.UNKNOWN_ERROR}` : ErrorMessages.UNKNOWN_ERROR;
};

/**
 * Create error with context
 * @param {string} operation - The operation being performed
 * @param {string} resourceName - The resource name (file, folder, etc.)
 * @returns {Function} Error handler function
 */
export const createContextualError = (operation, resourceName = '') => {
  return (error) => {
    const resource = resourceName ? ` "${resourceName}"` : '';
    const context = `Failed to ${operation}${resource}`;
    return getErrorMessage(error, context);
  };
};

/**
 * Get user-friendly message from backend error code
 * @param {string} errorCode - Backend error code (e.g., 'USER_NOT_FOUND')
 * @returns {string} User-friendly error message
 */
export const getBackendErrorMessage = (errorCode) => {
  return BackendErrorMessages[errorCode] || ErrorMessages.UNKNOWN_ERROR;
};

const errorHandler = {
  getErrorMessage,
  getBackendErrorMessage,
  createContextualError,
  ErrorMessages,
};

export default errorHandler;
