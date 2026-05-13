import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button
} from '@mui/material';

const FormDialog = ({
  open,
  onClose,
  onSubmit,
  title,
  label,
  placeholder = '',
  initialValue = '',
  submitText = 'Submit',
  cancelText = 'Cancel',
  validateInput,
  helperText = ''
}) => {
  const [value, setValue] = useState(initialValue);
  const [error, setError] = useState('');

  useEffect(() => {
    if (open) {
      setValue(initialValue);
      setError('');
    }
  }, [open, initialValue]);

  const handleSubmit = (e) => {
    e.preventDefault();

    if (validateInput) {
      const validationError = validateInput(value);
      if (validationError) {
        setError(validationError);
        return;
      }
    }

    onSubmit(value);
    onClose();
    setValue('');
    setError('');
  };

  const handleChange = (e) => {
    setValue(e.target.value);
    if (error) {
      setError('');
    }
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      aria-labelledby="form-dialog-title"
      maxWidth="sm"
      fullWidth
    >
      <form onSubmit={handleSubmit}>
        <DialogTitle id="form-dialog-title">{title}</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label={label}
            type="text"
            fullWidth
            variant="outlined"
            value={value}
            onChange={handleChange}
            error={!!error}
            helperText={error || helperText}
            placeholder={placeholder}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose} color="primary">
            {cancelText}
          </Button>
          <Button
            type="submit"
            color="primary"
            variant="contained"
            disabled={!value.trim()}
          >
            {submitText}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
};

FormDialog.propTypes = {
  open: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  onSubmit: PropTypes.func.isRequired,
  title: PropTypes.string.isRequired,
  label: PropTypes.string.isRequired,
  placeholder: PropTypes.string,
  initialValue: PropTypes.string,
  submitText: PropTypes.string,
  cancelText: PropTypes.string,
  validateInput: PropTypes.func,
  helperText: PropTypes.string
};

export default FormDialog;
