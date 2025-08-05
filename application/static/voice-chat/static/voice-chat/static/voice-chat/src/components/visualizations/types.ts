// Types for the visualization system

export interface HighlightAction {
  timestamp: number; // When in speech to trigger (seconds)
  target: string | number; // Data point identifier or index
  action: 'highlight' | 'pulse' | 'zoom' | 'focus' | 'reveal';
  duration?: number; // How long the highlight lasts
  color?: string; // Custom highlight color
}

export interface VisualizationData {
  type: 'bar' | 'line' | 'pie' | 'area' | 'scatter' | 'table' | 'metric';
  title?: string;
  data: any[];
  highlights: HighlightAction[];
  config?: {
    xKey?: string;
    yKey?: string;
    colors?: string[];
    animated?: boolean;
    responsive?: boolean;
  };
}

export interface LLMVisualizationResponse {
  speechText: string;
  speechMarkers?: {
    [marker: string]: number; // timestamp in seconds
  };
  visualizations: VisualizationData[];
  presentationMode?: boolean;
}

export interface ChartHighlightState {
  activeTarget: string | number | null;
  action: HighlightAction['action'] | null;
  color: string;
  startTime: number;
}