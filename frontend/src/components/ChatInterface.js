import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import PropTypes from 'prop-types';
import {
  Container,
  Paper,
  Typography,
  Box,
  TextField,
  IconButton,
  Card,
  CardContent,
  Chip,
  Alert,
  Divider,
  CircularProgress,
  Tooltip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Collapse,
} from '@mui/material';
import {
  Send,
  Person,
  Description,
  ExpandMore,
  ExpandLess,
  Info,
} from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';
import { chatAPI } from '../utils/api';
import { useAuth } from '../App';
import { logger } from '../utils/logger';
import { getErrorMessage } from '../utils/errorHandler';
import { escapeHtml } from '../utils/sanitization';
import AIAssistantIcon from './AIAssistantIcon';

const MessageBubble = React.memo(({ message, theme }) => {
  const isUser = message.type === 'user';
  const [showSources, setShowSources] = useState(false);

  const userBg = theme.palette.primary.main;
  const userText = theme.palette.primary.contrastText;
  const botBg = theme.palette.mode === 'dark' ? 'rgba(255,255,255,0.045)' : theme.palette.background.paper;
  const botText = theme.palette.text.primary;
  const errorBg = theme.palette.error.light;
  const errorText = theme.palette.error.contrastText || theme.palette.text.primary;

  let backgroundColor, color;
  if (isUser) {
    backgroundColor = userBg;
    color = userText;
  } else if (message.isError) {
    backgroundColor = errorBg;
    color = errorText;
  } else {
    backgroundColor = botBg;
    color = botText;
  }

  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: isUser ? 'flex-end' : 'flex-start',
        mb: 2,
      }}
    >
      <Card
        sx={{
          maxWidth: { xs: '88%', md: '72%' },
          borderRadius: 2,
          backgroundColor,
          color,
          boxShadow: 'none',
          border: isUser
            ? '1px solid transparent'
            : `1px solid ${theme.palette.divider}`,
        }}
      >
        <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
            {isUser ? <Person sx={{ mr: 1 }} /> : <AIAssistantIcon size={24} sx={{ mr: 1 }} />}
            <Typography variant="body2" sx={{ fontWeight: 800 }}>
              {isUser ? 'You' : 'AI Assistant'}
            </Typography>
          </Box>

          <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap', mb: 1 }}>
            {message.content}
          </Typography>

          {message.sources && message.sources.length > 0 && (
            <Box>
              <Divider sx={{ my: 1 }} />
              <Box sx={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}
                   onClick={() => setShowSources(!showSources)}>
                <Typography variant="caption" sx={{ mr: 1 }}>
                  Sources ({message.sources.length})
                </Typography>
                {showSources ? <ExpandLess size="small" /> : <ExpandMore size="small" />}
              </Box>

              <Collapse in={showSources}>
                <Box sx={{ mt: 1 }}>
                  {message.sources.map((source, index) => (
                    <Chip
                      key={index}
                      icon={<Description />}
                      label={`${source.filename} (${(source.score * 100).toFixed(1)}%)`}
                      size="small"
                      variant="outlined"
                      sx={{ mr: 0.5, mb: 0.5 }}
                    />
                  ))}
                </Box>
              </Collapse>
            </Box>
          )}

          {message.chunksFound > 0 && (
            <Box sx={{ mt: 1 }}>
              <Chip
                icon={<Info />}
                label={`${message.chunksFound} relevant sections found`}
                size="small"
                color="info"
                variant="outlined"
              />
            </Box>
          )}

          <Typography variant="caption" sx={{ mt: 1, display: 'block', opacity: 0.7 }}>
            {message.timestamp.toLocaleTimeString()}
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
});

MessageBubble.propTypes = {
  message: PropTypes.shape({
    id: PropTypes.number.isRequired,
    type: PropTypes.string.isRequired,
    content: PropTypes.string.isRequired,
    timestamp: PropTypes.instanceOf(Date).isRequired,
    sources: PropTypes.array,
    chunksFound: PropTypes.number,
    isError: PropTypes.bool
  }).isRequired,
  theme: PropTypes.object.isRequired
};

