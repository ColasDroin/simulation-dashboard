#################### Imports ####################

# Import standard libraries
import dash_mantine_components as dmc
from dash import dcc


# Import functions
import plot

#################### Filling scheme Layout ####################


def return_filling_scheme_layout():
    scheme_layout = dmc.Stack(
        children=[
            dmc.Alert(
                (
                    "Filling scheme analysis not available as no configuration was provided when"
                    " building the dashboard"
                ),
                title="No configuration provided!",
                id="filling-scheme-alert",
                style={"margin": "auto", "display": "none"},
            ),
            dcc.Loading(
                dcc.Graph(
                    id="filling-scheme-graph",
                    mathjax=True,
                    config={
                        "displayModeBar": False,
                        "scrollZoom": True,
                        "responsive": True,
                        "displaylogo": False,
                    },
                    style={"height": "90vh", "width": "100%", "margin": "auto"},
                ),
                type="circle",
                color="cyan",
            ),
        ]
    )
    return scheme_layout
