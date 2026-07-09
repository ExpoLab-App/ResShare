import React, { useState, useCallback } from 'react';
import {
  Container,
  Paper,
  TextField,
  Button,
  Typography,
  Box,
  Alert,
  Link,
  IconButton,
  InputAdornment,
  Fade,
  CircularProgress,
} from '@mui/material';
import {
  Visibility,
  VisibilityOff,
  Login as LoginIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useAuth, useThemeMode } from '../App';
import { authAPI } from '../utils/api';
import { logger } from '../utils/logger';
import { getErrorMessage, getBackendErrorMessage } from '../utils/errorHandler';
import { sanitizeUsername } from '../utils/sanitization';

const LoginPage = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  const { darkMode } = useThemeMode();
  
  const [formData, setFormData] = useState({
    username: '',
    password: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
    if (error) setError('');
  };

  const handleSubmit = useCallback(async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      // Sanitize username input
      const sanitizedUsername = sanitizeUsername(formData.username);

      // Check if username is empty after sanitization
      if (!sanitizedUsername) {
        setError('Username contains invalid characters');
        setLoading(false);
        return;
      }

      // Trim password to prevent whitespace-only passwords
      const trimmedPassword = formData.password.trim();
      if (!trimmedPassword) {
        setError('Password cannot be empty or contain only whitespace');
        setLoading(false);
        return;
      }

      logger.debug('Attempting login', { username: sanitizedUsername });
      const data = await authAPI.login(sanitizedUsername, trimmedPassword);

      if (data.result === 'SUCCESS') {
        logger.debug('Login successful', { username: sanitizedUsername });
        login(sanitizedUsername, data.root, data.share_list);
        navigate('/home');
      } else {
        logger.error('Login failed', { result: data.result });
        // Use getBackendErrorMessage to convert error code to user-friendly message
        setError(getBackendErrorMessage(data.result) || 'Login failed');
      }
    } catch (error) {
      logger.error('Login error', { error: error.message });
      setError(getErrorMessage(error, 'Failed to login'));
    } finally {
      setLoading(false);
    }
  }, [formData.username, formData.password, login, navigate]);

  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };

  return (
    <Container component="main" maxWidth="sm">
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
          py: 4,
        }}
      >
        <Fade in timeout={800}>
          <Paper
            elevation={6}
            sx={{
              padding: { xs: 3, sm: 4 },
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              width: '100%',
              maxWidth: 420,
              borderRadius: 2,
              border: '1px solid',
              borderColor: 'divider',
              backgroundColor: 'background.paper',
              boxShadow: darkMode
                ? '0 24px 60px rgba(0, 0, 0, 0.32)'
                : '0 24px 60px rgba(21, 37, 52, 0.08)',
            }}
          >
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                mb: 3,
                gap: 2,
              }}
            >
              <img 
                src="/logo192.png"
                alt="ResShare Logo"
                style={{
                  width: '48px',
                  height: '48px',
                  filter: 'drop-shadow(0 8px 14px rgba(36, 111, 167, 0.18))',
                }}
              />
              <Typography 
                component="h1" 
                variant="h4" 
                sx={{ 
                  fontWeight: 700,
                  color: 'text.primary',
                }}
              >
                ResShare
              </Typography>
            </Box>

            <Typography 
              variant="h6" 
              sx={{ 
                mb: 3, 
                color: 'text.secondary',
                textAlign: 'center',
              }}
            >
              Sign in to your account
            </Typography>

            {error && (
              <Alert 
                severity="error" 
                sx={{ 
                  width: '100%', 
                  mb: 2,
                  borderRadius: 2,
                }}
              >
                {error}
              </Alert>
            )}

            <Box component="form" onSubmit={handleSubmit} sx={{ width: '100%' }}>
              <TextField
                margin="normal"
                required
                fullWidth
                id="username"
                label="Username"
                name="username"
                autoComplete="username"
                autoFocus
                value={formData.username}
                onChange={handleChange}
                disabled={loading}
                sx={{
                  mb: 2,
                  '& .MuiOutlinedInput-root': {
                    borderRadius: 1,
                  },
                }}
              />
              
              <TextField
                margin="normal"
                required
                fullWidth
                name="password"
                label="Password"
                type={showPassword ? 'text' : 'password'}
                id="password"
                autoComplete="current-password"
                value={formData.password}
                onChange={handleChange}
                disabled={loading}
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        aria-label="toggle password visibility"
                        onClick={togglePasswordVisibility}
                        edge="end"
                        disabled={loading}
                      >
                        {showPassword ? <VisibilityOff /> : <Visibility />}
                      </IconButton>
                    </InputAdornment>
                  ),
                }}
                sx={{
                  mb: 3,
                  '& .MuiOutlinedInput-root': {
                    borderRadius: 1,
                  },
                }}
              />

              <Button
                type="submit"
                fullWidth
                variant="contained"
                disabled={loading}
                startIcon={loading ? <CircularProgress size={20} /> : <LoginIcon />}
                sx={{
                  mt: 1,
                  mb: 2,
                  py: 1.5,
                  borderRadius: 1,
                  fontSize: '1rem',
                  fontWeight: 800,
                  backgroundColor: 'primary.main',
                  boxShadow: 'none',
                  '&:hover': {
                    backgroundColor: 'primary.dark',
                    boxShadow: 'none',
                  },
                  '&:disabled': {
                    backgroundColor: 'action.disabledBackground',
                  },
                }}
              >
                {loading ? 'Signing In...' : 'Sign In'}
              </Button>

              <Box sx={{ textAlign: 'center', mt: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  Don't have an account?{' '}
                  <Link
                    component="button"
                    variant="body2"
                    onClick={() => navigate('/register')}
                    sx={{
                      textDecoration: 'none',
                      fontWeight: 600,
                      color: 'primary.main',
                      '&:hover': {
                        textDecoration: 'underline',
                      },
                    }}
                  >
                    Sign up here
                  </Link>
                </Typography>
              </Box>
            </Box>
          </Paper>
        </Fade>

        <Box sx={{ mt: 4, textAlign: 'center' }}>
          <Typography variant="caption" color="text.secondary">
            Secure file sharing
          </Typography>
        </Box>
      </Box>
    </Container>
  );
};

LoginPage.propTypes = {};

export default LoginPage; 
