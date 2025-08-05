import React, { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { VisualizationData, HighlightAction, ChartHighlightState } from './types';

interface InteractiveTableProps {
  data: VisualizationData;
  onHighlight?: (target: string | number, action: HighlightAction['action']) => void;
}

export const InteractiveTable: React.FC<InteractiveTableProps> = ({ data, onHighlight }) => {
  const [highlightState, setHighlightState] = useState<ChartHighlightState>({
    activeTarget: null,
    action: null,
    color: '#ff6b6b',
    startTime: 0
  });

  const [currentHighlight, setCurrentHighlight] = useState<HighlightAction | null>(null);

  // Function to trigger highlight from external source (voice sync)
  const triggerHighlight = useCallback((highlight: HighlightAction) => {
    setCurrentHighlight(highlight);
    setHighlightState({
      activeTarget: highlight.target,
      action: highlight.action,
      color: highlight.color || '#ff6b6b',
      startTime: Date.now()
    });

    // Auto-clear highlight after duration
    if (highlight.duration) {
      setTimeout(() => {
        setHighlightState(prev => ({ ...prev, activeTarget: null, action: null }));
        setCurrentHighlight(null);
      }, highlight.duration);
    }

    if (onHighlight) {
      onHighlight(highlight.target, highlight.action);
    }
  }, [onHighlight]);

  // Expose triggerHighlight through a global reference (for demo purposes)
  React.useEffect(() => {
    if (data.title) {
      (window as any)[`table_${data.title.replace(/\s+/g, '_')}`] = { triggerHighlight };
    }
  }, [triggerHighlight, data.title]);

  if (!data.data || data.data.length === 0) {
    return <div>No data available</div>;
  }

  // Get table headers from first row
  const headers = Object.keys(data.data[0]);

  const isRowHighlighted = (index: number, value: any) => {
    return highlightState.activeTarget === index || 
           highlightState.activeTarget === value?.name ||
           highlightState.activeTarget === value?.id;
  };

  const isCellHighlighted = (rowIndex: number, colKey: string, value: any) => {
    return highlightState.activeTarget === `${rowIndex},${colKey}` ||
           highlightState.activeTarget === value;
  };

  return (
    <motion.div
      className="interactive-table"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      style={{ position: 'relative' }}
    >
      {data.title && (
        <motion.h3
          className="table-title"
          animate={{
            color: highlightState.activeTarget !== null ? highlightState.color : '#333'
          }}
          style={{
            textAlign: 'center',
            marginBottom: '20px',
            fontSize: '1.2em',
            fontWeight: 'bold'
          }}
        >
          {data.title}
        </motion.h3>
      )}

      <div style={{ 
        overflowX: 'auto', 
        maxHeight: '400px', 
        border: '1px solid #ddd',
        borderRadius: '8px'
      }}>
        <table style={{ 
          width: '100%', 
          borderCollapse: 'collapse',
          backgroundColor: 'white'
        }}>
          <thead>
            <tr style={{ backgroundColor: '#f5f5f5' }}>
              {headers.map((header, index) => (
                <th
                  key={header}
                  style={{
                    padding: '12px',
                    textAlign: 'left',
                    borderBottom: '2px solid #ddd',
                    fontWeight: 'bold',
                    position: 'sticky',
                    top: 0,
                    backgroundColor: '#f5f5f5',
                    zIndex: 1
                  }}
                >
                  {header.charAt(0).toUpperCase() + header.slice(1)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.data.map((row, rowIndex) => {
              const isRowHigh = isRowHighlighted(rowIndex, row);
              
              return (
                <motion.tr
                  key={rowIndex}
                  animate={{
                    backgroundColor: isRowHigh ? 
                      `${highlightState.color}20` : 
                      (rowIndex % 2 === 0 ? '#fff' : '#f9f9f9'),
                    scale: isRowHigh && highlightState.action === 'zoom' ? 1.02 : 1,
                    opacity: highlightState.activeTarget !== null && !isRowHigh ? 0.5 : 1
                  }}
                  transition={{ duration: 0.3 }}
                  style={{
                    borderBottom: '1px solid #eee',
                    cursor: 'pointer'
                  }}
                  whileHover={{ backgroundColor: '#f0f0f0' }}
                >
                  {headers.map((header, colIndex) => {
                    const cellValue = row[header];
                    const isCellHigh = isCellHighlighted(rowIndex, header, cellValue);
                    
                    return (
                      <motion.td
                        key={`${rowIndex}-${colIndex}`}
                        animate={{
                          backgroundColor: isCellHigh ? highlightState.color : 'transparent',
                          color: isCellHigh ? 'white' : 'inherit',
                          fontWeight: isCellHigh ? 'bold' : 'normal'
                        }}
                        transition={{ duration: 0.3 }}
                        style={{
                          padding: '12px',
                          borderRight: colIndex < headers.length - 1 ? '1px solid #eee' : 'none',
                          position: 'relative'
                        }}
                      >
                        {cellValue}
                        
                        {/* Pulse effect for highlighted cells */}
                        {isCellHigh && highlightState.action === 'pulse' && (
                          <motion.div
                            style={{
                              position: 'absolute',
                              top: 0,
                              left: 0,
                              right: 0,
                              bottom: 0,
                              border: `2px solid ${highlightState.color}`,
                              borderRadius: '4px',
                              pointerEvents: 'none'
                            }}
                            animate={{
                              opacity: [0.3, 1, 0.3],
                              scale: [1, 1.05, 1]
                            }}
                            transition={{
                              duration: 1,
                              repeat: Infinity,
                              ease: "easeInOut"
                            }}
                          />
                        )}
                      </motion.td>
                    );
                  })}
                </motion.tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Highlight indicator */}
      <AnimatePresence>
        {currentHighlight && (
          <motion.div
            className="highlight-indicator"
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            style={{
              position: 'absolute',
              top: '10px',
              right: '10px',
              background: highlightState.color,
              color: 'white',
              padding: '5px 10px',
              borderRadius: '15px',
              fontSize: '0.8em',
              fontWeight: 'bold',
              zIndex: 10
            }}
          >
            {highlightState.action === 'highlight' && '🔍 Highlighting'}
            {highlightState.action === 'pulse' && '💫 Pulsing'}
            {highlightState.action === 'zoom' && '🔍 Zooming'}
            {highlightState.action === 'focus' && '🎯 Focusing'}
            {highlightState.action === 'reveal' && '✨ Revealing'}
            {` ${highlightState.activeTarget}`}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};