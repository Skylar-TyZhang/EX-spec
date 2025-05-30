from shiny import ui


def get_band_info_tab():
    """Return the band information tab component"""
    return ui.nav_panel(
        "Band Information",
        ui.div({"class": "tab-content"}, _get_band_info_card(), _get_band_plot_card()),
    )


def _get_band_info_card():
    """Band information summary card"""
    return ui.div(
        {"class": "card info-card"},
        ui.div(
            ui.h4("Band Information Summary", style="margin-top: 0;"),
            ui.div(
                ui.input_action_button(
                    "download_band_table",
                    "Download Table",
                    class_="btn-success download-btn btn-sm",
                ),
                style="float: right;",
            ),
            style="overflow: auto;",
        ),
        ui.output_data_frame("band_info_table"),
    )


def _get_band_plot_card():
    """Band response functions plot card"""
    return ui.div(
        {"class": "card plot-card"},
        ui.div(
            ui.h4("Band Response Functions", style="margin-top: 0;"),
            # Download button for the band plot
            ui.div(
                ui.input_action_button(
                    "download_band_plot",
                    "Download Plot",
                    class_="btn-info download-btn btn-sm",
                ),
                style="float: right;",
            ),
            style="overflow: auto;",
        ),
        ui.output_plot("band_plot", height="500px"),
    )
