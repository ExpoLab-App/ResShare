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
  CloudQueue,
  Visibility,
  VisibilityOff,
  PersonAdd,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useThemeMode } from '../App';
import { authAPI } from '../utils/api';
import { logger } from '../utils/logger';
import { getErrorMessage, getBackendErrorMessage } from '../utils/errorHandler';
import { sanitizeUsername } from '../utils/sanitization';
const RegisterPage = () => {
  const navigate = useNavigate();
  const { darkMode } = useThemeMode();
  
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    confirmPassword: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
    if (error) setError('');
    if (success) setSuccess('');
  };

  const validateForm = useCallback(() => {
    // Sanitize username input
    const sanitizedUsername = sanitizeUsername(formData.username);

    // Check if username is empty after sanitization
    if (!sanitizedUsername) {
      setError('Username contains invalid characters');
      return false;
    }

    if (sanitizedUsername.length < 3) {
      setError('Username must be at least 3 characters long');
      return false;
    }

    // Trim password to prevent whitespace-only passwords
    const trimmedPassword = formData.password.trim();
    if (!trimmedPassword) {
      setError('Password cannot be empty or contain only whitespace');
      return false;
    }

    if (trimmedPassword.length < 6) {
      setError('Password must be at least 6 characters long');
      return false;
    }

    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      return false;
    }

    return true;
  }, [formData.username, formData.password, formData.confirmPassword]);

  const handleSubmit = useCallback(async (e) => {
    e.preventDefault();

    if (!validateForm()) return;

    setLoading(true);
    setError('');

    try {
      // Sanitize username and trim password
      const sanitizedUsername = sanitizeUsername(formData.username);
      const trimmedPassword = formData.password.trim();

      logger.debug('Attempting signup', { username: sanitizedUsername });
      const signupData = await authAPI.signup(sanitizedUsername, trimmedPassword);
      logger.debug('Signup data', signupData);

      if (signupData.result === 'SUCCESS') {
        logger.debug('Signup successful, attempting auto-login', { username: sanitizedUsername });
        const loginData = await authAPI.login(sanitizedUsername, trimmedPassword);

        if (loginData.result === 'SUCCESS') {
          logger.debug('Auto-login successful', { username: sanitizedUsername });
          setSuccess('Account created and logged in successfully! Redirecting...');
          setTimeout(() => {
            navigate('/home');
          }, 1500);
        } else {
          logger.error('Auto-login failed after signup', { result: loginData.result });
          setSuccess('Account created successfully! Please log in.');
          setTimeout(() => {
            navigate('/login');
          }, 1500);
        }
      } else {
        logger.error('Signup failed', { result: signupData.result });

        // Special handling for USER_EXISTS error
        if (signupData.result === 'USER_EXISTS') {
          setError('This username is already taken. If it\'s your username, please login. Otherwise, choose a different username.');
        } else {
          // Use getBackendErrorMessage to convert error code to user-friendly message
          setError(getBackendErrorMessage(signupData.result) || 'Registration failed');
        }
      }
    } catch (error) {
      logger.error('Signup error', { error: error.message });
      setError(getErrorMessage(error, 'Failed to signup'));
    } finally {
      setLoading(false);
    }
  }, [formData.username, formData.password, validateForm, navigate]);

  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };

  const toggleConfirmPasswordVisibility = () => {
    setShowConfirmPassword(!showConfirmPassword);
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
              <CloudQueue 
                sx={{ 
                  fontSize: 48, 
                  color: 'primary.main',
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
              Create your account
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

            {success && (
              <Alert 
                severity="success" 
                sx={{ 
                  width: '100%', 
                  mb: 2,
                  borderRadius: 2,
                }}
              >
                {success}
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
                helperText="At least 3 characters"
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
                autoComplete="new-password"
                value={formData.password}
                onChange={handleChange}
                disabled={loading}
                helperText="At least 6 characters"
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
                name="confirmPassword"
                label="Confirm Password"
                type={showConfirmPassword ? 'text' : 'password'}
                id="confirmPassword"
                autoComplete="new-password"
                value={formData.confirmPassword}
                onChange={handleChange}
                disabled={loading}
                helperText="Must match password"
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        aria-label="toggle confirm password visibility"
                        onClick={toggleConfirmPasswordVisibility}
                        edge="end"
                        disabled={loading}
                      >
                        {showConfirmPassword ? <VisibilityOff /> : <Visibility />}
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
                startIcon={loading ? <CircularProgress size={20} /> : <PersonAdd />}
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
                {loading ? 'Creating Account...' : 'Create Account'}
              </Button>

              <Box sx={{ textAlign: 'center', mt: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  Already have an account?{' '}
                  <Link
                    component="button"
                    variant="body2"
                    onClick={() => navigate('/login')}
                    sx={{
                      textDecoration: 'none',
                      fontWeight: 600,
                      color: 'primary.main',
                      '&:hover': {
                        textDecoration: 'underline',
                      },
                    }}
                  >
                    Sign in here
                  </Link>
                </Typography>
              </Box>
            </Box>
          </Paper>
        </Fade>

        <Box sx={{ mt: 4, textAlign: 'center' }}>
          <Typography variant="caption" color="text.secondary">
            Join thousands of users sharing files securely
          </Typography>
        </Box>
      </Box>
    </Container>
  );
};

RegisterPage.propTypes = {};

export default RegisterPage; 