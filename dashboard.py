#################### Imports ####################

# Import standard libraries
import dash_mantine_components as dmc
from dash_iconify import DashIconify
from dash import Dash, html, dcc, Input, Output, State, ctx
import dash
import numpy as np
import base64
import xtrack as xt
import io
import json
import yaml

# Import plotting functions
import functions

# Import layout functions
from layout.configuration import return_configuration_layout
from layout.filling import return_filling_scheme_layout
from layout.optics import return_optics_layout
from layout.sanity import return_sanity_layout
from layout.survey import return_survey_layout
from layout.header import return_header_layout
from layout.tables import return_tables_layout

#################### Load global variables ####################

# Path to configuration file
path_configuration = "/afs/cern.ch/work/c/cdroin/private/example_DA_study/master_study/scans/opt_flathv_75_1500_withBB_chroma5_1p4_eol_bunch_scan/base_collider/xtrack_0002/config.yaml"

# Load configuration file
with open(path_configuration, "r") as fid:
    configuration = yaml.safe_load(fid)["config_collider"]
    num_particles_per_bunch = float(configuration["config_beambeam"]["num_particles_per_bunch"])
    nemitt_x = configuration["config_beambeam"]["nemitt_x"]
    nemitt_y = configuration["config_beambeam"]["nemitt_y"]
    sigma_z = configuration["config_beambeam"]["sigma_z"]

# Load the filling scheme
path_filling_scheme = "/afs/cern.ch/work/c/cdroin/private/example_DA_study/master_study/master_jobs/filling_scheme/8b4e_1972b_1960_1178_1886_224bpi_12inj_800ns_bs200ns.json"
with open(path_filling_scheme) as fid:
    filling_scheme = json.load(fid)

array_b1 = np.array(filling_scheme["beam1"])
array_b2 = np.array(filling_scheme["beam2"])

# Assert that the arrays have the required length, and do the convolution
assert len(array_b1) == len(array_b2) == 3564
n_collisions_ip1_and_5 = array_b1 @ array_b2
n_collisions_ip2 = np.roll(array_b1, -891) @ array_b2
n_collisions_ip8 = np.roll(array_b1, -2670) @ array_b2
l_ncollisions = [n_collisions_ip1_and_5, n_collisions_ip2, n_collisions_ip8]
# Get collider variables
collider, tw_b1, df_sv_b1, df_tw_b1, tw_b2, df_sv_b2, df_tw_b2, df_elements_corrected = (
    functions.return_all_loaded_variables(
        collider_path="/afs/cern.ch/work/c/cdroin/private/comparison_pymask_xmask/xmask/xsuite_lines/collider_03_tuned_and_leveled_bb_off.json"
    )
)

# Get corresponding data tables
table_sv_b1 = functions.return_data_table(df_sv_b1, "id-df-sv-b1", twiss=False)
table_tw_b1 = functions.return_data_table(df_tw_b1, "id-df-tw-b1", twiss=True)
table_sv_b2 = functions.return_data_table(df_sv_b2, "id-df-sv-b2", twiss=False)
table_tw_b2 = functions.return_data_table(df_tw_b2, "id-df-tw-b2", twiss=True)


#################### App ####################
app = Dash(
    __name__,
    title="Dashboard for current simulation",
    external_scripts=[
        "https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.5/MathJax.js?config=TeX-MML-AM_CHTML"
    ],
    # suppress_callback_exceptions=True,
)
server = app.server

#################### App Layout ####################

layout = html.Div(
    style={"width": "90%", "margin": "auto"},
    children=[
        return_header_layout(),
        dmc.Center(
            children=[
                html.Div(
                    id="main-div",
                    style={"width": "100%", "margin": "auto"},
                    children=[
                        html.Div(id="placeholder-tabs"),
                    ],
                ),
            ],
            style={"margin-top": "75px"},
        ),
    ],
)

# Dark theme
layout = dmc.MantineProvider(
    withGlobalStyles=True,
    theme={"colorScheme": "dark"},
    children=layout,
)

app.layout = layout


#################### App Callbacks ####################


@app.callback(Output("placeholder-tabs", "children"), Input("tab-titles", "value"))
def select_tab(value):
    match value:
        case "display-configuration":
            return return_configuration_layout(path_configuration)
        case "display-twiss":
            return return_tables_layout()
        case "display-scheme":
            return return_filling_scheme_layout(array_b1, array_b2)
        case "display-sanity":
            return return_sanity_layout(
                tw_b1, tw_b2, l_ncollisions, num_particles_per_bunch, nemitt_x, nemitt_y, sigma_z
            )
        case "display-optics":
            return return_optics_layout(tw_b1, tw_b2, df_sv_b1, df_elements_corrected)
        case "display-survey":
            return return_survey_layout()
        case _:
            return return_configuration_layout(path_configuration)


