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
              padding: 4,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              width: '100%',
              maxWidth: 400,
              borderRadius: 3,
              background: darkMode 
                ? 'linear-gradient(145deg, #1e1e1e 0%, #2d2d2d 100%)'
                : 'linear-gradient(145deg, #ffffff 0%, #f5f5f5 100%)',
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
                  filter: 'drop-shadow(0 2px 4px rgba(25,118,210,0.3))',
                }}
              />
              <Typography 
                component="h1" 
                variant="h4" 
                sx={{ 
                  fontWeight: 700,
                  background: darkMode
                    ? 'linear-gradient(45deg, #42a5f5 30%, #1976d2 90%)'
                    : 'linear-gradient(45deg, #1976d2 30%, #42a5f5 90%)',
                  backgroundClip: 'text',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
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
                    borderRadius: 2,
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
                    borderRadius: 2,
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
                  borderRadius: 2,
                  fontSize: '1rem',
                  fontWeight: 600,
                  background: 'linear-gradient(45deg, #1976d2 30%, #42a5f5 90%)',
                  boxShadow: '0 3px 5px 2px rgba(25, 118, 210, .3)',
                  '&:hover': {
                    background: 'linear-gradient(45deg, #1565c0 30%, #1976d2 90%)',
                    boxShadow: '0 4px 8px 3px rgba(25, 118, 210, .3)',
                  },
                  '&:disabled': {
                    background: 'rgba(25, 118, 210, 0.3)',
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
            Secure file sharing made simple
          </Typography>
        </Box>
      </Box>
    </Container>
  );
};

LoginPage.propTypes = {};

export default LoginPage; 