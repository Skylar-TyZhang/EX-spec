from shiny import ui

def get_full_spectrum_tab(mineral_families, default_collection, default_spectrometer):
    """Return the full spectrum data tab component"""
    return ui.nav_panel(
        "Full Spectrum Data",
        ui.div(
            {"class": "tab-content"},
            
            # Control Panel for Full Spectrum Data
            _get_full_spectrum_control_panel(mineral_families, default_collection, default_spectrometer),
            
            # Main Content
            ui.div(
                {"class": "tab-content"},
                _get_full_spectrum_plot_card(),
                _get_full_spectrum_data_table_card()
            )
        )
    )

def _get_full_spectrum_control_panel(mineral_families, default_collection, default_spectrometer):
    """Full spectrum control panel component"""
    return ui.div(
        {"class": "card control-card"},
        ui.h3("Full Spectrum Control Panel", style="margin-top: 0;"),
        
        ui.layout_columns(
            # Collection and Spectrometer Selection
            ui.div(
                #ui.h5("Data Collection"),
                #ui.input_select(
                #    "collection",
                #    "Collection:",
                #    choices=["a", "b"],
                #    selected=default_collection
                #),
                ui.input_select(
                    "spectrometer",
                    "Spectrometer:",
                    choices=[
                        "BECK",    # Beckman 5270 (0.2-3.0 μm)
                        "ASDFR",   # Standard resolution ASD (0.35-2.5 μm)
                        "ASDHR",   # High resolution ASD (0.35-2.5 μm)
                        "ASDNG",   # High resolution next gen ASD (0.35-2.5 μm)
                        "NIC4",    # Nicolet FTIR (1.12-216 μm)
                        "AVIRIS"   # NASA AVIRIS (0.37-2.5 μm)
                    ],
                    selected=default_spectrometer
                )
            ),
            
            # Mineral Family Selection (Multiple)
            ui.div(
                ui.h5("Mineral Families"),
                ui.input_select(
                    "full_spectrum_mineral_families",
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
                    "full_spectrum_individual_minerals",
                    None,
                    choices=[],
                    selected=None,
                    multiple=True,
                    size="5"
                )
            ),
            
            # Display Options and Wavelength Range
            ui.div(
                ui.h5("Display Options"),
                ui.input_slider(
                    "full_spectrum_max_samples",
                    "Max Samples per Family:",
                    min=1, max=20, value=5, step=1
                ),
                ui.h6("Wavelength Range (μm)", style="margin-top: 15px;"),
                ui.input_slider(
                    "wavelength_range",
                    None,
                    min=0.2, max=25.0, value=[0.4, 2.5], step=0.1
                )
            ),
            
            col_widths=[3, 3, 3, 3]
        ),
        
        # Status Info
        ui.output_ui("full_spectrum_status_info")
    )

def _get_full_spectrum_plot_card():
    """Full spectrum visualisation plot card"""
    return ui.div(
        {"class": "card plot-card"},
        ui.output_ui("full_spectrum_main_plot", height="700px")
    )

def _get_full_spectrum_data_table_card():
    """Full spectrum selected mineral data table card"""
    return ui.div(
        {"class": "card"},        
        ui.div(
            ui.h4("Selected Full Spectrum Mineral Data", style="margin-top: 0;"),
            ui.div(
                ui.input_action_button("download_full_spectrum_table", "Download Data", 
                                     class_="btn-success download-btn btn-sm"),
                style="float: right;"
            ),
            style="overflow: auto;"
        ),
        ui.output_data_frame("full_spectrum_selected_mineral_table")
    )