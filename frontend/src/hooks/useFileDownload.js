import { useState, useCallback } from 'react';
import { fileAPI, utils } from '../utils/api';
import { getErrorMessage } from '../utils/errorHandler';
import { logger } from '../utils/logger';

/**
 * Custom hook for handling file downloads
 * Supports both File System Access API and fallback blob download
 *
 * @param {Function} onError - Callback for error handling
 * @returns {Object} Download state and function
 */
const useFileDownload = (onError) => {
  const [isDownloading, setIsDownloading] = useState(false);

  const downloadFile = useCallback(async (path, filename, isShared = false) => {
    setIsDownloading(true);
    logger.debug('File Download', { path, filename, isShared });

    try {
      const response = await fileAPI.downloadFile(path, isShared);

      if (!response.ok) {
        throw new Error('Download failed');
      }

      const blob = await response.blob();

      // Check if File System Access API is supported
      if ('showSaveFilePicker' in window) {
        try {
          // Modern browser with File System Access API
          const handle = await window.showSaveFilePicker({
            suggestedName: filename,
            types: [{
              description: 'All Files',
              accept: { '*/*': [] }
            }]
          });

          const writable = await handle.createWritable();
          await writable.write(blob);
          await writable.close();

          logger.info('File Download', 'Saved via File System Access API');
          return { success: true, method: 'filesystem' };
        } catch (fsError) {
          // User cancelled or error in File System Access API
          if (fsError.name === 'AbortError') {
            logger.info('File Download', 'User cancelled save dialog');
            return { success: false, cancelled: true };
          }

          // Fall back to blob download
          logger.warn('File System Access API failed', fsError);
          utils.downloadBlob(blob, filename);
          return { success: true, method: 'blob' };
        }
      } else {
        // Fallback for older browsers
        utils.downloadBlob(blob, filename);
        logger.info('File Download', 'Saved via blob download (fallback)');
        return { success: true, method: 'blob' };
      }
    } catch (error) {
      logger.error('File Download Error', error);
      const errorMessage = getErrorMessage(error, `Failed to download "${filename}"`);
      if (onError) {
        onError(errorMessage);
      }
      return { success: false, error: errorMessage };
    } finally {
      setIsDownloading(false);
    }
  }, [onError]);

  return {
    downloadFile,
    isDownloading
  };
};

export default useFileDownload;
