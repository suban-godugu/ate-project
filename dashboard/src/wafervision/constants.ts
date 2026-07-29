/** Spatial AI Agent live pipeline bakes all wafer PNGs at this fixed edge length. */
export const AGENT_IMAGE_SIZE = 224;

/**
 * Scale a coordinate from agent/model space (224×224) into a display canvas.
 * Never mix native upload resolution with agent image space.
 */
export function scaleFromAgent(
  value: number,
  displaySize: number,
  agentSize: number = AGENT_IMAGE_SIZE,
): number {
  return (value * displaySize) / agentSize;
}
