'''Elements for the control panel of the application.'''
from shiny import ui

def get_control_panel(mineral_families, default_satellite):
    """Return the control panel component"""
    return ui.div(
        {"class": "card control-card"},
        ui.h3("Control Panel", style="margin-top: 0;"),
        
        ui.layout_columns(
            get_satellite_selection(default_satellite),
            get_mineral_family_selection(mineral_families),
            get_individual_mineral_selection(),
            get_display_options(),
            col_widths=[3, 3, 3, 3]
        ),
        
        # Status Info
        ui.output_ui("status_info")
    )

def get_satellite_selection(default_satellite):
    """Satellite selection component"""
    return ui.div(
        ui.h5("Satellite Sensor"),
        ui.input_select(
            "satellite",
            None,
            choices=["ASTER", "Landsat8", "Sentinel2", "WorldView3"],
            selected=default_satellite
        ),
        ui.input_action_button("load_data", "Load Data", class_="btn-primary btn-sm")
    )

def get_mineral_family_selection(mineral_families):
    """Mineral family selection component"""
    return ui.div(
        ui.h5("Mineral Family"),
        ui.input_select(
            "mineral_family",
            None,
            choices=mineral_families if mineral_families else ["No data loaded"],
            selected=mineral_families[0] if mineral_families else None
        ),
        #ui.input_action_button("mineral_viz", "Visualise Mineral Spectra", class_="btn-primary btn-sm")
    )

def get_individual_mineral_selection():
    """Individual mineral selection component"""
    return ui.div(
        ui.h5("Individual Samples"),
        ui.input_select(
            "individual_mineral",
            None,
            choices=[],
            selected=None,
            multiple=True,
            size="5"
        )
    )

def get_display_options():
    """Display options component"""
    return ui.div(
        ui.h5("Display Options"),
        ui.input_slider(
            "max_samples",
            "Max Samples:",
            min=1, max=20, value=5, step=1
        ),
        ui.input_checkbox("show_band_centers", "Band Centers", value=True),
        ui.input_checkbox("show_band_ranges", "Band Ranges", value=True),
        ui.input_checkbox("show_response_functions", "Response Functions", value=True)
    )