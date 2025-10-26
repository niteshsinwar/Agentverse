/**
 * Standardized sizing presets for SlidingPanel components
 * Use these to ensure consistent modal dimensions across the app
 */

export type PanelSize = 'small' | 'medium' | 'large' | 'xlarge' | 'full';

export interface PanelSizeConfig {
  maxWidthClassName: string;
  heightClassName: string;
  description: string;
}

/**
 * Predefined panel size configurations
 * All panels should use these instead of custom dimensions
 */
export const PANEL_SIZES: Record<PanelSize, PanelSizeConfig> = {
  small: {
    maxWidthClassName: 'w-[90vw] max-w-[600px]',
    heightClassName: 'h-[80vh] max-h-[600px]',
    description: 'Small panels - simple forms, confirmations',
  },
  medium: {
    maxWidthClassName: 'w-[90vw] max-w-[900px]',
    heightClassName: 'h-[85vh] max-h-[800px]',
    description: 'Medium panels - standard forms, single entity management',
  },
  large: {
    maxWidthClassName: 'w-[95vw] max-w-[1200px]',
    heightClassName: 'h-[90vh] max-h-[900px]',
    description: 'Large panels - complex forms, list + detail views',
  },
  xlarge: {
    maxWidthClassName: 'w-[95vw] max-w-[1600px]',
    heightClassName: 'h-[90vh]',
    description: 'Extra large panels - comprehensive management interfaces',
  },
  full: {
    maxWidthClassName: 'w-[98vw]',
    heightClassName: 'h-[95vh]',
    description: 'Full screen panels - maximum workspace (logs, documentation)',
  },
};

/**
 * Get size configuration for a panel
 * @param size - The desired panel size preset
 * @returns Configuration object with width and height class names
 */
export const getPanelSize = (size: PanelSize): PanelSizeConfig => {
  return PANEL_SIZES[size];
};

/**
 * Recommended sizes for common panel types:
 * 
 * - Help/Documentation: 'full'
 * - Logs/Monitoring: 'full'
 * - Agent Management: 'xlarge'
 * - MCP Management: 'xlarge'
 * - Tools Management: 'xlarge'
 * - Settings: 'large'
 * - Create/Edit Forms: 'medium'
 * - Confirmations: 'small'
 */