@app.callback(Output("placeholder-data-table", "children"), Input("segmented-data-table", "value"))
def select_data_table(value):
    match value:
        case "Twiss table beam 1":
            return table_tw_b1
        case "Survey table beam 1":
            return table_sv_b1
        case "Twiss table beam 2":
            return table_tw_b2
        case "Survey table beam 2":
            return table_sv_b2
        case _:
            return table_tw_b1


@app.callback(
    Output("LHC-layout", "figure"),
    Input("chips-ip", "value"),
)
def update_graph_LHC_layout(l_values):
    l_indices_to_keep = []
    for val in l_values:
        str_ind_1, str_ind_2 = val.split("-")
        # Get indices of elements to keep (# ! implemented only for beam 1)
        l_indices_to_keep.extend(
            functions.get_indices_of_interest(df_tw_b1, "ip" + str_ind_1, "ip" + str_ind_2)
        )

    fig = functions.return_plot_lattice_with_tracking(
        df_sv_b1,
        df_elements_corrected,
        df_tw_b1,
        df_sv_2=df_sv_b2,
        df_tw_2=df_tw_b2,
        l_indices_to_keep=l_indices_to_keep,
    )

    return fig


@app.callback(
    Output("text-element", "children"),
    Output("title-element", "children"),
    Output("type-element", "children"),
    Output("drawer-magnets", "opened"),
    Input("LHC-layout", "clickData"),
    prevent_initial_call=False,
)
def update_text_graph_LHC_2D(clickData):
    if clickData is not None:
        if "customdata" in clickData["points"][0]:
            name = clickData["points"][0]["customdata"]
            if name.startswith("mb"):
                type_text = "Dipole"
                try:
                    set_var = collider.lhcb1.element_refs[name].knl[0]._expr._get_dependencies()
                except:
                    set_var = (
                        collider.lhcb1.element_refs[name + "..1"].knl[0]._expr._get_dependencies()
                    )
            elif name.startswith("mq"):
                type_text = "Quadrupole"
                try:
                    set_var = collider.lhcb1.element_refs[name].knl[1]._expr._get_dependencies()
                except:
                    set_var = (
                        collider.lhcb1.element_refs[name + "..1"].knl[1]._expr._get_dependencies()
                    )
            elif name.startswith("ms"):
                type_text = "Sextupole"
                try:
                    set_var = collider.lhcb1.element_refs[name].knl[2]._expr._get_dependencies()
                except:
                    set_var = (
                        collider.lhcb1.element_refs[name + "..1"].knl[2]._expr._get_dependencies()
                    )
            elif name.startswith("mo"):
                type_text = "Octupole"
                try:
                    set_var = collider.lhcb1.element_refs[name].knl[3]._expr._get_dependencies()
                except:
                    set_var = (
                        collider.lhcb1.element_refs[name + "..1"].knl[3]._expr._get_dependencies()
                    )

            text = []
            for var in set_var:
                name_var = str(var).split("'")[1]
                val = collider.lhcb1.vars[name_var]._get_value()
                expr = collider.lhcb1.vars[name_var]._expr
                if expr is not None:
                    dependencies = collider.lhcb1.vars[name_var]._expr._get_dependencies()
                else:
                    dependencies = "No dependencies"
                    expr = "No expression"
                targets = collider.lhcb1.vars[name_var]._find_dependant_targets()

                text.append(dmc.Text("Name: ", weight=500))
                text.append(dmc.Text(name_var, size="sm"))
                text.append(dmc.Text("Element value: ", weight=500))
                text.append(dmc.Text(str(val), size="sm"))
                text.append(dmc.Text("Expression: ", weight=500))
                text.append(dmc.Text(str(expr), size="sm"))
                text.append(dmc.Text("Dependencies: ", weight=500))
                text.append(dmc.Text(str(dependencies), size="sm"))
                text.append(dmc.Text("Targets: ", weight=500))
                if len(targets) > 10:
                    text.append(
                        dmc.Text(str(targets[:10]), size="sm"),
                    )
                    text.append(dmc.Text("...", size="sm"))
                else:
                    text.append(dmc.Text(str(targets), size="sm"))

            return text, name, type_text, True

    return (
        dmc.Text("Please click on a multipole to get the corresponding knob information."),
        dmc.Text("Click !"),
        dmc.Text("Undefined type"),
        False,
    )


#################### Launch app ####################
if __name__ == "__main__":
    app.run_server(debug=False, host="0.0.0.0", port=8050)


# Run with gunicorn app:server -b :8000
# Run silently with nohup gunicorn app:server -b :8000 &
# Kill with pkill gunicorn