const ChatInterface = ({ embedded = false }) => {
  const { user } = useAuth();
  const theme = useTheme();
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [stats, setStats] = useState(null);
  const [showStats, setShowStats] = useState(false);
  const [error, setError] = useState('');
  const messagesEndRef = useRef(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  const loadStats = useCallback(async () => {
    try {
      const statsData = await chatAPI.getStats();
      setStats(statsData);
    } catch (error) {
      logger.error('Failed to load chat stats:', error);
    }
  }, []);

  const welcomeMessage = useMemo(() => ({
    id: 1,
    type: 'bot',
    content: `Hello ${escapeHtml(user)}! I'm your AI assistant. I can help you find information from your uploaded documents. Ask me anything about the files you've shared!`,
    timestamp: new Date(),
  }), [user]);

  useEffect(() => {
    loadStats();

    setMessages([welcomeMessage]);
  }, [loadStats, welcomeMessage]);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  const handleSendMessage = useCallback(async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputMessage.trim(),
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);
    setError('');

    try {
      const response = await chatAPI.sendMessage(userMessage.content);

      const botMessage = {
        id: Date.now() + 1,
        type: 'bot',
        content: response.answer,
        sources: response.sources || [],
        chunksFound: response.chunks_found || 0,
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      logger.error('Chat error:', error);
      const errorMsg = getErrorMessage(error, 'Failed to send message');
      const errorMessage = {
        id: Date.now() + 1,
        type: 'bot',
        content: 'Sorry, I encountered an error while processing your question. Please try again.',
        isError: true,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
      setError(errorMsg);
    } finally {
      setIsLoading(false);
    }
  }, [inputMessage, isLoading]);

  const handleKeyPress = useCallback((event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSendMessage();
    }
  }, [handleSendMessage]);

  const statsDisplay = useMemo(() => {
    if (!stats) {
      return (
        <Typography variant="body2" color="text.secondary">
          No documents have been processed yet. Upload some PDF, DOCX, or TXT files to get started!
        </Typography>
      );
    }

    return (
      <Box>
        <Typography variant="body2" color="text.secondary">
          Your AI assistant has indexed {stats.total_chunks} text sections from {stats.total_files} files.
        </Typography>

        {stats.files && stats.files.length > 0 && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="subtitle2" sx={{ mb: 1 }}>
              Indexed Files:
            </Typography>
            <List dense>
              {stats.files.map((filename, index) => (
                <ListItem key={index} sx={{ py: 0 }}>
                  <ListItemIcon sx={{ minWidth: 32 }}>
                    <Description fontSize="small" />
                  </ListItemIcon>
                  <ListItemText primary={filename} />
                </ListItem>
              ))}
            </List>
          </Box>
        )}
      </Box>
    );
  }, [stats]);

  const StatsPanel = () => (
    <Card
      sx={{
        mb: 2,
        boxShadow: 'none',
        borderRadius: 2,
        backgroundColor: 'background.default',
      }}
    >
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}
             onClick={() => setShowStats(!showStats)}>
          <AIAssistantIcon size={26} sx={{ mr: 1 }} />
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            Knowledge Base
          </Typography>
          {showStats ? <ExpandLess /> : <ExpandMore />}
        </Box>

        <Collapse in={showStats}>
          <Box sx={{ mt: 2 }}>
            {statsDisplay}
          </Box>
        </Collapse>
      </CardContent>
    </Card>
  );

  const chatPanel = (
    <Paper
      sx={{
        height: embedded ? '100%' : { xs: 'calc(100vh - 112px)', md: 'calc(100vh - 128px)' },
        minHeight: embedded ? 0 : 560,
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        borderRadius: embedded ? 0 : 2,
        border: embedded ? 0 : undefined,
        boxShadow: embedded ? 'none' : undefined,
        backgroundColor: 'background.paper',
      }}
    >
      {/* Header */}
      <Box sx={{ p: embedded ? 2 : { xs: 2, md: 2.5 }, borderBottom: 1, borderColor: 'divider' }}>
        <Typography variant={embedded ? 'h6' : 'h5'} sx={{ display: 'flex', alignItems: 'center' }}>
          <AIAssistantIcon size={30} sx={{ mr: 1 }} />
          AI Document Assistant
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Ask questions about your uploaded documents
        </Typography>
      </Box>

      {/* Stats Panel */}
      <Box sx={{ p: embedded ? 2 : { xs: 2, md: 2.5 }, pb: 0 }}>
        <StatsPanel />
      </Box>

      {/* Messages */}
      <Box sx={{ flexGrow: 1, overflow: 'auto', p: embedded ? 2 : { xs: 2, md: 2.5 } }}>
        {messages.map(message => (
          <MessageBubble key={message.id} message={message} theme={theme} />
        ))}

        {isLoading && (
          <Box sx={{ display: 'flex', justifyContent: 'flex-start', mb: 2 }}>
            <Card
              sx={{
                backgroundColor: theme.palette.mode === 'dark' ? 'rgba(255,255,255,0.06)' : theme.palette.background.paper,
                boxShadow: 'none',
                border: `1px solid ${theme.palette.divider}`,
              }}
            >
              <CardContent sx={{ p: 2, display: 'flex', alignItems: 'center' }}>
                <CircularProgress size={20} sx={{ mr: 2 }} />
                <Typography variant="body2">AI is thinking...</Typography>
              </CardContent>
            </Card>
          </Box>
        )}
        
        <div ref={messagesEndRef} />
      </Box>

      {/* Error Display */}
      {error && (
        <Box sx={{ p: 2 }}>
          <Alert severity="error" onClose={() => setError('')}>
            {error}
          </Alert>
        </Box>
      )}

      {/* Input */}
      <Box sx={{ p: embedded ? 2 : { xs: 2, md: 2.5 }, borderTop: 1, borderColor: 'divider' }}>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <TextField
            fullWidth
            multiline
            maxRows={3}
            placeholder="Ask a question about your documents..."
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={isLoading}
            variant="outlined"
            size="small"
            sx={{
              '& .MuiOutlinedInput-root': {
                alignItems: 'flex-end',
              },
            }}
          />
          <Tooltip title="Send message">
            <IconButton
              onClick={handleSendMessage}
              disabled={!inputMessage.trim() || isLoading}
              color="primary"
              sx={{
                alignSelf: 'flex-end',
                width: 42,
                height: 42,
                borderRadius: 1,
                bgcolor: 'primary.main',
                color: 'background.paper',
                '&:hover': { bgcolor: 'primary.dark' },
                '&.Mui-disabled': {
                  bgcolor: 'action.disabledBackground',
                },
              }}
            >
              <Send />
            </IconButton>
          </Tooltip>
        </Box>
        
      </Box>
    </Paper>
  );

  if (embedded) {
    return (
      <Box sx={{ height: '100%', minHeight: 0 }}>
        {chatPanel}
      </Box>
    );
  }

  return (
    <Container
      maxWidth={false}
      sx={{
        py: { xs: 2, md: 3 },
        px: { xs: 2, md: 3 },
        maxWidth: 1120,
        mx: 'auto',
      }}
    >
      {chatPanel}
    </Container>
  );
};

ChatInterface.propTypes = {
  embedded: PropTypes.bool,
};

export default ChatInterface; 
