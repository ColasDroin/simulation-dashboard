#################### Imports ####################

# Import standard libraries
import dash_mantine_components as dmc
from dash import dcc

# Import functions
import plot

#################### Separation Layout ####################


def return_separation_layout(dic_sep_IPs):
    separation_layout = (
        dmc.Center(
            dmc.Stack(
                children=[
                    dmc.Center(
                        children=[
                            dmc.Group(
                                children=[
                                    dmc.Text("Separation plane: "),
                                    dmc.ChipGroup(
                                        [
                                            dmc.Chip(
                                                x,
                                                value=x,
                                                variant="outline",
                                                color="cyan",
                                            )
                                            for x in ["v", "h"]
                                        ],
                                        id="chips-sep",
                                        value="v",
                                        mb=0,
                                    ),
                                ],
                                pt=10,
                            ),
                        ],
                    ),
                    dcc.Loading(
                        dcc.Graph(
                            id="beam-separation",
                            mathjax=True,
                            config={
                                "displayModeBar": False,
                                "scrollZoom": True,
                                "responsive": True,
                                "displaylogo": False,
                            },
                            figure=plot.return_plot_separation(dic_sep_IPs),
                            style={"height": "90vh", "width": "100%", "margin": "auto"},
                        ),
                        type="circle",
                        style={"height": "100%", "width": "100%", "margin": "auto"},
                        parent_style={"height": "100%", "width": "100%", "margin": "auto"},
                    ),
                ],
                style={"width": "100%", "margin": "auto"},
            )
        ),
    )
    return separation_layout