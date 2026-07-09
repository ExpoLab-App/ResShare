import React, { useState, useEffect, useCallback } from 'react';
import {
  Container,
  Paper,
  Typography,
  Box,
  Card,
  CardActionArea,
  Chip,
  IconButton,
  Tooltip,
  Button,
  LinearProgress,
  MenuItem,
  FormControlLabel,
  Switch,
  ClickAwayListener,
} from '@mui/material';
import {
  CreateNewFolder,
  Upload,
  Folder,
  InsertDriveFile,
  Share,
  People,
  Storage,
  Delete,
  MoreVert,
  Download,
  ChevronRight,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
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

const HomePage = () => {
  const navigate = useNavigate();
  const { user, rootData, shareList, setRootData, setShareList, refreshShareList } = useAuth();
  const [createFolderOpen, setCreateFolderOpen] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [stats, setStats] = useState({
    totalFiles: 0,
    totalFolders: 0,
    sharedItems: 0,
  });
  const fileInputRef = React.useRef(null);
  const [shareDialogOpen, setShareDialogOpen] = useState(false);
  const [shareUsername, setShareUsername] = useState('');
  const [aiModeEnabled, setAiModeEnabled] = useState(() =>
    safeParseBooleanFromStorage('aiModeEnabled', true)
  );
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [itemToDelete, setItemToDelete] = useState(null);

  // Custom hooks
  const { snackbar, showSuccess, showError, closeSnackbar } = useSnackbar();
  const { downloadFile } = useFileDownload(showError);
  const { menuAnchorEl, selectedItem, isMenuOpen, handleMenuOpen, handleMenuClose, clearSelection } = useItemContextMenu();

  useEffect(() => {
    const fetchSharedItems = async () => {
      if (!refreshShareList) return;
      try {
        await refreshShareList();
      } catch (error) {
        logger.error('Failed to refresh shared items on home', error);
      }
    };

    fetchSharedItems();
  }, [refreshShareList]);

  const calculateStats = useCallback((node) => {
    let files = 0;
    let folders = 0;

    const traverse = (currentNode) => {
      if (currentNode.is_folder) {
        folders++;
        if (currentNode.children) {
          Object.values(currentNode.children).forEach(child => traverse(child));
        }
      } else {
        files++;
      }
    };

    if (node.children) {
      Object.values(node.children).forEach(child => traverse(child));
    }

    // Calculate shared items count from shareList object
    let sharedItemsCount = 0;
    if (shareList && typeof shareList === 'object') {
      Object.values(shareList).forEach(nodes => {
        if (Array.isArray(nodes)) {
          sharedItemsCount += nodes.length;
        }
      });
    }

    setStats({
      totalFiles: files,
      totalFolders: folders,
      sharedItems: sharedItemsCount,
    });
  }, [shareList]);

  useEffect(() => {
    if (rootData) {
      calculateStats(rootData);
    }
  }, [rootData, calculateStats]);

  const handleCreateFolder = () => {
    setCreateFolderOpen(true);
  };

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
      const response = await fileAPI.createFolder(sanitized);

      if (response.result === 'SUCCESS') {
        setRootData(JSON.parse(response.root));
        showSuccess('Folder created successfully!');
        setCreateFolderOpen(false);
      } else {
        showError(getBackendErrorMessage(response.result) || 'Failed to create folder');
      }
    } catch (error) {
      showError(getErrorMessage(error, 'Failed to create folder'));
    }
  };

  const handleUploadFile = () => {
    // Trigger file input click
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const handleFileSelected = async (event) => {
    const files = Array.from(event.target.files);
    if (!files || files.length === 0) return;

    // Validate all files first
    for (const file of files) {
      const sizeValidation = utils.validateFileSize(file, 1);
      if (!sizeValidation.isValid) {
        showError(`${file.name}: ${sizeValidation.error}`);
        if (fileInputRef.current) {
          fileInputRef.current.value = '';
        }
        return;
      }
    }

    setUploading(true);
    setUploadProgress(0);

    const totalFiles = files.length;
    let uploadedFiles = 0;
    let failedFiles = [];

    try {
      for (const file of files) {
        try {
          logger.debug('[HomePage] Uploading with aiModeEnabled=', aiModeEnabled, 'skip=', !aiModeEnabled);
          const response = await fileAPI.uploadFile(file, '', !aiModeEnabled);

          if (response.message === 'SUCCESS') {
            setRootData(JSON.parse(response.root));
            uploadedFiles++;
          } else {
            failedFiles.push(file.name);
            logger.warn('[HomePage] Non-success response:', response);
          }
        } catch (error) {
          logger.error('[HomePage] Error uploading file:', file.name, error);
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
        } else {
          message += ' AI processing was skipped.';
        }
        showSuccess(message);
      } else if (uploadedFiles > 0) {
        showError(`Uploaded ${uploadedFiles} file(s), but ${failedFiles.length} failed: ${failedFiles.join(', ')}`);
      } else {
        showError(`Failed to upload all files: ${failedFiles.join(', ')}`);
      }
    } catch (error) {
      showError(getErrorMessage(error, 'Failed to upload files'));
    } finally {
      setUploading(false);
      setTimeout(() => setUploadProgress(0), 1000);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleFolderClick = (folderName) => {
    navigate(`/explorer/${folderName}`);
  };

  const handleFileClick = (fileName, item) => {
    if (item.is_folder) {
      handleFolderClick(fileName);
    } else {
      handleDownload({ name: fileName, ...item });
    }
  };

  const handleDeleteClick = (item) => {
    setItemToDelete(item);
    setDeleteConfirmOpen(true);
    handleMenuClose();
  };

  const handleConfirmDelete = async () => {
    if (!itemToDelete) return;

    try {
      const response = await fileAPI.deleteItem(
        itemToDelete.isShared ? itemToDelete.sharedBy + "/" + itemToDelete.name : itemToDelete.name,
        !itemToDelete.isShared
      );

      if (response.message === 'SUCCESS') {
        if (itemToDelete.isShared) {
          // Update share list
          const updatedShareList = { ...shareList };
          const fromUser = itemToDelete.sharedBy;
          if (updatedShareList[fromUser]) {
            updatedShareList[fromUser] = updatedShareList[fromUser].filter(
              node => node.name !== itemToDelete.name
            );
            if (updatedShareList[fromUser].length === 0) {
              delete updatedShareList[fromUser];
            }
          }
          setShareList(updatedShareList);
        } else {
          // Update root data
          setRootData(JSON.parse(response.root));
        }

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

  const handleDownload = async (itemOrEvent) => {
    // If it's an event from the menu, use selectedItem
    const item = itemOrEvent?.target?.tagName ? selectedItem : itemOrEvent;
    if (!item) return;

    try {
      logger.debug("item", item);
      // Check if the item is from shared items section
      const isShared = item.sharedBy !== undefined;
      const itemPath = isShared
        ? `${item.sharedBy}/${item.name}`
        : item.name;
      logger.debug("itemPath", itemPath, "isShared", isShared);

      if (item.is_folder || item.node?.is_folder) {
        // Download folder as ZIP
        const response = await fileAPI.downloadFolderAsZip(itemPath, isShared);
        const blob = await response.blob();

        // Trigger download
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${item.name}.zip`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        showSuccess(`Downloaded "${item.name}" as ZIP successfully`);
      } else {
        // Download single file
        const result = await downloadFile(itemPath, item.name, isShared);
        if (result.success && !result.cancelled) {
          showSuccess(`Downloaded "${item.name}" successfully`);
        }
      }
    } catch (error) {
      showError(getErrorMessage(error, `Failed to download "${item.name}"`));
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
    const itemToShare = selectedItem.isShared ? selectedItem.node : selectedItem;
    logger.debug("itemToShare:", itemToShare);

    try {
      const pathToShare = selectedItem?.isShared
        ? `${selectedItem.sharedBy}/${selectedItem.name}`
        : selectedItem?.name;

      const data = await fileAPI.shareItem(sanitized, itemToShare, pathToShare);

      if (data.message === 'SUCCESS') {
        showSuccess('Item shared successfully!');
        setShareDialogOpen(false);
        setShareUsername('');
      } else {
        showError(getBackendErrorMessage(data.message) || 'Failed to share item');
      }
    } catch (error) {
      showError(getErrorMessage(error, 'Network error. Please try again.'));
    }
    handleMenuClose();
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

  const statCardSx = (color) => ({
    p: 2,
    borderRadius: 2,
    boxShadow: 'none',
    borderLeft: '4px solid',
    borderLeftColor: color,
    backgroundColor: 'background.paper',
  });

  const renderRootItems = () => {
    if (!rootData || !rootData.children) return null;

    return Object.entries(rootData.children).map(([name, item]) => (
      <Card
        key={name}
        sx={fileCardSx}
      >
        <Box sx={{ position: 'relative' }}>
          <CardActionArea
            onClick={() => handleFileClick(name, item)}
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
                  <Folder sx={{ fontSize: 30, color: 'primary.main' }} />
                ) : (
                  <InsertDriveFile sx={{ fontSize: 30, color: 'secondary.main' }} />
                )}
              </Box>
              <Box sx={{ minWidth: 0, pr: 3 }}>
                <Typography
                  variant="subtitle2"
                  sx={{
                    fontWeight: 800,
                    wordBreak: 'break-word',
                    lineHeight: 1.25,
                    mb: 0.75,
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
                sx={menuButtonSx}
              >
                <MoreVert />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>
      </Card>
    ));
  };

  const renderSharedItems = () => {
    const sharedOwners = Object.entries(shareList || {}).filter(
      ([, nodes]) => Array.isArray(nodes) && nodes.length > 0
    );

    if (sharedOwners.length === 0) {
      return (
        <Typography variant="body2" color="text.secondary" sx={{ p: 2 }}>
          No shared items yet
        </Typography>
      );
    }

    return (
      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: { xs: '1fr', sm: 'repeat(auto-fit, minmax(220px, 1fr))' },
          gap: 1.5,
        }}
      >
        {sharedOwners.map(([fromUser, nodes]) => {
          const folderCount = nodes.filter((node) => node.is_folder).length;
          const itemLabel = `${nodes.length} item${nodes.length === 1 ? '' : 's'} shared`;
          const typeLabel = folderCount
            ? `${folderCount} folder${folderCount === 1 ? '' : 's'}`
            : 'Files only';

          return (
            <Card sx={fileCardSx} key={fromUser}>
              <CardActionArea
                onClick={() => navigate(`/shared/${encodeURIComponent(fromUser)}`)}
                aria-label={`View items shared by ${fromUser}`}
                sx={{ height: '100%', p: 2 }}
              >
                <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1.5 }}>
                  <Box
                    sx={{
                      ...iconFrameSx,
                      backgroundColor: (theme) => theme.palette.mode === 'dark'
                        ? 'rgba(232, 186, 117, 0.12)'
                        : 'rgba(168, 117, 50, 0.09)',
                      border: (theme) => theme.palette.mode === 'dark'
                        ? '1px solid rgba(232, 186, 117, 0.18)'
                        : '1px solid rgba(168, 117, 50, 0.14)',
                    }}
                  >
                    <People sx={{ fontSize: 30, color: 'secondary.main' }} />
                  </Box>
                  <Box sx={{ minWidth: 0, pr: 3 }}>
                    <Typography
                      variant="subtitle2"
                      sx={{
                        fontWeight: 800,
                        wordBreak: 'break-word',
                        lineHeight: 1.25,
                        mb: 0.5,
                      }}
                    >
                      {fromUser}
                    </Typography>
                    <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                      {itemLabel}
                    </Typography>
                    <Chip
                      label={typeLabel}
                      size="small"
                      variant="outlined"
                      sx={{ mt: 0.75, width: 'fit-content' }}
                    />
                  </Box>
                </Box>
                <ChevronRight
                  aria-hidden="true"
                  sx={{ position: 'absolute', top: 16, right: 12, color: 'text.secondary' }}
                />
              </CardActionArea>
            </Card>
          );
        })}
      </Box>
    );
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
      {/* Hidden file input */}
      <input
        type="file"
        ref={fileInputRef}
        style={{ display: 'none' }}
        onChange={handleFileSelected}
        title="Maximum file size: 1 MB"
        multiple
      />

      <Box sx={{ display: 'grid', gap: 2.5 }}>
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: { xs: '1fr', lg: 'minmax(0, 1fr) 280px' },
            gap: 2.5,
            alignItems: 'start',
          }}
        >
          <Box sx={{ display: 'grid', gap: 2.5, minWidth: 0 }}>
            <Paper sx={sectionSx}>
              <Box
                sx={{
                  display: 'flex',
                  flexDirection: { xs: 'column', sm: 'row' },
                  alignItems: { xs: 'flex-start', sm: 'center' },
                  justifyContent: 'space-between',
                  gap: 1.5,
                  mb: 2,
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.25 }}>
                  <Storage sx={{ color: 'primary.main' }} />
                  <Box>
                    <Typography variant="h6">My Files</Typography>
                    <Typography variant="body2" color="text.secondary">
                      Maximum file size: 1 MB
                    </Typography>
                  </Box>
                </Box>

                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={aiModeEnabled}
                        onChange={(e) => {
                          const enabled = e.target.checked;
                          logger.debug('[HomePage] AI toggle changed to', enabled);
                          setAiModeEnabled(enabled);
                          localStorage.setItem('aiModeEnabled', JSON.stringify(enabled));
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
                    onClick={handleUploadFile}
                  >
                    Upload
                  </Button>
                  <Button
                    variant="outlined"
                    startIcon={<CreateNewFolder />}
                    onClick={handleCreateFolder}
                  >
                    New Folder
                  </Button>
                </Box>
              </Box>

              <Box
                sx={{
                  display: 'grid',
                  gridTemplateColumns: { xs: '1fr', sm: 'repeat(auto-fit, minmax(220px, 1fr))' },
                  gap: 1.5,
                  alignItems: 'stretch',
                }}
              >
                {renderRootItems()}
                {(!rootData || !rootData.children || Object.keys(rootData.children).length === 0) && (
                  <Box
                    sx={{
                      gridColumn: '1 / -1',
                      border: '1px dashed',
                      borderColor: 'divider',
                      borderRadius: 2,
                      p: { xs: 3, md: 4 },
                      color: 'text.secondary',
                      textAlign: 'center',
                    }}
                  >
                    <Storage sx={{ fontSize: 42, mb: 1, opacity: 0.55 }} />
                    <Typography variant="h6" sx={{ mb: 0.5 }}>
                      No files yet
                    </Typography>
                    <Typography variant="body2">
                      Upload a file or create a folder to start.
                    </Typography>
                  </Box>
                )}
              </Box>
            </Paper>

            <Paper sx={sectionSx}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.25, mb: 2 }}>
                <Share sx={{ color: 'secondary.main' }} />
                <Box>
                  <Typography variant="h6">Shared with Me</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Files and folders shared by other users.
                  </Typography>
                </Box>
              </Box>
              {renderSharedItems()}
            </Paper>
          </Box>

          <Paper
            sx={{
              ...sectionSx,
              position: { lg: 'sticky' },
              top: { lg: 88 },
            }}
          >
            <Typography variant="h6" sx={{ mb: 2 }}>
              At a glance
            </Typography>
            <Box sx={{ display: 'grid', gap: 1.5 }}>
              <Box sx={statCardSx('primary.main')}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                  <Storage sx={{ color: 'primary.main' }} />
                  <Box>
                    <Typography variant="h4">{stats.totalFiles}</Typography>
                    <Typography variant="body2" color="text.secondary">Total Files</Typography>
                  </Box>
                </Box>
              </Box>
              <Box sx={statCardSx('secondary.main')}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                  <Folder sx={{ color: 'secondary.main' }} />
                  <Box>
                    <Typography variant="h4">{stats.totalFolders}</Typography>
                    <Typography variant="body2" color="text.secondary">Total Folders</Typography>
                  </Box>
                </Box>
              </Box>
              <Box sx={statCardSx('info.main')}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                  <People sx={{ color: 'info.main' }} />
                  <Box>
                    <Typography variant="h4">{stats.sharedItems}</Typography>
                    <Typography variant="body2" color="text.secondary">Shared Items</Typography>
                  </Box>
                </Box>
              </Box>
            </Box>
          </Paper>
        </Box>
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

      {/* Upload Progress */}
      {uploading && (
        <Box
          sx={{
            position: 'fixed',
            bottom: 90,
            right: 24,
            minWidth: 300,
            bgcolor: 'background.paper',
            borderRadius: 1,
            boxShadow: 3,
            p: 2,
            zIndex: 1300,
          }}
        >
          <Typography variant="body2" sx={{ mb: 1 }}>
            Uploading file...
          </Typography>
          <LinearProgress variant="determinate" value={uploadProgress} />
          <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
            {uploadProgress}% complete
          </Typography>
        </Box>
      )}

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
      {isMenuOpen && (
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
              <MenuItem onClick={handleDownload}>
                <Download sx={{ mr: 2 }} />
                {selectedItem.is_folder || selectedItem.node?.is_folder ? 'Download as ZIP' : 'Download'}
              </MenuItem>
            )}
            <MenuItem onClick={() => setShareDialogOpen(true)}>
              <Share sx={{ mr: 2 }} />
              Share
            </MenuItem>
            <MenuItem onClick={() => handleDeleteClick(selectedItem)} sx={{ color: 'error.main' }}>
              <Delete sx={{ mr: 2 }} />
              Delete
            </MenuItem>
          </Paper>
        </ClickAwayListener>
      )}

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
    </Container>
  );
};

HomePage.propTypes = {};

export default HomePage;
