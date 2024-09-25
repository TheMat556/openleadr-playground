import dash
from dash import dcc, html
import dash.dependencies as dd
import sqlite3
import pandas as pd

from src.openleadr_node.config1.config import Config


class LiveCharting:
    """
    A class to create and manage a live charting application using Dash.

    Attributes
    ----------
    app : dash.Dash
        The Dash application instance.

    Methods
    -------
    initAppLayout()
        Initializes the layout of the Dash application.
    get_data()
        Retrieves data from an SQLite database and returns it as a DataFrame.
    register_callbacks()
        Registers the callback functions for updating the live graph.
    """

    def __init__(self, db_name, table_name, config: Config):
        """
        Initializes the LiveCharting class, setting up the Dash application,
        layout, and callback functions.
        """
        # Create a Dash application
        self.db_name = db_name
        self.table_name = table_name
        self.app = dash.Dash(__name__)
        self.initAppLayout()
        self.register_callbacks()
        self.config = config

    def initAppLayout(self):
        """
        Initializes the layout of the Dash application with a graph component
        and an interval component to trigger updates.

        The layout consists of:
        - A `dcc.Graph` component for displaying the live chart.
        - A `dcc.Interval` component for periodic updates.
        """
        self.app.layout = html.Div(
            [
                dcc.Graph(id="live-graph"),
                dcc.Interval(
                    id="interval-component",
                    interval=1 * 1000,  # Update every second
                    n_intervals=0,
                ),
            ]
        )

    def get_data(self):
        """
        Retrieves data from an SQLite database.

        Connects to the database, executes a query to fetch all data from the
        'data' table, and returns it as a pandas DataFrame.

        Returns
        -------
        pandas.DataFrame
            DataFrame containing the data from the database.
        """
        conn = sqlite3.connect(self.db_name)
        query = f"SELECT * FROM {self.table_name} WHERE ven_id = '{self.config.get_ven_id()}'"
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df

    def register_callbacks(self):
        """
        Registers callback functions to update the live graph based on data
        and user interactions.

        The callback updates the graph figure with data from the database and
        preserves user interactions such as zoom and pan.
        """

        @self.app.callback(
            dd.Output("live-graph", "figure"),
            [dd.Input("interval-component", "n_intervals")],
            [dd.State("live-graph", "relayoutData")],
        )
        def update_graph_live(n, relayoutData):
            """
            Updates the graph with live data from the database.

            Parameters
            ----------
            n : int
                The number of intervals elapsed since the last update.
            relayoutData : dict
                A dictionary containing the current layout state of the graph.

            Returns
            -------
            dict
                A dictionary defining the figure's data and layout.
            """
            # Ensure relayoutData is not None
            if relayoutData is None:
                relayoutData = {}

            df = self.get_data()
            figure = {
                "data": [
                    {"x": df["time"], "y": df["value"], "type": "line", "name": "Value"}
                ],
                "layout": {
                    "title": "Live Data from SQLite Database",
                    "uirevision": "live-graph",  # Preserve user interaction state
                    "xaxis": {
                        "range": relayoutData.get("xaxis.range", [None, None]),
                        "autorange": (
                            True if "xaxis.autorange" in relayoutData else False
                        ),
                    },
                    "yaxis": {
                        "range": relayoutData.get("yaxis.range", [None, None]),
                        "autorange": (
                            True if "yaxis.autorange" in relayoutData else False
                        ),
                    },
                },
            }
            return figure


if __name__ == "__main__":
    chart = LiveCharting()
    chart.app.run_server(debug=True)
