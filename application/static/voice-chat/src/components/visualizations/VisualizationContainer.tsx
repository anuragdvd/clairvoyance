import React, { useRef, useCallback, useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { InteractiveChart } from './InteractiveChart';
import { InteractiveTable } from './InteractiveTable';
import { InteractiveMetric } from './InteractiveMetric';
import { VisualizationData, LLMVisualizationResponse, HighlightAction } from './types';

interface VisualizationContainerProps {
  llmResponse?: LLMVisualizationResponse;
  isPlaying?: boolean;
  currentTime?: number; // Current playback time in seconds
  activeTarget?: string | number | null; // Active highlight target from speech recognition
  onVisualizationInteraction?: (type: string, target: string | number) => void;
}

export const VisualizationContainer: React.FC<VisualizationContainerProps> = ({
  llmResponse,
  isPlaying = false,
  currentTime = 0,
  activeTarget = null,
  onVisualizationInteraction
}) => {
  const chartRefs = useRef<{ [key: number]: any }>({});
  const [activeHighlights, setActiveHighlights] = useState<Set<number>>(new Set());

  // Handle speech recognition highlights
  useEffect(() => {
    if (!activeTarget || !llmResponse?.visualizations) return;

    console.log('🎯 Processing activeTarget:', activeTarget);

    llmResponse.visualizations.forEach((viz, vizIndex) => {
      if (!viz.highlights) return;

      // Find highlight action for this target
      const highlight = viz.highlights.find(h => h.target === activeTarget);
      if (highlight) {
        console.log('🎯 Found highlight for target:', activeTarget, highlight);
        
        const chartRef = chartRefs.current[vizIndex];
        if (chartRef?.triggerHighlight) {
          chartRef.triggerHighlight(highlight);
          setActiveHighlights(prev => new Set(prev).add(vizIndex));
          
          // Track interaction
          if (onVisualizationInteraction) {
            onVisualizationInteraction(viz.type, highlight.target);
          }

          // Auto-clear highlight after duration
          setTimeout(() => {
            setActiveHighlights(prev => {
              const newSet = new Set(prev);
              newSet.delete(vizIndex);
              return newSet;
            });
          }, highlight.duration || 2000);
        }
      }
    });
  }, [activeTarget, llmResponse, onVisualizationInteraction]);

  // Process highlights based on current playback time
  useEffect(() => {
    if (!llmResponse?.visualizations || !isPlaying) return;

    llmResponse.visualizations.forEach((viz, vizIndex) => {
      if (!viz.highlights) return;

      viz.highlights.forEach((highlight) => {
        // Check if this highlight should be triggered now
        if (Math.abs(currentTime - highlight.timestamp) < 0.1) { // 100ms tolerance
          const chartRef = chartRefs.current[vizIndex];
          if (chartRef?.triggerHighlight) {
            chartRef.triggerHighlight(highlight);
            setActiveHighlights(prev => new Set(prev).add(vizIndex));
            
            // Track interaction
            if (onVisualizationInteraction) {
              onVisualizationInteraction(viz.type, highlight.target);
            }
          }
        }
      });
    });
  }, [currentTime, isPlaying, llmResponse, onVisualizationInteraction]);

  // Handle speech markers for enhanced synchronization
  useEffect(() => {
    if (!llmResponse?.speechMarkers || !isPlaying) return;

    Object.entries(llmResponse.speechMarkers).forEach(([marker, timestamp]) => {
      if (Math.abs(currentTime - timestamp) < 0.1) {
        // Trigger highlights for specific markers
        llmResponse.visualizations.forEach((viz, vizIndex) => {
          const relevantHighlight = viz.highlights.find(h => 
            marker.toLowerCase().includes(String(h.target).toLowerCase())
          );
          
          if (relevantHighlight) {
            const chartRef = chartRefs.current[vizIndex];
            if (chartRef?.triggerHighlight) {
              chartRef.triggerHighlight(relevantHighlight);
            }
          }
        });
      }
    });
  }, [currentTime, isPlaying, llmResponse]);

  const handleHighlight = useCallback((vizIndex: number) => {
    return (target: string | number, action: HighlightAction['action']) => {
      console.log(`Visualization ${vizIndex} highlighted:`, { target, action });
      if (onVisualizationInteraction) {
        onVisualizationInteraction(`highlight_${action}`, target);
      }
    };
  }, [onVisualizationInteraction]);

  const renderVisualization = (data: VisualizationData, index: number) => {
    const commonProps = {
      data,
      onHighlight: handleHighlight(index),
      ref: (ref: any) => {
        if (ref) chartRefs.current[index] = ref;
      }
    };

    switch (data.type) {
      case 'bar':
      case 'line':
      case 'pie':
      case 'area':
      case 'scatter':
        return <InteractiveChart key={index} {...commonProps} />;
      
      case 'table':
        return <InteractiveTable key={index} {...commonProps} />;
      
      case 'metric':
        return <InteractiveMetric key={index} {...commonProps} />;
      
      default:
        return (
          <div key={index} style={{ padding: '20px', textAlign: 'center' }}>
            <p>Unsupported visualization type: {data.type}</p>
          </div>
        );
    }
  };

  if (!llmResponse?.visualizations || llmResponse.visualizations.length === 0) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        style={{
          padding: '40px',
          textAlign: 'center',
          color: '#666',
          fontStyle: 'italic'
        }}
      >
        No visualizations available. Ask the AI to create charts, tables, or metrics!
      </motion.div>
    );
  }

  return (
    <motion.div
      className="visualization-container"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      style={{
        padding: '20px',
        backgroundColor: '#f8f9fa',
        borderRadius: '12px',
        margin: '20px 0'
      }}
    >
      {/* Presentation mode indicator */}
      {llmResponse.presentationMode && (
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          style={{
            background: 'linear-gradient(45deg, #667eea 0%, #764ba2 100%)',
            color: 'white',
            padding: '10px 20px',
            borderRadius: '25px',
            textAlign: 'center',
            marginBottom: '20px',
            fontWeight: 'bold',
            fontSize: '0.9em'
          }}
        >
          🎤 Presentation Mode Active
        </motion.div>
      )}

      {/* Speech text display */}
      {llmResponse.speechText && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          style={{
            backgroundColor: 'white',
            padding: '15px 20px',
            borderRadius: '8px',
            marginBottom: '20px',
            borderLeft: '4px solid #667eea',
            fontSize: '0.95em',
            lineHeight: '1.5'
          }}
        >
          <strong>🎙️ Voice Script:</strong><br />
          {llmResponse.speechText}
        </motion.div>
      )}

      {/* Visualizations grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: llmResponse.presentationMode ? '1fr' : 
          llmResponse.visualizations.length === 1 ? '1fr' :
          'repeat(auto-fit, minmax(400px, 1fr))',
        gap: '30px',
        minHeight: llmResponse.presentationMode ? '80vh' : 'auto'
      }}>
        <AnimatePresence>
          {llmResponse.visualizations.map((visualization, index) => (
            <motion.div
              key={index}
              layout
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ 
                opacity: 1, 
                scale: 1,
                zIndex: activeHighlights.has(index) ? 10 : 1
              }}
              exit={{ opacity: 0, scale: 0.9 }}
              transition={{ duration: 0.3 }}
              style={{
                backgroundColor: 'white',
                borderRadius: '12px',
                padding: '20px',
                boxShadow: activeHighlights.has(index) ? 
                  '0 8px 32px rgba(102, 126, 234, 0.3)' : 
                  '0 4px 16px rgba(0, 0, 0, 0.1)',
                border: activeHighlights.has(index) ? 
                  '2px solid #667eea' : 
                  '1px solid #e1e5e9',
                position: 'relative',
                overflow: 'hidden'
              }}
            >
              {renderVisualization(visualization, index)}
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      {/* Debug info in development */}
      {process.env.NODE_ENV === 'development' && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          style={{
            marginTop: '20px',
            padding: '10px',
            backgroundColor: '#fff3cd',
            borderRadius: '6px',
            fontSize: '0.8em',
            color: '#856404'
          }}
        >
          <strong>Debug:</strong> Playing: {isPlaying ? 'Yes' : 'No'}, 
          Time: {currentTime.toFixed(1)}s, 
          Active Highlights: {activeHighlights.size}
          {llmResponse.speechMarkers && (
            <div>Speech Markers: {Object.keys(llmResponse.speechMarkers).join(', ')}</div>
          )}
        </motion.div>
      )}
    </motion.div>
  );
};