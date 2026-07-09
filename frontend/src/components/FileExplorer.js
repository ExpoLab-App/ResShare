import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Container,
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
  FolderShared,
  LockOutlined,
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
import AIAssistantIcon from './AIAssistantIcon';

const decodeRouteSegment = (segment) => {
  try {
    return decodeURIComponent(segment);
  } catch {
    return segment;
  }
};

const EMPTY_SHARED_ITEMS = [];

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

  const sharedRoute = useMemo(() => {
    const prefix = '/shared/';
    if (!location.pathname.startsWith(prefix)) return null;

    const segments = location.pathname
      .slice(prefix.length)
      .split('/')
      .filter(Boolean)
      .map(decodeRouteSegment);

    if (!segments[0]) return null;

    const owner = segments[0];
    const routePath = segments.slice(1).join('/');
    const sharedItems = shareList?.[owner] || EMPTY_SHARED_ITEMS;
    const matchedRoot = routePath
      ? sharedItems
        .filter((item) => {
          const itemPath = item.shared_path || item.name;
          return routePath === itemPath || routePath.startsWith(`${itemPath}/`);
        })
        .sort((left, right) => {
          const leftPath = left.shared_path || left.name;
          const rightPath = right.shared_path || right.name;
          return rightPath.length - leftPath.length;
        })[0]
      : null;
    const rootPath = matchedRoot?.shared_path || matchedRoot?.name || routePath;
    const descendants = matchedRoot
      ? routePath.slice(rootPath.length).split('/').filter(Boolean)
      : [];

    return {
      owner,
      rootPath,
      descendants,
    };
  }, [location.pathname, shareList]);

  const isSharedView = Boolean(sharedRoute);
  const sharedOwnerItems = sharedRoute
    ? shareList?.[sharedRoute.owner] || EMPTY_SHARED_ITEMS
    : EMPTY_SHARED_ITEMS;
  const sharedRoot = useMemo(() => {
    if (!sharedRoute?.rootPath) return null;

    return sharedOwnerItems.find(
      (item) => (item.shared_path || item.name) === sharedRoute.rootPath
    ) || null;
  }, [sharedOwnerItems, sharedRoute]);

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
    if (sharedRoute) {
      const { owner, rootPath, descendants } = sharedRoute;
      setCurrentPath(rootPath ? [rootPath, ...descendants].join('/') : '');

      if (!rootPath) {
        const children = sharedOwnerItems.reduce((items, item) => {
          const itemKey = item.shared_path || item.name;
          if (itemKey) {
            items[itemKey] = item;
          }
          return items;
        }, {});

        setCurrentNode({
          name: owner,
          is_folder: true,
          children,
        });
        return;
      }

      const node = sharedRoot
        ? findNodeByPath(sharedRoot, descendants.join('/'))
        : null;
      setCurrentNode(node);
      return;
    }

    const path = location.pathname.replace('/explorer/', '').replace('/explorer', '');
    setCurrentPath(path);

    const node = rootData ? findNodeByPath(rootData, path) : null;
    setCurrentNode(node);
  }, [location.pathname, rootData, sharedOwnerItems, sharedRoot, sharedRoute, findNodeByPath]);

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

  const navigateToSharedPath = useCallback((rootPath = '', descendants = []) => {
    if (!sharedRoute?.owner) {
      navigate('/home');
      return;
    }

    const routePath = [
      sharedRoute.owner,
      ...rootPath.split('/').filter(Boolean),
      ...descendants,
    ]
      .map(encodeURIComponent)
      .join('/');
    navigate(`/shared/${routePath}`);
  }, [navigate, sharedRoute]);

  const handleBreadcrumbClick = useCallback((index) => {
    const parts = getPathParts();
    const newPath = parts.slice(0, index + 1).join('/');
    navigate(`/explorer/${newPath}`);
  }, [getPathParts, navigate]);

  const handleBack = useCallback(() => {
    if (!sharedRoute) {
      navigate('/home');
      return;
    }

    if (sharedRoute.descendants.length > 0) {
      navigateToSharedPath(sharedRoute.rootPath, sharedRoute.descendants.slice(0, -1));
    } else if (sharedRoute.rootPath) {
      navigateToSharedPath();
    } else {
      navigate('/home');
    }
  }, [navigate, navigateToSharedPath, sharedRoute]);

  const handleDownloadFile = useCallback(async (fileName, sharedSourcePath) => {
    try {
      const isShared = Boolean(sharedRoute);
      const filePath = isShared
        ? [
            sharedRoute.owner,
            sharedSourcePath || sharedRoute.rootPath,
            ...(sharedSourcePath ? [] : sharedRoute.descendants),
            ...(sharedSourcePath ? [] : [fileName]),
          ].filter(Boolean).join('/')
        : currentPath ? `${currentPath}/${fileName}` : fileName;

      // Call downloadFile with (path, filename, isShared)
      const result = await downloadFile(filePath, fileName, isShared);
      if (result.success && !result.cancelled) {
        showSuccess(`Downloaded "${fileName}" successfully`);
      }
    } catch (error) {
      showError(getErrorMessage(error, `Failed to download "${fileName}"`));
    }
  }, [currentPath, downloadFile, sharedRoute, showSuccess, showError]);

  const handleItemClick = useCallback((itemName, item) => {
    if (item.is_folder) {
      if (sharedRoute) {
        if (!sharedRoute.rootPath) {
          navigateToSharedPath(item.shared_path || itemName);
        } else {
          navigateToSharedPath(sharedRoute.rootPath, [...sharedRoute.descendants, itemName]);
        }
        return;
      }

      const newPath = currentPath ? `${currentPath}/${itemName}` : itemName;
      navigate(`/explorer/${newPath}`);
    } else {
      // Handle file click (preview or download)
      handleDownloadFile(
        itemName,
        sharedRoute && !sharedRoute.rootPath ? item.shared_path : undefined
      );
    }
  }, [currentPath, handleDownloadFile, navigate, navigateToSharedPath, sharedRoute]);

  const handleConfirmCreateFolder = async (folderName) => {
    if (isSharedView) {
      showError('Shared items are read-only');
      return;
    }

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
    if (isSharedView) {
      showError('Shared items are read-only');
      return;
    }

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
    if (isSharedView) {
      showError('Shared items are read-only');
      return;
    }

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
    if (isSharedView) return;
    if (!selectedItem) return;

    try {
      const itemPath = currentPath ? `${currentPath}/${selectedItem.name}` : selectedItem.name;

      if (selectedItem.is_folder) {
        // Download folder as ZIP
        const response = await fileAPI.downloadFolderAsZip(itemPath, false);
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
        const result = await downloadFile(itemPath, selectedItem.name, false);
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
    if (isSharedView) {
      showError('Shared items are read-only');
      return;
    }

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
    if (isSharedView) {
      showError('Shared items are read-only');
      return;
    }

    if (!selectedItem) return;
    setItemToDelete(selectedItem);
    setDeleteConfirmOpen(true);
    handleMenuClose();
  };

  const handleConfirmDelete = async () => {
    if (isSharedView) {
      showError('Shared items are read-only');
      return;
    }

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

  const sectionSx = {
    p: { xs: 2, md: 2.5 },
    borderRadius: 2,
    backgroundColor: 'background.paper',
  };

  const fileCardSx = {
    width: '100%',
    minHeight: 124,
    borderRadius: 1,
    backgroundColor: 'background.paper',
    boxShadow: 'none',
    transition: 'transform 160ms ease, border-color 160ms ease, background-color 160ms ease',
    '&:hover': {
      transform: 'translateY(-2px)',
      borderColor: 'primary.main',
      backgroundColor: 'action.hover',
    },
  };

  const iconFrameSx = {
    width: 46,
    height: 46,
    display: 'grid',
    placeItems: 'center',
    borderRadius: 1,
    backgroundColor: (theme) => theme.palette.mode === 'dark'
      ? 'rgba(142, 205, 247, 0.12)'
      : 'rgba(36, 111, 167, 0.08)',
    border: (theme) => theme.palette.mode === 'dark'
      ? '1px solid rgba(142, 205, 247, 0.2)'
      : '1px solid rgba(36, 111, 167, 0.14)',
  };

  const menuButtonSx = {
    bgcolor: (theme) => theme.palette.mode === 'dark'
      ? 'rgba(17, 20, 23, 0.9)'
      : 'rgba(255, 255, 255, 0.92)',
    border: '1px solid',
    borderColor: 'divider',
    '&:hover': {
      bgcolor: 'action.hover',
      borderColor: 'primary.main',
    },
  };

  const getFileIcon = (filename) => {
    const iconType = utils.getFileIcon(filename, false);

    switch (iconType) {
      case 'image':
        return <Image sx={{ fontSize: 34, color: 'primary.main' }} />;
      case 'pdf':
        return <PictureAsPdf sx={{ fontSize: 34, color: '#b64d42' }} />;
      case 'document':
        return <Description sx={{ fontSize: 34, color: 'primary.main' }} />;
      case 'spreadsheet':
        return <TableChart sx={{ fontSize: 34, color: '#6ba7cf' }} />;
      case 'presentation':
        return <Slideshow sx={{ fontSize: 34, color: '#b8832e' }} />;
      case 'code':
        return <Code sx={{ fontSize: 34, color: '#7c5c99' }} />;
      case 'archive':
        return <Archive sx={{ fontSize: 34, color: '#6f4d1e' }} />;
      case 'audio':
        return <Audiotrack sx={{ fontSize: 34, color: '#b64d42' }} />;
      case 'video':
        return <Movie sx={{ fontSize: 34, color: 'primary.main' }} />;
      default:
        return <InsertDriveFile sx={{ fontSize: 34, color: 'secondary.main' }} />;
    }
  };

  const renderItems = () => {
    const hasChildren = Boolean(currentNode?.children);
    const isEmpty = !hasChildren || Object.keys(currentNode.children).length === 0;

    if (isEmpty) {
      const isUnavailableSharedItem = isSharedView && !currentNode;
      const isSharedOwnerView = isSharedView && !sharedRoute?.rootPath;
      const title = isUnavailableSharedItem
        ? 'This shared item is no longer available'
        : isSharedOwnerView
          ? `No items shared by ${sharedRoute.owner}`
          : 'This folder is empty';
      const description = isUnavailableSharedItem
        ? 'It may have been removed by its owner.'
        : isSharedOwnerView
          ? 'This shared collection does not contain any items right now.'
          : isSharedView
            ? 'This shared folder does not contain any items.'
            : 'Upload files or create folders to get started.';

      return (
        <Box
          sx={{
            gridColumn: '1 / -1',
            textAlign: 'center',
            py: 7,
            px: 3,
            color: 'text.secondary',
            border: '1px dashed',
            borderColor: 'divider',
            borderRadius: 2,
          }}
        >
          {isSharedView ? (
            <FolderShared sx={{ fontSize: 48, mb: 1, opacity: 0.5 }} />
          ) : (
            <Folder sx={{ fontSize: 48, mb: 1, opacity: 0.5 }} />
          )}
          <Typography variant="h6" sx={{ mb: 0.75 }}>
            {title}
          </Typography>
          <Typography variant="body2" sx={{ mb: 1 }}>
            {description}
          </Typography>
          {!isSharedView && (
            <Typography variant="caption" color="text.secondary">
              Maximum file size: 1 MB
            </Typography>
          )}
        </Box>
      );
    }

    return Object.entries(currentNode.children).map(([key, item]) => {
      const itemName = item.name || key;
      const isSharedOwnerItem = isSharedView && !sharedRoute?.rootPath;

      return (
        <Card
          sx={fileCardSx}
          key={item.shared_path || key}
        >
          <Box sx={{ position: 'relative' }}>
            <CardActionArea
              onClick={() => handleItemClick(itemName, item)}
              sx={{ height: '100%', p: 2 }}
            >
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: 1.5,
                }}
              >
                <Box sx={iconFrameSx}>
                  {item.is_folder ? (
                    isSharedOwnerItem ? (
                      <FolderShared sx={{ fontSize: 30, color: 'primary.main' }} />
                    ) : (
                      <Folder sx={{ fontSize: 30, color: 'primary.main' }} />
                    )
                  ) : (
                    getFileIcon(itemName)
                  )}
                </Box>
                <Box sx={{ minWidth: 0, pr: isSharedView ? 0 : 3 }}>
                  <Typography
                    variant="subtitle2"
                    sx={{
                      fontWeight: 800,
                      wordBreak: 'break-word',
                      lineHeight: 1.25,
                      mb: 0.75,
                    }}
                  >
                    {itemName}
                  </Typography>
                  {!item.is_folder && item.file_obj && (
                    <Chip
                      label={`${(item.file_obj.size / 1024).toFixed(1)} KB`}
                      size="small"
                      variant="outlined"
                    />
                  )}
                </Box>
              </Box>
            </CardActionArea>
            {!isSharedView && (
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
                    onClick={(e) => handleMenuOpen(e, { name: itemName, ...item })}
                    size="small"
                    sx={menuButtonSx}
                  >
                    <MoreVert />
                  </IconButton>
                </Tooltip>
              </Box>
            )}
          </Box>
        </Card>
      );
    });
  };

  return (
    <Container
      maxWidth={false}
      sx={{
        py: { xs: 2, md: 3 },
        px: { xs: 2, md: 3, lg: 4 },
        width: '100%',
      }}
    >
      <Box sx={{ display: 'grid', gap: 2.5 }}>
        <Paper
          sx={{
            ...sectionSx,
            overflow: 'hidden',
            p: 0,
          }}
        >
          <Box
            sx={{
              display: 'flex',
              alignItems: { xs: 'flex-start', md: 'center' },
              flexDirection: { xs: 'column', md: 'row' },
              gap: 2,
              p: { xs: 2, md: 2.5 },
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.25, minWidth: 0, flex: 1 }}>
              <IconButton
                onClick={handleBack}
                sx={{
                  border: '1px solid',
                  borderColor: 'divider',
                  borderRadius: 1,
                  flexShrink: 0,
                }}
              >
                <ArrowBack />
              </IconButton>

              <Breadcrumbs
                separator={<NavigateNext fontSize="small" />}
                sx={{
                  minWidth: 0,
                  '& ol': {
                    flexWrap: 'nowrap',
                  },
                  '& li': {
                    minWidth: 0,
                  },
                }}
              >
            <Link
              component="button"
              variant="body1"
              onClick={() => navigate('/home')}
              sx={{
                display: 'flex',
                alignItems: 'center',
                textDecoration: 'none',
                color: 'primary.main',
                fontWeight: 800,
                '&:hover': { textDecoration: 'underline' },
              }}
            >
              <Home sx={{ mr: 0.5, fontSize: 20 }} />
              Home
            </Link>
            {isSharedView ? [
              <Link
                key="shared-with-me"
                component="button"
                variant="body1"
                onClick={() => navigate('/home')}
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  whiteSpace: 'nowrap',
                  textDecoration: 'none',
                  color: 'secondary.main',
                  fontWeight: 800,
                  '&:hover': { textDecoration: 'underline' },
                }}
              >
                <FolderShared sx={{ mr: 0.5, fontSize: 20 }} />
                Shared with Me
              </Link>,
              <Link
                key="shared-owner"
                component="button"
                variant="body1"
                onClick={() => navigateToSharedPath()}
                sx={{
                  whiteSpace: 'nowrap',
                  textDecoration: 'none',
                  color: 'primary.main',
                  fontWeight: 800,
                  '&:hover': { textDecoration: 'underline' },
                }}
              >
                {sharedRoute.owner}
              </Link>,
              ...(sharedRoute.rootPath ? [
                <Link
                  key="shared-root"
                  component="button"
                  variant="body1"
                  onClick={() => navigateToSharedPath(sharedRoute.rootPath)}
                  sx={{
                    whiteSpace: 'nowrap',
                    textDecoration: 'none',
                    color: 'text.primary',
                    fontWeight: 700,
                    '&:hover': { textDecoration: 'underline' },
                  }}
                >
                  {sharedRoot?.name || sharedRoute.rootPath.split('/').pop()}
                </Link>,
              ] : []),
              ...sharedRoute.descendants.map((part, index) => (
                <Link
                  key={`shared-descendant-${part}-${index}`}
                  component="button"
                  variant="body1"
                  onClick={() => navigateToSharedPath(
                    sharedRoute.rootPath,
                    sharedRoute.descendants.slice(0, index + 1)
                  )}
                  sx={{
                    whiteSpace: 'nowrap',
                    textDecoration: 'none',
                    color: 'text.primary',
                    fontWeight: 700,
                    '&:hover': { textDecoration: 'underline' },
                  }}
                >
                  {part}
                </Link>
              )),
            ] : (
              getPathParts().map((part, index) => (
                <Link
                  key={index}
                  component="button"
                  variant="body1"
                  onClick={() => handleBreadcrumbClick(index)}
                  sx={{
                    textDecoration: 'none',
                    color: 'text.primary',
                    fontWeight: 700,
                    '&:hover': { textDecoration: 'underline' },
                  }}
                >
                  {part}
                </Link>
              ))
            )}
              </Breadcrumbs>
            </Box>

            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
              {isSharedView ? (
                <>
                  <Chip
                    icon={<LockOutlined />}
                    label="Read only"
                    size="small"
                    variant="outlined"
                    color="primary"
                  />
                  <Typography variant="caption" color="text.secondary">
                    Shared by {sharedRoute.owner}
                  </Typography>
                </>
              ) : (
                <>
                  <Typography variant="caption" color="text.secondary">
                    Max: 1 MB
                  </Typography>

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
                        <AIAssistantIcon size={16} sx={{ opacity: aiModeEnabled ? 1 : 0.46 }} />
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

                  <Button
                    variant="outlined"
                    startIcon={<CreateNewFolder />}
                    onClick={() => setCreateFolderOpen(true)}
                  >
                    New Folder
                  </Button>
                </>
              )}
            </Box>
          </Box>

          {uploading && !isSharedView && (
            <LinearProgress
              variant="determinate"
              value={uploadProgress}
              sx={{ height: 3 }}
            />
          )}
        </Paper>

        <Paper sx={sectionSx}>
          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: { xs: '1fr', sm: 'repeat(auto-fit, minmax(220px, 1fr))' },
              gap: 1.5,
              alignItems: 'stretch',
            }}
          >
            {renderItems()}
          </Box>
        </Paper>
      </Box>

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
        PaperProps={{
          sx: {
            borderRadius: 1,
          },
        }}
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
                sx={{ mb: 3, justifyContent: 'center' }}
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
              <AIAssistantIcon size={24} sx={{ opacity: aiModeEnabled ? 1 : 0.46 }} />
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
              borderRadius: 1,
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
      {!isSharedView && isMenuOpen && (
        <ClickAwayListener onClickAway={handleMenuClose}>
          <Paper
            sx={{
              position: 'fixed',
              top: menuAnchorEl?.getBoundingClientRect().top,
              left: menuAnchorEl?.getBoundingClientRect().left,
              zIndex: 1300,
              minWidth: 200,
              borderRadius: 1,
              overflow: 'hidden',
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
