import React from 'react';
import PropTypes from 'prop-types';
import { AutoAwesomeRounded } from '@mui/icons-material';

const AIAssistantIcon = ({ size = 24, sx = {}, alt = '' }) => (
  <AutoAwesomeRounded
    titleAccess={alt || undefined}
    aria-hidden={alt ? undefined : true}
    sx={{
      fontSize: size,
      display: 'inline-block',
      flexShrink: 0,
      color: 'primary.main',
      ...sx,
    }}
  />
);

AIAssistantIcon.propTypes = {
  size: PropTypes.number,
  sx: PropTypes.object,
  alt: PropTypes.string,
};

export default AIAssistantIcon;
