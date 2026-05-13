import { useState, useCallback } from 'react';

/**
 * Custom hook for managing snackbar state
 * Provides consistent snackbar management across components
 *
 * @returns {Object} Snackbar state and control functions
 */
const useSnackbar = () => {
  const [snackbar, setSnackbarState] = useState({
    open: false,
    message: '',
    severity: 'info'
  });

  const showSnackbar = useCallback((message, severity = 'info') => {
    setSnackbarState({
      open: true,
      message,
      severity
    });
  }, []);

  const showSuccess = useCallback((message) => {
    showSnackbar(message, 'success');
  }, [showSnackbar]);

  const showError = useCallback((message) => {
    showSnackbar(message, 'error');
  }, [showSnackbar]);

  const showWarning = useCallback((message) => {
    showSnackbar(message, 'warning');
  }, [showSnackbar]);

  const showInfo = useCallback((message) => {
    showSnackbar(message, 'info');
  }, [showSnackbar]);

  const closeSnackbar = useCallback(() => {
    setSnackbarState((prev) => ({ ...prev, open: false }));
  }, []);

  return {
    snackbar,
    showSnackbar,
    showSuccess,
    showError,
    showWarning,
    showInfo,
    closeSnackbar
  };
};

export default useSnackbar;
