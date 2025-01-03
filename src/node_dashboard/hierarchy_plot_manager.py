from typing import List, Dict, Tuple, Optional
import logging
import plotly.graph_objects as go
from igraph import Graph

from src.node_dashboard.helper.config import ContainerConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HierarchyPlotManager:
  """Manages the creation and visualization of hierarchical container relationships.

  This class handles the construction and visualization of hierarchical relationships
  between containers using Plotly for visualization and iGraph for graph operations.
  """

  def __init__(self, configs: List[ContainerConfig]):
    """Initialize the HierarchyPlotManager.

    Args:
        configs: List of container configurations to visualize
    """
    self.configs = configs

  @staticmethod
  def _create_depth_map(nodes: List[str]) -> Dict[str, int]:
    """Create a mapping of nodes to their depths.

    Args:
        nodes: List of node IDs

    Returns:
        Dictionary mapping node IDs to their depths
    """
    return {node: len(node.split('_')) for node in nodes}

  def _get_hierarchy_map(self) -> Dict[str, List[str]]:
    """Build parent-child relationships map.

    Returns:
        Dictionary mapping parent nodes to their children
    """
    try:
      hierarchy = {}
      for config in self.configs:
        parent = self._get_parent_id(config.node_id)
        if parent:
          hierarchy.setdefault(parent, []).append(config.node_id)

      # Sort children by depth and ID
      depth_map = self._create_depth_map([config.node_id for config in self.configs])
      for parent in hierarchy:
        hierarchy[parent].sort(key=lambda x: (depth_map[x], x))

      return hierarchy
    except Exception as e:
      logger.error(f'Failed to build hierarchy map: {e}')
      raise ValueError('Invalid node configuration') from e

  @staticmethod
  def _get_parent_id(node_id: str) -> Optional[str]:
    """Extract parent ID from a node ID.

    Args:
        node_id: Node identifier

    Returns:
        Parent node ID if it exists, None otherwise
    """
    parts = node_id.split('_')
    return '_'.join(parts[:-1]) if len(parts) > 1 else None

  def _prepare_graph_data(self) -> Tuple[List[Tuple[str, str]], List[str]]:
    """Prepare edges and vertices for graph creation.

    Returns:
        Tuple containing list of edges and list of vertices
    """
    try:
      hierarchy = self._get_hierarchy_map()

      # Collect all unique nodes
      nodes = {
        node for parent, children in hierarchy.items() for node in [parent] + children
      }

      # Sort vertices by depth
      depth_map = self._create_depth_map(list(nodes))
      vertices = sorted(nodes, key=lambda x: (depth_map[x], x))

      # Create edges
      edges = [
        (parent, child) for parent, children in hierarchy.items() for child in children
      ]

      return edges, vertices
    except Exception as e:
      logger.error(f'Failed to prepare graph data: {e}')
      raise

  def _create_visualization(
    self, graph: Graph, vertices: List[str]
  ) -> Tuple[go.Figure, dict]:
    """Create visualization traces and layout.

    Args:
        graph: iGraph Graph object
        vertices: List of vertex labels

    Returns:
        Tuple of Plotly figure and layout settings
    """
    try:
      layout = graph.layout_sugiyama()
      node_positions = {i: layout[i] for i in range(len(vertices))}

      # Prepare node coordinates
      x_nodes = [pos[0] for pos in node_positions.values()]
      y_nodes = [-pos[1] for pos in node_positions.values()]

      # Prepare edge coordinates
      edges = [(e.source, e.target) for e in graph.es]
      x_edges, y_edges = [], []
      for edge in edges:
        x_edges.extend([node_positions[edge[0]][0], node_positions[edge[1]][0], None])
        y_edges.extend([-node_positions[edge[0]][1], -node_positions[edge[1]][1], None])

      return self._create_plotly_figure(x_nodes, y_nodes, x_edges, y_edges, vertices)
    except Exception as e:
      logger.error(f'Failed to create visualization: {e}')
      raise

  def _create_plotly_figure(
    self,
    x_nodes: List[float],
    y_nodes: List[float],
    x_edges: List[float],
    y_edges: List[float],
    labels: List[str],
  ) -> go.Figure:
    """Create and configure Plotly figure.

    Args:
        x_nodes: X coordinates for nodes
        y_nodes: Y coordinates for nodes
        x_edges: X coordinates for edges
        y_edges: Y coordinates for edges
        labels: Node labels

    Returns:
        Configured Plotly figure
    """
    fig = go.Figure()

    # Add edges
    fig.add_trace(
      go.Scatter(
        x=x_edges,
        y=y_edges,
        mode='lines',
        line=dict(color='rgba(210,210,210,0.6)', width=1.5),
        hoverinfo='none',
      )
    )

    # Add nodes
    fig.add_trace(
      go.Scatter(
        x=x_nodes,
        y=y_nodes,
        mode='markers+text',
        name='Nodes',
        marker=dict(
          symbol='circle-dot',
          size=30,
          color='rgba(24, 115, 250, 0.8)',
          line=dict(color='rgba(50, 50, 50, 1)', width=1.5),
        ),
        text=labels,
        textposition='middle center',
        hoverinfo='text',
        opacity=0.9,
      )
    )

    # Configure layout
    fig.update_layout(
      showlegend=False,
      xaxis=dict(
        showgrid=False,
        zeroline=False,
        visible=False,
        range=[min(x_nodes) - 1, max(x_nodes) + 1],
      ),
      yaxis=dict(
        showgrid=False,
        zeroline=False,
        visible=False,
        range=[min(y_nodes) - 1, max(y_nodes) + 1],
        scaleanchor='x',
        scaleratio=1,
      ),
      font_color='white',
      template='plotly_dark',
      plot_bgcolor='rgba(0,0,0,0)',
      paper_bgcolor='rgba(0,0,0,0)',
      margin=dict(t=40, b=40, l=40, r=40),
    )

    return fig

  def visualize_hierarchy(self) -> go.Figure:
    """Create a hierarchical visualization of the container relationships.

    Returns:
        Plotly figure object containing the visualization

    Raises:
        ValueError: If the container configuration is invalid
        RuntimeError: If visualization creation fails
    """
    try:
      edges, vertices = self._prepare_graph_data()

      # Create and configure graph
      graph = Graph(directed=True)
      graph.add_vertices(len(vertices))
      graph.add_edges(
        [(vertices.index(parent), vertices.index(child)) for parent, child in edges]
      )

      return self._create_visualization(graph, vertices)
    except Exception as e:
      logger.error(f'Failed to create hierarchy visualization: {e}')
      raise RuntimeError(f'Visualization creation failed: {str(e)}') from e
