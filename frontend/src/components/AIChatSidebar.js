import React, { useState } from 'react';
import {
  Box,
  Button,
  Divider,
  IconButton,
  Tooltip,
  Typography,
} from '@mui/material';
import {
  AutoAwesomeRounded,
  ChatBubbleOutlineRounded,
  ChevronLeft,
  OpenInFull,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import ChatInterface from './ChatInterface';

const AIChatSidebar = () => {
  const [open, setOpen] = useState(false);
  const [hasOpened, setHasOpened] = useState(false);
  const navigate = useNavigate();
  const chatPanelId = 'ai-chat-sidebar-panel';

  const toggleChat = () => {
    if (!open) {
      setHasOpened(true);
    }
    setOpen((current) => !current);
  };

  return (
    <Box
      component="aside"
      aria-label="AI chat sidebar"
      sx={{
        width: open ? { xs: 'calc(100vw - 32px)', sm: 360, md: 390 } : 56,
        maxWidth: open ? 'calc(100vw - 32px)' : 56,
        flexShrink: 0,
        height: open
          ? { xs: 'calc(100dvh - 96px)', md: 'calc(100vh - 68px)' }
          : { xs: 56, md: 'calc(100vh - 68px)' },
        position: { xs: 'fixed', md: 'sticky' },
        top: { xs: 'auto', md: 68 },
        right: { xs: 2, md: 'auto' },
        bottom: { xs: 2, md: 'auto' },
        alignSelf: 'flex-start',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        border: { xs: '1px solid', md: 'none' },
        borderRight: '1px solid',
        borderColor: 'divider',
        borderRadius: { xs: '8px', md: 0 },
        backgroundColor: 'background.paper',
        boxShadow: { xs: open ? 8 : 3, md: 'none' },
        transition: 'width 180ms ease, height 180ms ease, box-shadow 180ms ease',
        zIndex: { xs: 1300, md: 2 },
      }}
    >
      <Box
        sx={{
          height: 56,
          display: 'flex',
          alignItems: 'center',
          justifyContent: open ? 'space-between' : 'center',
          gap: 1,
          px: open ? 1.5 : 1,
          flexShrink: 0,
        }}
      >
        <Tooltip title={open ? 'Collapse AI chat' : 'Open AI chat'} placement="right">
          <IconButton
            onClick={toggleChat}
            aria-label={open ? 'Collapse AI chat' : 'Open AI chat'}
            aria-expanded={open}
            aria-controls={hasOpened ? chatPanelId : undefined}
            sx={{
              width: 44,
              height: 44,
              borderRadius: 1,
              color: open ? 'text.secondary' : 'primary.main',
              backgroundColor: open ? 'transparent' : 'action.selected',
              border: '1px solid',
              borderColor: open ? 'transparent' : 'divider',
              '&:hover': {
                backgroundColor: 'action.hover',
                color: 'primary.main',
              },
              '&.Mui-focusVisible': {
                outline: '2px solid',
                outlineColor: 'secondary.main',
                outlineOffset: 2,
              },
            }}
          >
            {open ? (
              <ChevronLeft />
            ) : (
              <Box
                component="span"
                aria-hidden="true"
                sx={{
                  position: 'relative',
                  width: 26,
                  height: 26,
                  display: 'inline-flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <ChatBubbleOutlineRounded sx={{ fontSize: 25 }} />
                <AutoAwesomeRounded
                  sx={{
                    position: 'absolute',
                    top: -4,
                    right: -5,
                    fontSize: 14,
                    color: 'secondary.main',
                    backgroundColor: 'background.paper',
                    borderRadius: '50%',
                    p: '1px',
                  }}
                />
              </Box>
            )}
          </IconButton>
        </Tooltip>

        {open && (
          <>
            <Box sx={{ minWidth: 0, flex: 1 }}>
              <Typography variant="subtitle2" sx={{ fontWeight: 800, lineHeight: 1.1 }}>
                AI Chat
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Document assistant
              </Typography>
            </Box>
            <Button
              size="small"
              variant="text"
              startIcon={<OpenInFull />}
              onClick={() => navigate('/chat')}
              sx={{ flexShrink: 0 }}
            >
              Full
            </Button>
          </>
        )}
      </Box>

      <Divider />

      {hasOpened && (
        <Box
          id={chatPanelId}
          role="region"
          aria-label="AI chat panel"
          sx={{ flex: 1, minHeight: 0, display: open ? 'block' : 'none' }}
        >
          <ChatInterface embedded />
        </Box>
      )}

      {!open && <Box sx={{ flex: 1 }} />}
    </Box>
  );
};

export default AIChatSidebar;
