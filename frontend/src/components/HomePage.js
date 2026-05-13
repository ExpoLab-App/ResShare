import React, { useState, useEffect, useCallback } from 'react';
import {
  Container,
  Grid,
  Paper,
  Typography,
  Box,
  SpeedDial,
  SpeedDialAction,
  SpeedDialIcon,
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
  Psychology,
  SmartToy,
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

const HomePage = () => {
  const navigate = useNavigate();
  const { user, rootData, shareList, setRootData, setShareList, refreshShareList } = useAuth();
  const [speedDialOpen, setSpeedDialOpen] = useState(false);
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
    setSpeedDialOpen(false);
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
    setSpeedDialOpen(false);
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

  const renderRootItems = () => {
    if (!rootData || !rootData.children) return null;

    return Object.entries(rootData.children).map(([name, item]) => (
      <Grid item xs={12} sm={6} md={4} lg={3} key={name}>
        <Card
          sx={{
            height: '100%',
            transition: 'all 0.3s ease',
            '&:hover': {
              transform: 'translateY(-4px)',
              boxShadow: 6,
            },
          }}
        >
          <Box sx={{ position: 'relative' }}>
            <CardActionArea
              onClick={() => handleFileClick(name, item)}
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
                  <InsertDriveFile sx={{ fontSize: 48, color: 'text.secondary' }} />
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

  const renderSharedItems = () => {
    let sharedItemsArray = [];

    if (shareList && typeof shareList === 'object') {
      Object.entries(shareList).forEach(([fromUser, nodes]) => {
        if (Array.isArray(nodes)) {
          nodes.forEach(node => {
            sharedItemsArray.push({
              name: node.name || 'Shared Item',
              sharedBy: fromUser,
              node: node,
              is_folder: node.is_folder
            });
          });
        }
      });
    }

    if (sharedItemsArray.length === 0) {
      return (
        <Typography variant="body2" color="text.secondary" sx={{ p: 2 }}>
          No shared items yet
        </Typography>
      );
    }

    return (
      <Grid container spacing={2}>
        {sharedItemsArray.map((item, index) => (
          <Grid item xs={12} sm={6} md={4} lg={3} key={index}>
            <Card
              sx={{
                height: '100%',
                transition: 'all 0.3s ease',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: 6,
                },
              }}
            >
              <Box sx={{ position: 'relative' }}>
                <CardActionArea
                  onClick={() => item.is_folder ? handleFolderClick(`${item.sharedBy}/${item.name}`) : handleDownload(item)}
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
                      <InsertDriveFile sx={{ fontSize: 48, color: 'text.secondary' }} />
                    )}
                    <Typography
                      variant="subtitle1"
                      align="center"
                      sx={{
                        fontWeight: 500,
                        wordBreak: 'break-word',
                      }}
                    >
                      {item.name}
                    </Typography>
                    <Typography
                      variant="caption"
                      color="text.secondary"
                      align="center"
                    >
                      Shared by {item.sharedBy}
                    </Typography>
                    {!item.is_folder && item.node.file_obj && (
                      <Chip
                        label={`${(item.node.file_obj.size / 1024).toFixed(1)} KB`}
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
                      onClick={(e) => handleMenuOpen(e, item, true)}
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
        ))}
      </Grid>
    );
  };

  const speedDialActions = [
    {
      icon: <CreateNewFolder />,
      name: 'Create Folder',
      onClick: handleCreateFolder,
    },
    {
      icon: <Upload />,
      name: 'Upload File',
      onClick: handleUploadFile,
    },
  ];

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Hidden file input */}
      <input
        type="file"
        ref={fileInputRef}
        style={{ display: 'none' }}
        onChange={handleFileSelected}
        title="Maximum file size: 1 MB"
        multiple
      />

      {/* Welcome Section */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 600, mb: 1 }}>
          Welcome back, {user}!
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Manage your files and folders with ease
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* Left Side - My Files and Shared With Me */}
        <Grid item size={{ xs: 12, sm: 9 }}>
          {/* My Files Section */}
          <Paper sx={{ p: 3, mb: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
              <Storage sx={{ mr: 2, color: 'primary.main' }} />
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                My Files
              </Typography>
            </Box>
            <Box sx={{ mb: 2, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Typography variant="body2" color="text.secondary">
                Maximum file size: 1 MB
              </Typography>

              {/* AI Processing Toggle */}
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
            </Box>
            <Grid container spacing={2}>
              {renderRootItems()}
              {(!rootData || !rootData.children || Object.keys(rootData.children).length === 0) && (
                <Grid item xs={12}>
                  <Box
                    sx={{
                      textAlign: 'center',
                      py: 6,
                      color: 'text.secondary',
                    }}
                  >
                    <Storage sx={{ fontSize: 64, mb: 2, opacity: 0.5 }} />
                    <Typography variant="h6" sx={{ mb: 1 }}>
                      No files yet
                    </Typography>
                    <Typography variant="body2" sx={{ mb: 2 }}>
                      Start by creating a folder or uploading a file
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Maximum file size: 1 MB
                    </Typography>
                  </Box>
                </Grid>
              )}
            </Grid>
          </Paper>

          {/* Shared with Me Section */}
          <Paper sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
              <Share sx={{ mr: 2, color: 'secondary.main' }} />
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Shared with Me
              </Typography>
            </Box>
            {renderSharedItems()}
          </Paper>
        </Grid>

        {/* Right Side - Stats Cards */}
        <Grid item size={{ xs: 12, sm: 3 }}>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Paper
                sx={{
                  p: 3,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 2,
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  color: 'white',
                }}
              >
                <Storage sx={{ fontSize: 40 }} />
                <Box>
                  <Typography variant="h4" sx={{ fontWeight: 600 }}>
                    {stats.totalFiles}
                  </Typography>
                  <Typography variant="body2">Total Files</Typography>
                </Box>
              </Paper>
            </Grid>
            <Grid item xs={12}>
              <Paper
                sx={{
                  p: 3,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 2,
                  background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
                  color: 'white',
                }}
              >
                <Folder sx={{ fontSize: 40 }} />
                <Box>
                  <Typography variant="h4" sx={{ fontWeight: 600 }}>
                    {stats.totalFolders}
                  </Typography>
                  <Typography variant="body2">Total Folders</Typography>
                </Box>
              </Paper>
            </Grid>
            <Grid item xs={12}>
              <Paper
                sx={{
                  p: 3,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 2,
                  background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
                  color: 'white',
                }}
              >
                <People sx={{ fontSize: 40 }} />
                <Box>
                  <Typography variant="h4" sx={{ fontWeight: 600 }}>
                    {stats.sharedItems}
                  </Typography>
                  <Typography variant="body2">Shared Items</Typography>
                </Box>
              </Paper>
            </Grid>
          </Grid>
        </Grid>
      </Grid>

      {/* Speed Dial for Actions */}
      <SpeedDial
        ariaLabel="File actions"
        sx={{ position: 'fixed', bottom: 24, right: 24 }}
        icon={<SpeedDialIcon />}
        onClose={() => setSpeedDialOpen(false)}
        onOpen={() => setSpeedDialOpen(true)}
        open={speedDialOpen}
      >
        {speedDialActions.map((action) => (
          <SpeedDialAction
            key={action.name}
            icon={action.icon}
            tooltipTitle={action.name}
            onClick={action.onClick}
          />
        ))}
      </SpeedDial>

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
            borderRadius: 2,
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
