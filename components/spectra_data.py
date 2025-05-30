from shiny import ui

def get_spectral_data_tab():
    """Return the spectral data tab component"""
    return ui.nav_panel(
        "Spectral Data",
        ui.div(
            {"class": "tab-content"},
            _get_spectral_plot_card(),
            _get_data_table_card()
        )
    )

def _get_spectral_plot_card():
    """Spectral visualization plot card"""
    return ui.div(
        {"class": "card plot-card"},
        ui.div(
            ui.h4("Spectral Visualization", style="margin-top: 0;"),
            ui.div(
                ui.input_action_button("download_spectra_plot", "Download Plot", 
                                     class_="btn-info download-btn btn-sm"),
                style="float: right;"
            ),
            style="overflow: auto;"
        ),
        ui.output_plot("main_plot", height="500px")
    )

def _get_data_table_card():
    """Selected mineral data table card"""
    return ui.div(
        {"class": "card"},        
        ui.div(
            ui.h4("Selected Mineral Data", style="margin-top: 0;"),
            ui.div(
                ui.input_action_button("download_spectra_table", "Download Data", 
                                     class_="btn-success download-btn btn-sm"),
                style="float: right;"
            ),
            style="overflow: auto;"
        ),
        ui.output_data_frame("selected_mineral_table")
    )