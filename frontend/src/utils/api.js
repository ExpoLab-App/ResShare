import { logger } from './logger';

const getApiBaseUrl = () => {
  const url = process.env.REACT_APP_API_BASE_URL || 'http://localhost:5000';
  return url.replace(/\/+$/, ''); // Remove trailing slashes
};

const API_BASE_URL = getApiBaseUrl();

if (!process.env.REACT_APP_API_BASE_URL && process.env.NODE_ENV === 'production') {
  logger.warn('API Configuration', 'REACT_APP_API_BASE_URL not configured in production');
}

const handleResponse = async (response, skipAutoRedirect = false) => {
  let data;
  try {
    data = await response.json();
  } catch (error) {
    throw new Error('Invalid server response');
  }

  if (!response.ok) {
    logger.debug('API Error Response', { status: response.status, data });

    const error = new Error(data.message || data.result || 'API request failed');
    error.response = { status: response.status, data };

    // Auto-redirect on 401 (session expired), but skip for signup/login endpoints
    if (response.status === 401 && !skipAutoRedirect) {
      if (window.location.pathname !== '/login' && window.location.pathname !== '/register') {
        logger.info('Session Expired', 'Redirecting to login');
        window.location.href = '/login';
      }
    }

    throw error;
  }

  return data;
};

