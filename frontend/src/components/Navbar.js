import React, { useState, useCallback } from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  Menu,
  MenuItem,
  Box,
  Avatar,
  Tooltip,
  Button,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  Brightness4,
  Brightness7,
  Home,
  Folder,
  Logout,
  Delete,
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth, useThemeMode } from '../App';
import { authAPI } from '../utils/api';
import { useTheme } from '@mui/material/styles';
import { logger } from '../utils/logger';
import { getErrorMessage } from '../utils/errorHandler';
import ConfirmDialog from './ConfirmDialog';

const Navbar = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();
  const { darkMode, toggleTheme } = useThemeMode();
  const [anchorEl, setAnchorEl] = useState(null);
  const [deleteAccountOpen, setDeleteAccountOpen] = useState(false);
  const [deletePasswordOpen, setDeletePasswordOpen] = useState(false);
  const [deletePassword, setDeletePassword] = useState('');
  const [deleteError, setDeleteError] = useState('');
  const theme = useTheme();

  const handleMenuOpen = useCallback((event) => {
    setAnchorEl(event.currentTarget);
  }, []);

  const handleMenuClose = useCallback(() => {
    setAnchorEl(null);
  }, []);

  const handleLogout = useCallback(async () => {
    try {
      await authAPI.logout();
      logger.info('Logout', 'User logged out successfully');
    } catch (error) {
      logger.error('Logout', error);
      const errorMessage = getErrorMessage(error, 'Logout failed');
      logger.error('Logout Error', errorMessage);
    }
    logout();
    navigate('/login');
    handleMenuClose();
  }, [logout, navigate, handleMenuClose]);

  const handleDeleteAccountClick = useCallback(() => {
    handleMenuClose();
    setDeleteAccountOpen(true);
  }, [handleMenuClose]);

  const handleDeleteAccountConfirm = useCallback(() => {
    setDeleteAccountOpen(false);
    setDeletePasswordOpen(true);
  }, []);

  const handleDeleteAccountCancel = useCallback(() => {
    setDeleteAccountOpen(false);
  }, []);

  const handlePasswordDialogClose = useCallback(() => {
    setDeletePasswordOpen(false);
    setDeletePassword('');
    setDeleteError('');
  }, []);

  const handleDeleteAccountSubmit = useCallback(async () => {
    try {
      setDeleteError('');
      logger.info('Delete Account', 'Attempting to delete account');
      await authAPI.deleteUser(deletePassword);
      logger.info('Delete Account', 'Account deleted successfully');
      logout();
      navigate('/login');
      handlePasswordDialogClose();
    } catch (error) {
      logger.error('Delete Account', error);
      const errorMessage = getErrorMessage(error, 'Failed to delete account');
      setDeleteError(errorMessage);
    }
  }, [deletePassword, logout, navigate, handlePasswordDialogClose]);

  const handleHomeClick = useCallback(() => {
    navigate('/home');
  }, [navigate]);

  const isExplorerRoute = location.pathname.startsWith('/explorer') || location.pathname.startsWith('/shared');

  const navButtonStyle = (active) => ({
    my: 1,
    mx: 0.25,
    px: 1.5,
    py: 0.8,
    color: active ? 'primary.main' : 'text.secondary',
    backgroundColor: active ? 'action.selected' : 'transparent',
    border: active ? '1px solid' : '1px solid transparent',
    borderColor: active ? 'divider' : 'transparent',
    borderRadius: 1,
    display: 'flex',
    alignItems: 'center',
    fontWeight: 800,
    '&:hover': {
      backgroundColor: 'action.hover',
      color: 'primary.main',
    },
    '& .MuiButton-startIcon .MuiSvgIcon-root': {
      color: active ? 'primary.main' : 'text.secondary',
    },
  });

  return (
    <AppBar
      position="sticky"
      elevation={0}
      role="navigation"
      aria-label="Main navigation"
      sx={{
        backgroundColor: 'background.paper',
        color: 'text.primary',
        borderBottom: '1px solid',
        borderColor: 'divider',
      }}
    >
      <Toolbar
        sx={{
          justifyContent: 'space-between',
          minHeight: { xs: 64, md: 68 },
          px: { xs: 2, md: 3, lg: 4 },
          width: '100%',
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
          <Box
            sx={{
              width: 38,
              height: 38,
              display: 'grid',
              placeItems: 'center',
              borderRadius: 1,
              backgroundColor: 'background.default',
              border: '1px solid',
              borderColor: 'divider',
              cursor: 'pointer',
            }}
            onClick={handleHomeClick}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                handleHomeClick();
              }
            }}
          >
            <img
              src="/logo192.png"
              alt="ResShare Logo"
              style={{
                width: '28px',
                height: '28px',
              }}
            />
          </Box>
          <Typography
            variant="h6"
            sx={{
              color: 'text.primary',
              fontWeight: 800,
              letterSpacing: 0,
              cursor: 'pointer',
            }}
            onClick={handleHomeClick}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                handleHomeClick();
              }
            }}
          >
            ResShare
          </Typography>
        </Box>

        <Box sx={{ flexGrow: 1, display: { xs: 'none', md: 'flex' }, ml: 4 }}>
          <Button
            onClick={() => navigate('/home')}
            sx={navButtonStyle(location.pathname === '/home')}
            startIcon={<Home />}
            aria-label="Navigate to Home"
            aria-current={location.pathname === '/home' ? 'page' : undefined}
          >
            Drive
          </Button>
          <Button
            onClick={() => navigate('/explorer')}
            sx={navButtonStyle(isExplorerRoute)}
            startIcon={<Folder />}
            aria-label="Navigate to Explorer"
            aria-current={isExplorerRoute ? 'page' : undefined}
          >
            Explorer
          </Button>
        </Box>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Tooltip title="Go to Home">
            <IconButton 
              onClick={handleHomeClick}
              aria-label="Go to Home"
              sx={{ 
                display: { xs: 'inline-flex', md: 'none' },
                color: location.pathname === '/home' ? 'primary.main' : 'text.secondary',
                '&:hover': { backgroundColor: 'action.hover' },
              }}
            >
              <Home fontSize="medium" />
            </IconButton>
          </Tooltip>

          <Tooltip title={darkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'}>
            <IconButton 
              onClick={toggleTheme}
              aria-label={darkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
              sx={{ 
                color: 'text.secondary',
                '&:hover': { backgroundColor: 'action.hover', color: 'primary.main' },
              }}
            >
              {darkMode ? <Brightness7 fontSize="medium" /> : <Brightness4 fontSize="medium" />}
            </IconButton>
          </Tooltip>

          <Tooltip title="Account settings">
            <IconButton
              onClick={handleMenuOpen}
              aria-label="Account settings"
              sx={{ 
                ml: 1,
                color: 'text.secondary',
                '&:hover': { backgroundColor: 'action.hover' },
              }}
            >
              <Avatar 
                sx={{ 
                  width: 32, 
                  height: 32, 
                  bgcolor: 'primary.main',
                  fontSize: '0.875rem',
                  color: 'background.paper',
                  fontWeight: 800,
                }}
              >
                {user?.charAt(0).toUpperCase()}
              </Avatar>
            </IconButton>
          </Tooltip>

          <Menu
            anchorEl={anchorEl}
            open={Boolean(anchorEl)}
            onClose={handleMenuClose}
            onClick={handleMenuClose}
            PaperProps={{
              elevation: 3,
              sx: {
                overflow: 'visible',
                filter: 'drop-shadow(0px 2px 8px rgba(0,0,0,0.32))',
                mt: 1.5,
                minWidth: 200,
                '& .MuiAvatar-root': {
                  width: 32,
                  height: 32,
                  ml: -0.5,
                  mr: 1,
                },
                '&:before': {
                  content: '""',
                  display: 'block',
                  position: 'absolute',
                  top: 0,
                  right: 14,
                  width: 10,
                  height: 10,
                  bgcolor: 'background.paper',
                  transform: 'translateY(-50%) rotate(45deg)',
                  zIndex: 0,
                },
              },
            }}
            transformOrigin={{ horizontal: 'right', vertical: 'top' }}
            anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
          >
            <MenuItem disabled>
              <Avatar sx={{ bgcolor: 'primary.main', color: theme.palette.primary.contrastText }}>
                {user?.charAt(0).toUpperCase()}
              </Avatar>
              <Box>
                <Typography variant="subtitle2">{user}</Typography>
                <Typography variant="caption" color="text.secondary">
                  Signed in
                </Typography>
              </Box>
            </MenuItem>
            
            <MenuItem
              onClick={handleLogout}
              sx={{ color: theme.palette.text.primary }}
              aria-label="Logout from account"
            >
              <Logout fontSize="medium" sx={{ mr: 2, color: theme.palette.action.active }} />
              Logout
            </MenuItem>

            <MenuItem
              onClick={handleDeleteAccountClick}
              sx={{ color: theme.palette.error.main }}
              aria-label="Delete account permanently"
            >
              <Delete fontSize="medium" sx={{ mr: 2, color: theme.palette.error.main }} />
              Delete Account
            </MenuItem>
          </Menu>
        </Box>
      </Toolbar>

      {/* Delete Account Confirmation Dialog */}
      <ConfirmDialog
        open={deleteAccountOpen}
        onClose={handleDeleteAccountCancel}
        onConfirm={handleDeleteAccountConfirm}
        title="Delete Account"
        message="Are you sure you want to delete your account? This action is permanent and cannot be undone. All your files and data will be permanently deleted."
        confirmText="Continue"
        cancelText="Cancel"
        isDestructive={true}
      />

      {/* Password Confirmation Dialog */}
      <Dialog
        open={deletePasswordOpen}
        onClose={handlePasswordDialogClose}
        aria-labelledby="delete-password-dialog-title"
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle id="delete-password-dialog-title">
          Confirm Account Deletion
        </DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Enter your password to confirm"
            type="password"
            fullWidth
            variant="outlined"
            value={deletePassword}
            onChange={(e) => setDeletePassword(e.target.value)}
            error={!!deleteError}
            helperText={deleteError || 'Please enter your password to permanently delete your account'}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && deletePassword.trim()) {
                e.preventDefault();
                handleDeleteAccountSubmit();
              }
            }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handlePasswordDialogClose} color="primary">
            Cancel
          </Button>
          <Button
            onClick={handleDeleteAccountSubmit}
            color="error"
            variant="contained"
            disabled={!deletePassword.trim()}
          >
            Delete Account
          </Button>
        </DialogActions>
      </Dialog>
    </AppBar>
  );
};

Navbar.propTypes = {};

export default Navbar; 
