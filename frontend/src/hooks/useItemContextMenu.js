import { useState, useCallback } from 'react';

/**
 * Custom hook for managing context menus on items (files/folders)
 * Provides consistent menu state management across components
 *
 * @returns {Object} Menu state and control functions
 */
const useItemContextMenu = () => {
  const [menuAnchorEl, setMenuAnchorEl] = useState(null);
  const [selectedItem, setSelectedItem] = useState(null);

  const handleMenuOpen = useCallback((event, item) => {
    event.stopPropagation();
    setMenuAnchorEl(event.currentTarget);
    setSelectedItem(item);
  }, []);

  const handleMenuClose = useCallback(() => {
    setMenuAnchorEl(null);
  }, []);

  const clearSelection = useCallback(() => {
    setMenuAnchorEl(null);
    setSelectedItem(null);
  }, []);

  const isMenuOpen = Boolean(menuAnchorEl);

  return {
    menuAnchorEl,
    selectedItem,
    isMenuOpen,
    handleMenuOpen,
    handleMenuClose,
    clearSelection
  };
};

export default useItemContextMenu;