export const authAPI = {
  login: async (username, password) => {
    logger.api('POST', '/login', { username });
    const response = await fetch(`${API_BASE_URL}/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify({ username, password }),
    });

    return handleResponse(response, true); // Skip auto-redirect for login errors
  },

  signup: async (username, password) => {
    logger.api('POST', '/signup', { username });
    const response = await fetch(`${API_BASE_URL}/signup`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username, password }),
    });
    return handleResponse(response, true); // Skip auto-redirect for signup errors
  },

  logout: async () => {
    const response = await fetch(`${API_BASE_URL}/logout`, {
      method: 'POST',
      credentials: 'include',
    });
    
    return handleResponse(response);
  },

  deleteUser: async (password) => {
    const response = await fetch(`${API_BASE_URL}/delete-user`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify({ password }),
    });

    return handleResponse(response);
  },

  checkAuthStatus: async () => {
    const response = await fetch(`${API_BASE_URL}/auth-status`, {
      method: 'GET',
      credentials: 'include',
    });

    return handleResponse(response);
  },

  fetchSharedItems: async () => {
    const response = await fetch(`${API_BASE_URL}/shared`, {
      method: 'GET',
      credentials: 'include',
    });

    return handleResponse(response);
  },
};

export const fileAPI = {
  createFolder: async (folderPath) => {
    const response = await fetch(`${API_BASE_URL}/create-folder`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify({ folder_path: folderPath }),
    });
    
    return handleResponse(response);
  },

  uploadFile: async (file, path, skipAiProcessing = false) => {
    logger.api('POST', '/upload', { path, skipAiProcessing, filename: file?.name, size: file?.size });
    const sizeValidation = utils.validateFileSize(file, 1); // 1 MB limit
    if (!sizeValidation.isValid) {
      throw new Error(sizeValidation.error);
    }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('path', path || '');
    formData.append('skip_ai_processing', skipAiProcessing.toString());

    const response = await fetch(`${API_BASE_URL}/upload`, {
      method: 'POST',
      credentials: 'include',
      body: formData,
    });
    const data = await handleResponse(response);
    logger.debug('Upload Response', data);
    return data;
  },

  downloadFile: async (path, isShared = false) => {
    const response = await fetch(`${API_BASE_URL}/download`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify({ path, is_shared: isShared }),
    });

    if (!response.ok) {
      const data = await response.json();
      throw new Error(data.message || 'Download failed');
    }

    return response;
  },

  downloadFolderAsZip: async (path, isShared = false) => {
    const response = await fetch(`${API_BASE_URL}/download-zip`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify({ path, is_shared: isShared }),
    });

    if (!response.ok) {
      const data = await response.json();
      throw new Error(data.message || 'Download failed');
    }

    return response;
  },

  deleteItem: async (nodePath, deleteInRoot) => {
    const response = await fetch(`${API_BASE_URL}/delete`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify({ node_path: nodePath, delete_in_root: deleteInRoot }),
    });
    
    return handleResponse(response);
  },

  shareItem: async (targetUsername, node, path) => {
    const payload = {
      target: targetUsername,
    };

    if (path) {
      payload.path = path;
    }

    if (node) {
      payload.node = typeof node === 'string' ? node : JSON.stringify(node);
    }

    const response = await fetch(`${API_BASE_URL}/share`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify(payload),
    });
    
    return handleResponse(response);
  },
};

export const chatAPI = {
  sendMessage: async (query) => {
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify({ query }),
    });
    
    return handleResponse(response);
  },

  getStats: async () => {
    const response = await fetch(`${API_BASE_URL}/chat/stats`, {
      method: 'GET',
      credentials: 'include',
    });
    
    return handleResponse(response);
  },
};

export const utils = {
  formatFileSize: (bytes) => {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  },

  getFileExtension: (filename) => {
    return filename.slice((filename.lastIndexOf('.') - 1 >>> 0) + 2);
  },

  validateFileSize: (file, maxSizeMB = 1) => {
    const maxSizeBytes = maxSizeMB * 1024 * 1024;
    if (file.size > maxSizeBytes) {
      return {
        isValid: false,
        error: `File size (${utils.formatFileSize(file.size)}) exceeds the maximum limit of ${maxSizeMB} MB`
      };
    }
    return { isValid: true, error: null };
  },

  getFileIcon: (filename, isFolder) => {
    if (isFolder) return 'folder';
    
    const extension = utils.getFileExtension(filename).toLowerCase();
    
    const iconMap = {
      // Images
      jpg: 'image',
      jpeg: 'image',
      png: 'image',
      gif: 'image',
      bmp: 'image',
      svg: 'image',
      webp: 'image',
      
      // Documents
      pdf: 'pdf',
      doc: 'document',
      docx: 'document',
      txt: 'text',
      rtf: 'document',
      
      // Spreadsheets
      xls: 'spreadsheet',
      xlsx: 'spreadsheet',
      csv: 'spreadsheet',
      
      // Presentations
      ppt: 'presentation',
      pptx: 'presentation',
      
      // Archives
      zip: 'archive',
      rar: 'archive',
      '7z': 'archive',
      tar: 'archive',
      gz: 'archive',
      
      // Code
      js: 'code',
      jsx: 'code',
      ts: 'code',
      tsx: 'code',
      html: 'code',
      css: 'code',
      scss: 'code',
      py: 'code',
      java: 'code',
      cpp: 'code',
      c: 'code',
      php: 'code',
      rb: 'code',
      go: 'code',
      rs: 'code',
      
      // Audio
      mp3: 'audio',
      wav: 'audio',
      flac: 'audio',
      aac: 'audio',
      ogg: 'audio',
      
      // Video
      mp4: 'video',
      avi: 'video',
      mkv: 'video',
      mov: 'video',
      wmv: 'video',
      flv: 'video',
      webm: 'video',
    };
    
    return iconMap[extension] || 'file';
  },

  downloadBlob: (blob, filename) => {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  },

  validateFileName: (name) => {
    const invalidChars = /[<>:"/\\|?*]/g;
    const reservedNames = /^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])$/i;
    
    if (!name || name.trim() === '') {
      return 'Name cannot be empty';
    }
    
    if (name.length > 255) {
      return 'Name is too long (max 255 characters)';
    }
    
    if (invalidChars.test(name)) {
      return 'Name contains invalid characters';
    }
    
    if (reservedNames.test(name)) {
      return 'Name is reserved by the system';
    }
    
    if (name.startsWith('.') || name.endsWith('.')) {
      return 'Name cannot start or end with a dot';
    }
    
    return null; // Valid name
  },

  debounce: (func, wait) => {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  },

  throttle: (func, limit) => {
    let inThrottle;
    return function() {
      const args = arguments;
      const context = this;
      if (!inThrottle) {
        func.apply(context, args);
        inThrottle = true;
        setTimeout(() => inThrottle = false, limit);
      }
    };
  },
};

const api = {
  authAPI,
  fileAPI,
  utils,
};

export default api; 
