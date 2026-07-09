import React, { useState, createContext, useContext, useEffect, useCallback } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline, Box, CircularProgress } from '@mui/material';
import LoginPage from './components/LoginPage';
import RegisterPage from './components/RegisterPage';
import HomePage from './components/HomePage';
import FileExplorer from './components/FileExplorer';
import ChatInterface from './components/ChatInterface';
import Navbar from './components/Navbar';
import ErrorBoundary from './components/ErrorBoundary';
import AIChatSidebar from './components/AIChatSidebar';
import { authAPI } from './utils/api';

// Auth Context
const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

const ThemeContext = createContext();

export const useThemeMode = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useThemeMode must be used within a ThemeProvider');
  }
  return context;
};

function App() {
  const [darkMode, setDarkMode] = useState(() => {
    const saved = localStorage.getItem('darkMode');
    return saved !== null ? JSON.parse(saved) : false;
  });
  const [user, setUser] = useState(null);
  const [rootData, setRootData] = useState(null);
  const [shareList, setShareList] = useState({});
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);

  useEffect(() => {
    const checkSession = async () => {
      try {
        const data = await authAPI.checkAuthStatus();
        if (data.authenticated && data.username) {
          setUser(data.username);
          setRootData(data.root);
          setShareList(data.share_list || {});
        }
      } catch (error) {
        console.error('Error checking auth status:', error);
      } finally {
        setIsCheckingAuth(false);
      }
    };

    checkSession();
  }, []);

  const theme = createTheme({
    palette: {
      mode: darkMode ? 'dark' : 'light',
      primary: {
        main: darkMode ? '#8ecdf7' : '#246fa7',
        light: darkMode ? '#c4e8ff' : '#5e9dca',
        dark: darkMode ? '#5aa9de' : '#17547f',
      },
      secondary: {
        main: darkMode ? '#e8ba75' : '#a87532',
        light: darkMode ? '#f3d7aa' : '#cb9651',
        dark: darkMode ? '#b78845' : '#744f20',
      },
      success: {
        main: darkMode ? '#7fc297' : '#2f7a55',
      },
      warning: {
        main: darkMode ? '#e9bf6b' : '#b47c24',
      },
      error: {
        main: darkMode ? '#ef8f83' : '#b94d43',
      },
      info: {
        main: darkMode ? '#4f91c7' : '#2a6f9e',
      },
      background: {
        default: darkMode ? '#111417' : '#f5f7fa',
        paper: darkMode ? '#191d21' : '#ffffff',
      },
      text: {
        primary: darkMode ? '#eff3f7' : '#17202a',
        secondary: darkMode ? '#aab7c3' : '#667585',
      },
      divider: darkMode ? 'rgba(210, 222, 232, 0.13)' : 'rgba(27, 43, 60, 0.11)',
      action: {
        hover: darkMode ? 'rgba(142, 205, 247, 0.08)' : 'rgba(36, 111, 167, 0.06)',
        selected: darkMode ? 'rgba(142, 205, 247, 0.13)' : 'rgba(36, 111, 167, 0.09)',
      },
    },
    typography: {
      fontFamily: '"Aptos", "Segoe UI", "Helvetica Neue", sans-serif',
      h1: {
        fontWeight: 800,
        letterSpacing: 0,
      },
      h2: {
        fontWeight: 800,
        letterSpacing: 0,
      },
      h3: {
        fontWeight: 800,
        letterSpacing: 0,
      },
      h4: {
        fontWeight: 800,
        letterSpacing: 0,
      },
      h5: {
        fontWeight: 800,
        letterSpacing: 0,
      },
      h6: {
        fontWeight: 800,
        letterSpacing: 0,
      },
      button: {
        fontWeight: 700,
        letterSpacing: 0,
      },
    },
    shape: {
      borderRadius: 8,
    },
    components: {
      MuiButton: {
        styleOverrides: {
          root: {
            textTransform: 'none',
            borderRadius: 8,
            boxShadow: 'none',
            paddingInline: 18,
            minHeight: 40,
            '&:hover': {
              boxShadow: 'none',
            },
          },
          containedPrimary: {
            background: darkMode ? '#8ecdf7' : '#246fa7',
            color: darkMode ? '#111417' : '#ffffff',
            '&:hover': {
              background: darkMode ? '#c4e8ff' : '#17547f',
            },
          },
          outlinedPrimary: {
            borderColor: darkMode ? 'rgba(142, 205, 247, 0.32)' : 'rgba(36, 111, 167, 0.24)',
            color: darkMode ? '#d7ecff' : '#246fa7',
            '&:hover': {
              borderColor: darkMode ? '#8ecdf7' : '#246fa7',
              background: darkMode ? 'rgba(142, 205, 247, 0.08)' : 'rgba(36, 111, 167, 0.06)',
            },
          },
        },
      },
      MuiPaper: {
        styleOverrides: {
          root: {
            backgroundImage: 'none',
            border: darkMode ? '1px solid rgba(210, 222, 232, 0.12)' : '1px solid rgba(27, 43, 60, 0.09)',
            boxShadow: darkMode
              ? '0 18px 42px rgba(0, 0, 0, 0.26)'
              : '0 16px 36px rgba(21, 37, 52, 0.06)',
          },
        },
      },
      MuiCard: {
        styleOverrides: {
          root: {
            borderRadius: 8,
            border: darkMode ? '1px solid rgba(210, 222, 232, 0.12)' : '1px solid rgba(27, 43, 60, 0.09)',
            boxShadow: darkMode
              ? '0 12px 30px rgba(0, 0, 0, 0.22)'
              : '0 12px 28px rgba(21, 37, 52, 0.055)',
          },
        },
      },
      MuiOutlinedInput: {
        styleOverrides: {
          root: {
            borderRadius: 8,
            backgroundColor: darkMode ? 'rgba(255, 255, 255, 0.035)' : '#ffffff',
          },
        },
      },
      MuiChip: {
        styleOverrides: {
          root: {
            borderRadius: 6,
            fontWeight: 700,
          },
        },
      },
      MuiAppBar: {
        styleOverrides: {
          root: {
            boxShadow: 'none',
          },
        },
      },
      MuiDialog: {
        styleOverrides: {
          paper: {
            borderRadius: 8,
          },
        },
      },
    },
  });

  const toggleTheme = () => {
    setDarkMode((prev) => {
      const newValue = !prev;
      localStorage.setItem('darkMode', JSON.stringify(newValue));
      return newValue;
    });
  };

  const login = (username, root, shares) => {
    setUser(username);
    setRootData(root);
    setShareList(shares || {});
  };

  const logout = () => {
    setUser(null);
    setRootData(null);
    setShareList({});
  };

  const refreshShareList = useCallback(async () => {
    try {
      const data = await authAPI.fetchSharedItems();
      if (data && data.share_list !== undefined) {
        setShareList(data.share_list || {});
      }
    } catch (error) {
      console.error('Error refreshing shared items:', error);
    }
  }, []);

  const authValue = {
    user,
    rootData,
    shareList,
    login,
    logout,
    setRootData,
    setShareList,
    refreshShareList,
  };

  const themeValue = {
    darkMode,
    toggleTheme,
  };

  if (isCheckingAuth) {
    return (
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            minHeight: '100vh',
            backgroundColor: 'background.default'
          }}
        >
          <CircularProgress />
        </Box>
      </ThemeProvider>
    );
  }

  const appRoutes = (
    <Routes>
      <Route 
        path="/login" 
        element={!user ? <LoginPage /> : <Navigate to="/home" />} 
      />
      <Route 
        path="/register" 
        element={!user ? <RegisterPage /> : <Navigate to="/home" />} 
      />
      <Route 
        path="/home" 
        element={user ? <HomePage /> : <Navigate to="/login" />} 
      />
      <Route 
        path="/explorer/*" 
        element={user ? <FileExplorer /> : <Navigate to="/login" />} 
      />
      <Route
        path="/shared"
        element={<Navigate to={user ? "/home" : "/login"} replace />}
      />
      <Route
        path="/shared/*"
        element={user ? <FileExplorer /> : <Navigate to="/login" />}
      />
      <Route 
        path="/chat" 
        element={user ? <ChatInterface /> : <Navigate to="/login" />} 
      />
      <Route 
        path="/" 
        element={<Navigate to={user ? "/home" : "/login"} />} 
      />
    </Routes>
  );

  return (
    <ErrorBoundary>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <AuthContext.Provider value={authValue}>
          <ThemeContext.Provider value={themeValue}>
            <Box
              className="res-share-app"
              sx={{
                minHeight: '100vh',
                backgroundColor: 'background.default',
                color: 'text.primary',
              }}
            >
              {user && <Navbar />}
              {user ? (
                <Box sx={{ display: 'flex', alignItems: 'stretch', minHeight: { xs: 'calc(100dvh - 64px)', md: 'calc(100vh - 68px)' } }}>
                  <AIChatSidebar />
                  <Box component="main" sx={{ flex: 1, minWidth: 0 }}>
                    {appRoutes}
                  </Box>
                </Box>
              ) : (
                appRoutes
              )}
          </Box>
        </ThemeContext.Provider>
      </AuthContext.Provider>
    </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;
