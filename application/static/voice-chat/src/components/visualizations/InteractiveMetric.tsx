import React, { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { VisualizationData, HighlightAction, ChartHighlightState } from './types';

interface InteractiveMetricProps {
  data: VisualizationData;
  onHighlight?: (target: string | number, action: HighlightAction['action']) => void;
}

export const InteractiveMetric: React.FC<InteractiveMetricProps> = ({ data, onHighlight }) => {
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
      (window as any)[`metric_${data.title.replace(/\s+/g, '_')}`] = { triggerHighlight };
    }
  }, [triggerHighlight, data.title]);

  if (!data.data || data.data.length === 0) {
    return <div>No metric data available</div>;
  }

  const isMetricHighlighted = (metric: any, index: number) => {
    return highlightState.activeTarget === metric.name ||
           highlightState.activeTarget === metric.id ||
           highlightState.activeTarget === index;
  };

  const formatValue = (value: any) => {
    if (typeof value === 'number') {
      // Format large numbers with commas
      if (value >= 1000000) {
        return `${(value / 1000000).toFixed(1)}M`;
      } else if (value >= 1000) {
        return `${(value / 1000).toFixed(1)}K`;
      }
      return value.toLocaleString();
    }
    return value;
  };

  return (
    <motion.div
      className="interactive-metrics"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      style={{ position: 'relative' }}
    >
      {data.title && (
        <motion.h3
          className="metrics-title"
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
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '20px',
        padding: '20px'
      }}>
        {data.data.map((metric, index) => {
          const isHighlighted = isMetricHighlighted(metric, index);
          
          return (
            <motion.div
              key={metric.name || index}
              className="metric-card"
              animate={{
                scale: isHighlighted && highlightState.action === 'zoom' ? 1.1 : 1,
                opacity: highlightState.activeTarget !== null && !isHighlighted ? 0.3 : 1,
                borderColor: isHighlighted ? highlightState.color : '#e1e5e9',
                backgroundColor: isHighlighted ? `${highlightState.color}10` : '#fff'
              }}
              transition={{ duration: 0.3 }}
              style={{
                border: '2px solid #e1e5e9',
                borderRadius: '12px',
                padding: '24px',
                textAlign: 'center',
                backgroundColor: '#fff',
                boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                position: 'relative',
                overflow: 'hidden'
              }}
              whileHover={{ 
                scale: 1.02,
                boxShadow: '0 4px 16px rgba(0,0,0,0.15)'
              }}
            >
              {/* Background pulse effect */}
              {isHighlighted && highlightState.action === 'pulse' && (
                <motion.div
                  style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    right: 0,
                    bottom: 0,
                    background: `linear-gradient(45deg, ${highlightState.color}20, transparent)`,
                    borderRadius: '10px'
                  }}
                  animate={{
                    opacity: [0.3, 0.7, 0.3]
                  }}
                  transition={{
                    duration: 1.5,
                    repeat: Infinity,
                    ease: "easeInOut"
                  }}
                />
              )}

              {/* Metric label */}
              <motion.div
                style={{
                  fontSize: '0.9em',
                  color: '#666',
                  marginBottom: '8px',
                  fontWeight: '500',
                  textTransform: 'uppercase',
                  letterSpacing: '0.5px'
                }}
                animate={{
                  color: isHighlighted ? highlightState.color : '#666'
                }}
              >
                {metric.label || metric.name}
              </motion.div>

              {/* Metric value */}
              <motion.div
                style={{
                  fontSize: '2.5em',
                  fontWeight: 'bold',
                  color: '#333',
                  marginBottom: '8px',
                  lineHeight: '1'
                }}
                animate={{
                  color: isHighlighted ? highlightState.color : '#333',
                  scale: isHighlighted && highlightState.action === 'focus' ? 1.1 : 1
                }}
                transition={{ duration: 0.3 }}
              >
                {formatValue(metric.value)}
              </motion.div>

              {/* Optional unit */}
              {metric.unit && (
                <motion.div
                  style={{
                    fontSize: '0.8em',
                    color: '#888',
                    fontWeight: '400'
                  }}
                  animate={{
                    color: isHighlighted ? highlightState.color : '#888'
                  }}
                >
                  {metric.unit}
                </motion.div>
              )}

              {/* Optional change indicator */}
              {metric.change && (
                <motion.div
                  style={{
                    marginTop: '12px',
                    fontSize: '0.85em',
                    fontWeight: '500',
                    color: metric.change > 0 ? '#22c55e' : '#ef4444'
                  }}
                  animate={{
                    scale: isHighlighted && highlightState.action === 'highlight' ? 1.1 : 1
                  }}
                >
                  {metric.change > 0 ? '↗️' : '↘️'} {Math.abs(metric.change)}%
                </motion.div>
              )}

              {/* Highlight glow effect */}
              {isHighlighted && highlightState.action === 'highlight' && (
                <motion.div
                  style={{
                    position: 'absolute',
                    top: '-2px',
                    left: '-2px',
                    right: '-2px',
                    bottom: '-2px',
                    background: `linear-gradient(45deg, ${highlightState.color}, transparent, ${highlightState.color})`,
                    borderRadius: '14px',
                    zIndex: -1
                  }}
                  animate={{
                    backgroundPosition: ['0% 50%', '100% 50%', '0% 50%']
                  }}
                  transition={{
                    duration: 2,
                    repeat: Infinity,
                    ease: "linear"
                  }}
                />
              )}
            </motion.div>
          );
        })}
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