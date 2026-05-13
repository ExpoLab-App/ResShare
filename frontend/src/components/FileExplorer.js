import React, { useState, useEffect, useCallback } from 'react';
import {
  Container,
  Grid,
  Paper,
  Typography,
  Box,
  Breadcrumbs,
  Link,
  Card,
  CardActionArea,
  Chip,
  IconButton,
  MenuItem,
  Toolbar,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  LinearProgress,
  Tooltip,
  FormControlLabel,
  Switch,
  Divider,
  ClickAwayListener,
} from '@mui/material';
import {
  Folder,
  InsertDriveFile,
  MoreVert,
  ArrowBack,
  Upload,
  CreateNewFolder,
  Share,
  Download,
  Delete,
  NavigateNext,
  Home,
  Image,
  PictureAsPdf,
  Description,
  Code,
  Movie,
  Audiotrack,
  Archive,
  TableChart,
  Slideshow,
  Psychology,
  SmartToy,
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../App';
import { fileAPI, utils } from '../utils/api';
import { logger } from '../utils/logger';
import { getErrorMessage, getBackendErrorMessage } from '../utils/errorHandler';
import { sanitizeFileName, sanitizeUsername, safeParseBooleanFromStorage } from '../utils/sanitization';
import useSnackbar from '../hooks/useSnackbar';
import useFileDownload from '../hooks/useFileDownload';
import useItemContextMenu from '../hooks/useItemContextMenu';
import ConfirmDialog from './ConfirmDialog';
import FormDialog from './FormDialog';

const FileExplorer = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, rootData, setRootData, shareList, refreshShareList } = useAuth();

  const [currentPath, setCurrentPath] = useState('');
  const [currentNode, setCurrentNode] = useState(null);
  const [createFolderOpen, setCreateFolderOpen] = useState(false);
  const [shareDialogOpen, setShareDialogOpen] = useState(false);
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploading, setUploading] = useState(false);
  const [shareUsername, setShareUsername] = useState('');
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [aiModeEnabled, setAiModeEnabled] = useState(() =>
    safeParseBooleanFromStorage('aiModeEnabled', true)
  );
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [itemToDelete, setItemToDelete] = useState(null);

  // Custom hooks
  const { snackbar, showSuccess, showError, closeSnackbar } = useSnackbar();
  const { downloadFile } = useFileDownload(showError);
  const { menuAnchorEl, selectedItem, isMenuOpen, handleMenuOpen, handleMenuClose, clearSelection } = useItemContextMenu();

  const findNodeByPath = useCallback((root, path) => {
    if (!path || path === '') return root;

    const parts = path.split('/').filter(part => part !== '');
    let current = root;

    for (const part of parts) {
      if (current.children && current.children[part]) {
        current = current.children[part];
      } else {
        return null;
      }
    }

    return current;
  }, []);

  useEffect(() => {
    const path = location.pathname.replace('/explorer/', '').replace('/explorer', '');
    setCurrentPath(path);

    if (rootData) {
      // Check if we're in a shared folder
      const pathParts = path.split('/');
      if (pathParts.length > 0 && shareList && shareList[pathParts[0]]) {
        // We're in a shared folder, find the shared node
        const sharedNode = shareList[pathParts[0]].find(node => node.name === pathParts[1]);
        if (sharedNode) {
          setCurrentNode(sharedNode);
          return;
        }
      }

      // Otherwise, find the node in the root data
      const node = findNodeByPath(rootData, path);
      setCurrentNode(node);
    }
  }, [location.pathname, rootData, shareList, findNodeByPath]);

  useEffect(() => {
    const refreshSharedItems = async () => {
      if (!refreshShareList) return;
      try {
        await refreshShareList();
      } catch (error) {
        logger.error('Failed to refresh shared items', error);
      }
    };

    refreshSharedItems();
  }, [refreshShareList, location.pathname]);

  const getPathParts = useCallback(() => {
    if (!currentPath) return [];
    return currentPath.split('/').filter(part => part !== '');
  }, [currentPath]);

  const handleBreadcrumbClick = useCallback((index) => {
    const parts = getPathParts();
    const newPath = parts.slice(0, index + 1).join('/');
    navigate(`/explorer/${newPath}`);
  }, [getPathParts, navigate]);

  const handleDownloadFile = useCallback(async (fileName) => {
    try {
      const filePath = currentPath ? `${currentPath}/${fileName}` : fileName;

      // Check if we're in a shared folder by looking at the path
      const pathParts = currentPath.split('/');
      const isShared = pathParts.length > 0 && shareList && shareList[pathParts[0]];

      // Call downloadFile with (path, filename, isShared)
      const result = await downloadFile(filePath, fileName, isShared);
      if (result.success && !result.cancelled) {
        showSuccess(`Downloaded "${fileName}" successfully`);
      }
    } catch (error) {
      showError(getErrorMessage(error, `Failed to download "${fileName}"`));
    }
  }, [currentPath, shareList, downloadFile, showSuccess, showError]);

  const handleItemClick = useCallback((itemName, item) => {
    if (item.is_folder) {
      const newPath = currentPath ? `${currentPath}/${itemName}` : itemName;
      navigate(`/explorer/${newPath}`);
    } else {
      // Handle file click (preview or download)
      handleDownloadFile(itemName);
    }
  }, [currentPath, navigate, handleDownloadFile]);

  const handleConfirmCreateFolder = async (folderName) => {
    const sanitized = sanitizeFileName(folderName);
    if (!sanitized) {
      showError('Folder name cannot be empty');
      return;
    }

    const validationError = utils.validateFileName(sanitized);
    if (validationError) {
      showError(validationError);
      return;
    }

    try {
      const folderPath = currentPath ? `${currentPath}/${sanitized}` : sanitized;
      const data = await fileAPI.createFolder(folderPath);

      if (data.result === 'SUCCESS') {
        setRootData(JSON.parse(data.root));
        showSuccess('Folder created successfully!');
        setCreateFolderOpen(false);
      } else {
        showError(getBackendErrorMessage(data.result) || 'Failed to create folder');
      }
    } catch (error) {
      showError(getErrorMessage(error, 'Failed to create folder'));
    }
  };

  const handleUploadButtonClick = () => {
    logger.debug('Upload button clicked, opening dialog');
    setUploadDialogOpen(true);
  };

  const handleFileSelect = (event) => {
    const files = Array.from(event.target.files);
    if (files.length > 0) {
      setSelectedFiles(files);
    }
  };

  const handleAiModeToggle = (event) => {
    const enabled = event.target.checked;
    logger.debug('[FileExplorer] Setting aiModeEnabled =', enabled);
    setAiModeEnabled(enabled);
    try {
      localStorage.setItem('aiModeEnabled', JSON.stringify(enabled));
      logger.debug('[FileExplorer] aiModeEnabled saved to localStorage:', enabled);
    } catch (err) {
      logger.warn('[FileExplorer] Failed to save aiModeEnabled:', err);
    }
  };

  const handleUploadConfirm = async () => {
    if (!selectedFiles || selectedFiles.length === 0) return;

    // Validate all files first
    for (const file of selectedFiles) {
      const sizeValidation = utils.validateFileSize(file, 1);
      if (!sizeValidation.isValid) {
        showError(`${file.name}: ${sizeValidation.error}`);
        return;
      }
    }

    logger.debug('[FileExplorer] Starting upload. aiModeEnabled=', aiModeEnabled, 'skip will be', !aiModeEnabled);
    setUploading(true);
    setUploadProgress(0);
    setUploadDialogOpen(false);

    const totalFiles = selectedFiles.length;
    let uploadedFiles = 0;
    let failedFiles = [];

    try {
      for (const file of selectedFiles) {
        try {
          logger.debug('[FileExplorer] Calling API with', {
            path: currentPath || '',
            skip_ai_processing: !aiModeEnabled,
            filename: file?.name,
            size: file?.size,
          });

          const response = await fileAPI.uploadFile(file, currentPath || '', !aiModeEnabled);

          logger.debug('Upload response flags:', {
            rag_processed: response?.rag_processed,
            rag_skipped: response?.rag_skipped,
            skip_ai_processing_sent: !aiModeEnabled,
            skip_ai_processing_backend: response?.skip_ai_processing,
          });

          if (response.message === 'SUCCESS') {
            // Update the root data with the new file
            setRootData(JSON.parse(response.root));
            uploadedFiles++;
          } else {
            failedFiles.push(file.name);
            logger.warn('[FileExplorer] Non-success response:', response);
          }
        } catch (error) {
          logger.error('[FileExplorer] Error uploading file:', file.name, error);
          failedFiles.push(file.name);
        }

        // Update progress
        setUploadProgress(Math.round((uploadedFiles + failedFiles.length) / totalFiles * 100));
      }

      // Show results
      if (failedFiles.length === 0) {
        let message = `${uploadedFiles} file${uploadedFiles > 1 ? 's' : ''} uploaded successfully!`;
        if (aiModeEnabled) {
          message += ' Ready for AI chat.';
        }
        showSuccess(message);
      } else if (uploadedFiles > 0) {
        showError(`Uploaded ${uploadedFiles} file(s), but ${failedFiles.length} failed: ${failedFiles.join(', ')}`);
      } else {
        showError(`Failed to upload all files: ${failedFiles.join(', ')}`);
      }
    } catch (error) {
      logger.error('[FileExplorer] Error thrown:', error);
      showError(getErrorMessage(error, 'Failed to upload files'));
    } finally {
      logger.debug('[FileExplorer] Finalizing upload UI state reset');
      setUploading(false);
      setTimeout(() => setUploadProgress(0), 1000);
      setSelectedFiles([]);
    }
  };

  const handleUploadCancel = () => {
    setUploadDialogOpen(false);
    setSelectedFiles([]);
  };

  const handleDownloadFromMenu = async () => {
    if (!selectedItem) return;

    try {
      const itemPath = currentPath ? `${currentPath}/${selectedItem.name}` : selectedItem.name;

      // Check if we're in a shared folder by looking at the path
      const pathParts = currentPath.split('/');
      const isShared = pathParts.length > 0 && shareList && shareList[pathParts[0]];

      if (selectedItem.is_folder) {
        // Download folder as ZIP
        const response = await fileAPI.downloadFolderAsZip(itemPath, isShared);
        const blob = await response.blob();

        // Trigger download
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${selectedItem.name}.zip`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        showSuccess(`Downloaded "${selectedItem.name}" as ZIP successfully`);
      } else {
        // Download single file
        const result = await downloadFile(itemPath, selectedItem.name, isShared);
        if (result.success && !result.cancelled) {
          showSuccess(`Downloaded "${selectedItem.name}" successfully`);
        }
      }
    } catch (error) {
      showError(getErrorMessage(error, `Failed to download "${selectedItem.name}"`));
    }

    clearSelection();
  };

  const handleShare = async (username) => {
    const sanitized = sanitizeUsername(username || shareUsername);
    if (!sanitized) {
      showError('Invalid username');
      return;
    }

    // Prevent self-sharing
    if (sanitized === user) {
      showError('You cannot share with yourself');
      return;
    }

    if (!selectedItem) return;

    try {
      const path = currentPath ? `${currentPath}/${selectedItem.name}` : selectedItem.name;
      const data = await fileAPI.shareItem(sanitized, selectedItem, path);

      if (data.message === 'SUCCESS') {
        showSuccess('Item shared successfully!');
        setShareDialogOpen(false);
        setShareUsername('');
      } else {
        showError(getBackendErrorMessage(data.message) || 'Failed to share item');
      }
    } catch (error) {
      showError(getErrorMessage(error, 'Failed to share item'));
    }
    handleMenuClose();
  };

  const handleDeleteClick = () => {
    if (!selectedItem) return;
    setItemToDelete(selectedItem);
    setDeleteConfirmOpen(true);
    handleMenuClose();
  };

  const handleConfirmDelete = async () => {
    if (!itemToDelete) return;

    try {
      const itemPath = currentPath ? `${currentPath}/${itemToDelete.name}` : itemToDelete.name;

      const response = await fileAPI.deleteItem(itemPath, true);
      if (response.message === 'SUCCESS') {
        setRootData(JSON.parse(response.root));
        showSuccess(`Deleted "${itemToDelete.name}" successfully`);
      } else {
        showError(getBackendErrorMessage(response.message) || `Failed to delete "${itemToDelete.name}"`);
      }
    } catch (error) {
      showError(getErrorMessage(error, `Failed to delete "${itemToDelete.name}"`));
    } finally {
      setItemToDelete(null);
    }
  };

  const getFileIcon = (filename) => {
    const iconType = utils.getFileIcon(filename, false);

    switch (iconType) {
      case 'image':
        return <Image sx={{ fontSize: 48, color: 'primary.main' }} />;
      case 'pdf':
        return <PictureAsPdf sx={{ fontSize: 48, color: '#f44336' }} />;
      case 'document':
        return <Description sx={{ fontSize: 48, color: '#2196f3' }} />;
      case 'spreadsheet':
        return <TableChart sx={{ fontSize: 48, color: '#4caf50' }} />;
      case 'presentation':
        return <Slideshow sx={{ fontSize: 48, color: '#ff9800' }} />;
      case 'code':
        return <Code sx={{ fontSize: 48, color: '#9c27b0' }} />;
      case 'archive':
        return <Archive sx={{ fontSize: 48, color: '#795548' }} />;
      case 'audio':
        return <Audiotrack sx={{ fontSize: 48, color: '#e91e63' }} />;
      case 'video':
        return <Movie sx={{ fontSize: 48, color: '#00bcd4' }} />;
      default:
        return <InsertDriveFile sx={{ fontSize: 48, color: 'text.secondary' }} />;
    }
  };

  const renderItems = () => {
    if (!currentNode || !currentNode.children) {
      return (
        <Grid item xs={12}>
          <Box
            sx={{
              textAlign: 'center',
              py: 8,
              color: 'text.secondary',
            }}
          >
            <Folder sx={{ fontSize: 64, mb: 2, opacity: 0.5 }} />
            <Typography variant="h6" sx={{ mb: 1 }}>
              This folder is empty
            </Typography>
            <Typography variant="body2" sx={{ mb: 2 }}>
              Upload files or create folders to get started
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Maximum file size: 1 MB
            </Typography>
          </Box>
        </Grid>
      );
    }

    return Object.entries(currentNode.children).map(([name, item]) => (
      <Grid item xs={12} sm={6} md={4} lg={3} key={name}>
        <Card
          sx={{
            height: '100%',
            transition: 'all 0.3s ease',
            '&:hover': {
              transform: 'translateY(-2px)',
              boxShadow: 4,
            },
          }}
        >
          <Box sx={{ position: 'relative' }}>
            <CardActionArea
              onClick={() => handleItemClick(name, item)}
              sx={{ height: '100%', p: 2 }}
            >
              <Box
                sx={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: 2,
                }}
              >
                {item.is_folder ? (
                  <Folder sx={{ fontSize: 48, color: 'primary.main' }} />
                ) : (
                  getFileIcon(name)
                )}
                <Typography
                  variant="subtitle1"
                  align="center"
                  sx={{
                    fontWeight: 500,
                    wordBreak: 'break-word',
                  }}
                >
                  {name}
                </Typography>
                {!item.is_folder && item.file_obj && (
                  <Chip
                    label={`${(item.file_obj.size / 1024).toFixed(1)} KB`}
                    size="small"
                    variant="outlined"
                  />
                )}
              </Box>
            </CardActionArea>
            <Box
              sx={{
                position: 'absolute',
                top: 8,
                right: 8,
                zIndex: 1,
              }}
            >
              <Tooltip title="More options">
                <IconButton
                  onClick={(e) => handleMenuOpen(e, { name, ...item })}
                  size="small"
                  sx={{
                    bgcolor: 'background.paper',
                    '&:hover': {
                      bgcolor: 'action.hover',
                    },
                  }}
                >
                  <MoreVert />
                </IconButton>
              </Tooltip>
            </Box>
          </Box>
        </Card>
      </Grid>
    ));
  };

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Toolbar */}
      <Paper sx={{ mb: 3 }}>
        <Toolbar sx={{ gap: 2 }}>
          <IconButton onClick={() => navigate('/home')}>
            <ArrowBack />
          </IconButton>

          <Breadcrumbs
            separator={<NavigateNext fontSize="small" />}
            sx={{ flexGrow: 1 }}
          >
            <Link
              component="button"
              variant="body1"
              onClick={() => navigate('/home')}
              sx={{
                display: 'flex',
                alignItems: 'center',
                textDecoration: 'none',
                '&:hover': { textDecoration: 'underline' },
              }}
            >
              <Home sx={{ mr: 0.5, fontSize: 20 }} />
              Home
            </Link>
            {getPathParts().map((part, index) => (
              <Link
                key={index}
                component="button"
                variant="body1"
                onClick={() => handleBreadcrumbClick(index)}
                sx={{
                  textDecoration: 'none',
                  '&:hover': { textDecoration: 'underline' },
                }}
              >
                {part}
              </Link>
            ))}
          </Breadcrumbs>

          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Typography variant="caption" color="text.secondary">
              Max: 1 MB
            </Typography>

            {/* AI Processing Toggle (global for uploads) */}
            <FormControlLabel
              control={
                <Switch
                  checked={aiModeEnabled}
                  onChange={(e) => {
                    logger.debug('[FileExplorer] Toolbar AI toggle changed to', e.target.checked);
                    handleAiModeToggle(e);
                  }}
                  color="primary"
                  size="small"
                />
              }
              label={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                  {aiModeEnabled ? (
                    <Psychology sx={{ fontSize: 16, color: 'primary.main' }} />
                  ) : (
                    <SmartToy sx={{ fontSize: 16, color: 'text.secondary' }} />
                  )}
                  <Typography variant="caption" color="text.secondary">
                    AI {aiModeEnabled ? 'On' : 'Off'}
                  </Typography>
                </Box>
              }
              sx={{ m: 0 }}
            />

            <Button
              variant="contained"
              startIcon={<Upload />}
              disabled={uploading}
              onClick={handleUploadButtonClick}
            >
              Upload
            </Button>
          </Box>

          <Button
            variant="outlined"
            startIcon={<CreateNewFolder />}
            onClick={() => setCreateFolderOpen(true)}
          >
            New Folder
          </Button>
        </Toolbar>

        {uploading && (
          <LinearProgress
            variant="determinate"
            value={uploadProgress}
            sx={{ height: 2 }}
          />
        )}
      </Paper>

      {/* File Grid */}
      <Paper sx={{ p: 3 }}>
        <Grid container spacing={2}>
          {renderItems()}
        </Grid>
      </Paper>

      {/* Create Folder Dialog */}
      <FormDialog
        open={createFolderOpen}
        onClose={() => setCreateFolderOpen(false)}
        onSubmit={handleConfirmCreateFolder}
        title="Create New Folder"
        label="Folder Name"
        placeholder="Enter folder name"
        validateInput={(value) => utils.validateFileName(sanitizeFileName(value))}
        submitText="Create"
      />

      {/* Share Dialog */}
      <FormDialog
        open={shareDialogOpen}
        onClose={() => {
          setShareDialogOpen(false);
          setShareUsername('');
        }}
        onSubmit={(username) => {
          handleShare(username);
        }}
        title="Share Item"
        label="Username"
        placeholder="Enter the username of the person you want to share with"
        validateInput={(value) => {
          const sanitized = sanitizeUsername(value);
          if (!sanitized) return 'Invalid username';
          return null;
        }}
        submitText="Share"
      />

      {/* Upload Dialog */}
      <Dialog
        open={uploadDialogOpen}
        onClose={handleUploadCancel}
        maxWidth="sm"
        fullWidth
        sx={{ zIndex: 9999 }}
      >
        <DialogTitle>Upload File</DialogTitle>
        <DialogContent>
          <Box sx={{ py: 2 }}>
            <Typography variant="body1" sx={{ mb: 2 }}>
              Select one or more files to upload to your drive.
            </Typography>

            <input
              accept="*/*"
              style={{ display: 'none' }}
              id="upload-file-input"
              type="file"
              multiple
              onChange={handleFileSelect}
            />
            <label htmlFor="upload-file-input">
              <Button
                variant="outlined"
                component="span"
                startIcon={<Upload />}
                fullWidth
                sx={{ mb: 3 }}
              >
                {selectedFiles.length > 0 ? `${selectedFiles.length} file${selectedFiles.length > 1 ? 's' : ''} selected` : 'Choose Files'}
              </Button>
            </label>

            {selectedFiles.length > 0 && (
              <Box sx={{ mb: 3, maxHeight: '200px', overflowY: 'auto' }}>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  Selected files:
                </Typography>
                {selectedFiles.map((file, index) => (
                  <Box key={index} sx={{ mb: 1, pl: 1 }}>
                    <Typography variant="body2">
                      • {file.name}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {utils.formatFileSize(file.size)}
                    </Typography>
                  </Box>
                ))}
              </Box>
            )}

            <Divider sx={{ my: 2 }} />

            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
              {aiModeEnabled ? (
                <Psychology sx={{ color: 'primary.main' }} />
              ) : (
                <SmartToy sx={{ color: 'text.secondary' }} />
              )}
              <Typography variant="subtitle2">
                AI Processing Options
              </Typography>
            </Box>

            <FormControlLabel
              control={
                <Switch
                  checked={aiModeEnabled}
                  onChange={handleAiModeToggle}
                  color="primary"
                />
              }
              label={
                <Box>
                  <Typography variant="body2">
                    {aiModeEnabled
                      ? "Enable AI processing for this file"
                      : "Skip AI processing for this file"
                    }
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {aiModeEnabled
                      ? "File will be processed for AI chat capabilities. Supported formats: PDF, DOCX, TXT"
                      : "File will be stored without AI processing. You can still chat with other processed files."
                    }
                  </Typography>
                </Box>
              }
              sx={{ alignItems: 'flex-start' }}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleUploadCancel}>Cancel</Button>
          <Button
            onClick={handleUploadConfirm}
            variant="contained"
            disabled={selectedFiles.length === 0}
          >
            Upload
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        open={deleteConfirmOpen}
        onClose={() => {
          setDeleteConfirmOpen(false);
          setItemToDelete(null);
        }}
        onConfirm={handleConfirmDelete}
        title="Delete Item"
        message={`Are you sure you want to delete "${itemToDelete?.name}"? This action cannot be undone.`}
        confirmText="Delete"
        confirmColor="error"
      />

      {/* Snackbar for notifications */}
      {snackbar.open && (
        <Box
          sx={{
            position: 'fixed',
            bottom: 24,
            left: 24,
            zIndex: 1400,
          }}
        >
          <Paper
            sx={{
              p: 2,
              display: 'flex',
              alignItems: 'center',
              gap: 2,
              minWidth: 288,
              bgcolor: snackbar.severity === 'error' ? 'error.main' :
                       snackbar.severity === 'success' ? 'success.main' :
                       snackbar.severity === 'warning' ? 'warning.main' : 'info.main',
              color: 'white',
            }}
          >
            <Typography variant="body2">{snackbar.message}</Typography>
            <Button size="small" onClick={closeSnackbar} sx={{ color: 'white', minWidth: 'auto' }}>
              ✕
            </Button>
          </Paper>
        </Box>
      )}

      {/* Context Menu */}
      {isMenuOpen && (
        <ClickAwayListener onClickAway={handleMenuClose}>
          <Paper
            sx={{
              position: 'fixed',
              top: menuAnchorEl?.getBoundingClientRect().top,
              left: menuAnchorEl?.getBoundingClientRect().left,
              zIndex: 1300,
              minWidth: 200,
            }}
          >
            {selectedItem && (
              <MenuItem onClick={handleDownloadFromMenu}>
                <Download sx={{ mr: 2 }} />
                {selectedItem.is_folder ? 'Download as ZIP' : 'Download'}
              </MenuItem>
            )}
            <MenuItem onClick={() => setShareDialogOpen(true)}>
              <Share sx={{ mr: 2 }} />
              Share
            </MenuItem>
            <MenuItem onClick={handleDeleteClick} sx={{ color: 'error.main' }}>
              <Delete sx={{ mr: 2 }} />
              Delete
            </MenuItem>
          </Paper>
        </ClickAwayListener>
      )}
    </Container>
  );
};

FileExplorer.propTypes = {};

export default FileExplorer;
