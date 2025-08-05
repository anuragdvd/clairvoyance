import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, AreaChart, Area,
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import { VisualizationData, HighlightAction, ChartHighlightState } from './types';

interface InteractiveChartProps {
  data: VisualizationData;
  onHighlight?: (target: string | number, action: HighlightAction['action']) => void;
}

export const InteractiveChart: React.FC<InteractiveChartProps> = ({ data, onHighlight }) => {
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
      (window as any)[`chart_${data.title.replace(/\s+/g, '_')}`] = { triggerHighlight };
    }
  }, [triggerHighlight, data.title]);

  // Custom bar component with highlighting
  const CustomBar = (props: any) => {
    const { payload, ...restProps } = props;
    const isHighlighted = highlightState.activeTarget === payload?.name || 
                         highlightState.activeTarget === restProps.index;
    
    return (
      <motion.g
        animate={{
          scale: isHighlighted && highlightState.action === 'zoom' ? 1.1 : 1,
          opacity: isHighlighted && highlightState.action === 'focus' ? 1 : 
                  (highlightState.activeTarget !== null && !isHighlighted ? 0.3 : 1)
        }}
        transition={{ duration: 0.3 }}
      >
        <Bar
          {...restProps}
          fill={isHighlighted ? highlightState.color : restProps.fill}
          stroke={isHighlighted && highlightState.action === 'highlight' ? '#fff' : 'none'}
          strokeWidth={isHighlighted && highlightState.action === 'highlight' ? 2 : 0}
        />
        {isHighlighted && highlightState.action === 'pulse' && (
          <motion.circle
            cx={restProps.x + restProps.width / 2}
            cy={restProps.y + restProps.height / 2}
            r={20}
            fill="none"
            stroke={highlightState.color}
            strokeWidth={2}
            initial={{ scale: 0, opacity: 1 }}
            animate={{ scale: 2, opacity: 0 }}
            transition={{ duration: 1, repeat: Infinity }}
          />
        )}
      </motion.g>
    );
  };

  // Custom line dot component with highlighting
  const CustomDot = (props: any) => {
    const { payload, cx, cy, index, ...restProps } = props;
    const isHighlighted = highlightState.activeTarget === payload?.name || 
                         highlightState.activeTarget === index;

    return (
      <motion.circle
        cx={cx}
        cy={cy}
        r={isHighlighted ? 8 : 4}
        fill={isHighlighted ? highlightState.color : restProps.fill}
        stroke={isHighlighted ? '#fff' : 'none'}
        strokeWidth={isHighlighted ? 2 : 0}
        animate={{
          scale: isHighlighted && highlightState.action === 'pulse' ? [1, 1.5, 1] : 1
        }}
        transition={{
          duration: 0.8,
          repeat: highlightState.action === 'pulse' ? Infinity : 0
        }}
      />
    );
  };

  // Custom pie cell with highlighting
  const CustomPieCell = (entry: any, index: number) => {
    const isHighlighted = highlightState.activeTarget === entry.name || 
                         highlightState.activeTarget === index;
    
    return (
      <Cell
        key={`cell-${index}`}
        fill={isHighlighted ? highlightState.color : data.config?.colors?.[index] || '#8884d8'}
        stroke={isHighlighted && highlightState.action === 'highlight' ? '#fff' : 'none'}
        strokeWidth={isHighlighted && highlightState.action === 'highlight' ? 3 : 0}
      />
    );
  };

  const renderChart = () => {
    const commonProps = {
      data: data.data,
      margin: { top: 20, right: 30, left: 20, bottom: 5 }
    };

    const xKey = data.config?.xKey || 'name';
    const yKey = data.config?.yKey || 'value';
    
    // Support both 'seriesKeys' and 'yKeys' for backward compatibility
    const seriesKeys: string[] | undefined = data.config?.seriesKeys || data.config?.yKeys;

    switch (data.type) {
      case 'bar':
        return (
          <BarChart {...commonProps}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey={xKey} />
            <YAxis />
            <Tooltip />
            <Legend />
            {/* Render multiple series if seriesKeys are provided */}
            {seriesKeys ? (
              seriesKeys.map((seriesKey, index) => (
                <Bar 
                  key={seriesKey}
                  dataKey={seriesKey} 
                  name={seriesKey.charAt(0).toUpperCase() + seriesKey.slice(1)}
                  fill={data.config?.colors?.[index] || `hsl(${index * 60}, 70%, 50%)`}
                />
              ))
            ) : (
              <Bar 
                dataKey={yKey} 
                fill={data.config?.colors?.[0] || '#8884d8'}
              />
            )}
          </BarChart>
        );

      case 'line':
        return (
          <LineChart {...commonProps}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey={xKey} />
            <YAxis />
            <Tooltip />
            <Legend />
            {/* Render multiple series if seriesKeys are provided */}
            {seriesKeys ? (
              seriesKeys.map((seriesKey, index) => (
                <Line 
                  key={seriesKey}
                  type="monotone" 
                  dataKey={seriesKey}
                  name={seriesKey.charAt(0).toUpperCase() + seriesKey.slice(1)}
                  stroke={data.config?.colors?.[index] || `hsl(${index * 60}, 70%, 50%)`}
                  dot={<CustomDot />}
                  strokeWidth={3}
                />
              ))
            ) : (
              <Line 
                type="monotone" 
                dataKey={yKey}
                stroke={data.config?.colors?.[0] || '#8884d8'}
                dot={<CustomDot />}
                strokeWidth={3}
              />
            )}
          </LineChart>
        );

      case 'area':
        return (
          <AreaChart {...commonProps}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey={xKey} />
            <YAxis />
            <Tooltip />
            <Legend />
            <Area 
              type="monotone" 
              dataKey={yKey}
              stroke={data.config?.colors?.[0] || '#8884d8'}
              fill={data.config?.colors?.[0] || '#8884d8'}
              fillOpacity={0.6}
              dot={<CustomDot />}
            />
          </AreaChart>
        );

      case 'pie':
        return (
          <PieChart>
            <Pie
              data={data.data}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ name, percent }) => `${name}: ${((percent || 0) * 100).toFixed(0)}%`}
              outerRadius={120}
              fill="#8884d8"
              dataKey={yKey}
            >
              {data.data.map((entry, index) => CustomPieCell(entry, index))}
            </Pie>
            <Tooltip />
          </PieChart>
        );

      case 'scatter':
        return (
          <ScatterChart {...commonProps}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey={xKey} />
            <YAxis dataKey={yKey} />
            <Tooltip />
            <Legend />
            <Scatter 
              name="Data Points"
              data={data.data}
              fill={data.config?.colors?.[0] || '#8884d8'}
              shape={<CustomDot />}
            />
          </ScatterChart>
        );

      default:
        return <div>Unsupported chart type: {data.type}</div>;
    }
  };

  return (
    <motion.div
      className="interactive-chart"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      {data.title && (
        <motion.h3
          className="chart-title"
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
      
      <ResponsiveContainer width="100%" height={400}>
        {renderChart()}
      </ResponsiveContainer>

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
              fontWeight: 'bold'
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