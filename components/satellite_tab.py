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
            # Column 1: Satellite & Chapter Selection
            ui.div(
                ui.h5("Satellite Sensor"),
                ui.input_select(
                    "satellite",
                    None,
                    choices=["ASTER", "Landsat8", "Sentinel2", "WorldView3"],
                    selected=default_satellite
                ),
                ui.h5("Data Chapters", style="margin-top: 15px;"),
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
                    selected=['M']
                ),
                ui.help_text("Select which data chapters to load", style="font-size: 0.85em; color: #666;")
            ),
            
            # Column 2: Material Selection with Search
            ui.div(
                ui.h5("Material Families"),
                ui.input_text(
                    "satellite_material_search",
                    None,
                    placeholder="Search materials...",
                    value=""
                ),
                ui.input_select(
                    "satellite_material_families",
                    None,
                    choices=mineral_families if mineral_families else ["No data loaded"],
                    selected=[],
                    multiple=True,
                    size="6"
                ),
                ui.help_text("Type to search, then select materials", style="font-size: 0.85em; color: #666;")
            ),
            
            # Column 3: Individual Sample Selection
            ui.div(
                ui.h5("Individual Samples"),
                ui.input_select(
                    "satellite_individual_material",
                    None,
                    choices=[],
                    selected=None,
                    multiple=True,
                    size="8"
                ),
                ui.help_text("Select specific samples for plotting", style="font-size: 0.85em; color: #666;")
            ),
            
            # Column 4: Display Options
            ui.div(
                ui.h5("Display Options"),
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
            ui.h4("Selected Satellite Material Data", style="margin-top: 0;"),
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