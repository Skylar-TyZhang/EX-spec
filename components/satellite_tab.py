from shiny import ui

def get_satellite_tab(mineral_families, default_satellite):
    """Return the satellite resampled spectra tab component"""
    return ui.nav_panel(
        "Satellite Resampled Spectra",
        ui.div(
            {"class": "tab-content"},
            
            # Control Panel for Satellite Data
            _get_satellite_control_panel(mineral_families, default_satellite),
            
            # Main Content
            ui.navset_tab(
                # Spectral Data Sub-tab
                ui.nav_panel(
                    "Spectral Data",
                    ui.div(
                        {"class": "tab-content"},
                        _get_satellite_spectral_plot_card(),
                        _get_satellite_data_table_card()
                    )
                ),
                
                # Band Information Sub-tab
                ui.nav_panel(
                    "Band Information",
                    ui.div(
                        {"class": "tab-content"},
                        _get_satellite_band_info_card()
                    )
                )
            )
        )
    )

def _get_satellite_control_panel(mineral_families, default_satellite):
    """Satellite control panel component"""
    return ui.div(
        {"class": "card control-card"},
        ui.h3("Satellite Control Panel", style="margin-top: 0;"),
        
        ui.layout_columns(
            # Satellite Selection
            ui.div(
                ui.h5("Satellite Sensor"),
                ui.input_select(
                    "satellite",
                    None,
                    choices=["ASTER", "Landsat8", "Sentinel2", "WorldView3"],
                    selected=default_satellite
                )
            ),
            
            # Chapter Selection
            ui.div(
                ui.h5("Data Chapters"),
                ui.input_checkbox_group(
                    "satellite_chapters",
                    None,
                    choices={
                        'M': 'Minerals',
                        'S': 'Soils & Mixtures',
                        'V': 'Vegetation',
                        'C': 'Coatings',
                        'L': 'Liquids',
                        'O': 'Organic Compounds',
                        'A': 'Artificial Materials'
                    },
                    selected=['M']  # Default to Minerals
                )
            ),

            # Mineral Family Selection (Multiple)
            ui.div(
                ui.h5("Mineral Families"),
                ui.input_select(
                    "satellite_mineral_families",
                    None,
                    choices=mineral_families if mineral_families else ["No data loaded"],
                    selected=mineral_families[:min(3, len(mineral_families))] if mineral_families else None,
                    multiple=True,
                    size="5"
                )
            ),
            
            # Individual Mineral Selection
            ui.div(
                ui.h5("Individual Samples"),
                ui.input_select(
                    "satellite_individual_minerals",
                    None,
                    choices=[],
                    selected=None,
                    multiple=True,
                    size="5"
                )
            ),
            
            # Display Options
            ui.div(
                ui.h5("Display Options"),
                ui.input_slider(
                    "satellite_max_samples",
                    "Max Samples per Family:",
                    min=1, max=20, value=5, step=1
                ),
                ui.input_checkbox("satellite_show_band_centers", "Band Centers", value=True),
                ui.input_checkbox("satellite_show_band_ranges", "Band Ranges", value=True),
                ui.input_checkbox("satellite_show_response_functions", "Response Functions", value=True),
                ui.input_checkbox("satellite_show_atmospheric_transmission", "Atmospheric Transmission", value=False)
            ),
            
            col_widths=[3, 3, 3, 3]
        ),
        
        # Status Info
        ui.output_ui("satellite_status_info")
    )

def _get_satellite_spectral_plot_card():
    """Satellite spectral visualisation plot card"""
    return ui.div(
        {"class": "card plot-card"},
        
        ui.output_ui("satellite_main_plot", height="700px")
    )

def _get_satellite_data_table_card():
    """Satellite selected mineral data table card"""
    return ui.div(
        {"class": "card"},        
        ui.div(
            ui.h4("Selected Satellite Mineral Data", style="margin-top: 0;"),
            ui.div(
                ui.download_button("download_satellite_table", "Download Data", 
                                 class_="btn-success download-btn btn-sm"),
                style="float: right;"
            ),
            style="overflow: auto;"
        ),
        ui.output_data_frame("satellite_selected_mineral_table")
    )

def _get_satellite_band_info_card():
    """Satellite band information summary card"""
    return ui.div(
        {"class": "card info-card"},
        ui.div(
            ui.h4("Satellite Band Information Summary", style="margin-top: 0;"),
            ui.div(
                ui.download_button(
                    "download_satellite_band_table",
                    "Download Table",
                    class_="btn-success download-btn btn-sm",
                ),
                style="float: right;",
            ),
            style="overflow: auto;",
        ),
        ui.output_data_frame("satellite_band_info_table"),
    )