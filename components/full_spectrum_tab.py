from shiny import ui

def get_full_spectrum_tab(mineral_families, default_collection):
    """Return the full spectrum data tab component"""
    return ui.nav_panel(
        "Full Spectrum Data",
        ui.div(
            {"class": "tab-content"},
            
            # Control Panel for Full Spectrum Data
            _get_full_spectrum_control_panel(mineral_families, default_collection),
            
            # Main Content
            ui.div(
                {"class": "tab-content"},
                _get_full_spectrum_plot_card(),
                _get_full_spectrum_data_table_card()
            )
        )
    )

def _get_full_spectrum_control_panel(mineral_families, default_collection):
    """Full spectrum control panel component"""
    return ui.div(
        {"class": "card control-card"},
        ui.h3("Full Spectrum Control Panel", style="margin-top: 0;"),
        
        ui.layout_columns(
            # Search and Material Selection
            ui.div(
                ui.h5("Search & Selection"),
                ui.input_text(
                    "material_search",
                    "Search Materials:",
                    placeholder="Type to search materials...",
                    value=""
                ),
                ui.input_select(
                    "full_spectrum_mineral_families",
                    "Mineral Families:",
                    choices=mineral_families if mineral_families else ["Loading..."],
                    selected=mineral_families[:min(3, len(mineral_families))] if mineral_families else None,
                    multiple=True,
                    size="4"
                )
            ),
            
            # Wavelength Range Control
            ui.div(
                ui.h5("Wavelength Range"),
                ui.input_slider(
                    "wavelength_range",
                    "Range (μm):",
                    min=0.2, max=25.0, value=[0.4, 2.5], step=0.1
                ),
                ui.help_text(
                    "Drag the slider to focus on specific wavelength regions"
                ),
                ui.h6("Display Options", style="margin-top: 15px;"),
                ui.input_checkbox("full_spectrum_show_atmospheric_transmission", "Show Atmospheric Transmission", value=False),
                ui.input_slider(
                    "full_spectrum_max_samples",
                    "Max Samples per Family:",
                    min=1, max=20, value=5, step=1
                )
            ),
            
            # Individual Sample Selection
            ui.div(
                ui.h5("Individual Samples"),
                ui.input_select(
                    "full_spectrum_individual_minerals",
                    "Specific Samples:",
                    choices=[],
                    selected=None,
                    multiple=True,
                    size="5"
                ),
                ui.help_text(
                    "Select specific samples for detailed analysis"
                )
            ),
            
            # Filters (Spectrometer moved here)
            ui.div(
                ui.h5("Filters"),
                ui.input_select(
                    "spectrometer",
                    "Spectrometer:",
                    choices=[
                        "All",       # New option for all spectrometers
                        "BECK",      # Beckman 5270 (0.2-3.0 μm)
                        "ASDFR",     # Standard resolution ASD (0.35-2.5 μm)
                        "ASDHR",     # High resolution ASD (0.35-2.5 μm)
                        "ASDNG",     # High resolution next gen ASD (0.35-2.5 μm)
                        "NIC4",      # Nicolet FTIR (1.12-216 μm)
                        "AVIRIS"     # NASA AVIRIS (0.37-2.5 μm)
                    ],
                    selected="All"
                ),
                ui.help_text(
                    ui.HTML("""
                    <div style="font-size: 10px; color: #666; line-height: 1.2;">
                    <strong>BECK:</strong> Beckman 5270 (0.2-3.0 μm)<br>
                    <strong>ASDFR:</strong> ASD FieldSpec Standard Resolution (0.35-2.5 μm)<br>
                    <strong>ASDHR:</strong> ASD FieldSpec High Resolution (0.35-2.5 μm)<br>
                    <strong>ASDNG:</strong> ASD FieldSpec Next Generation (0.35-2.5 μm)<br>
                    <strong>NIC4:</strong> Nicolet FTIR (1.12-216 μm)<br>
                    <strong>AVIRIS:</strong> NASA AVIRIS Imaging Spectrometer (0.37-2.5 μm)
                    </div>
                    """)
                ),
                ui.input_numeric(
                    "min_wavelength_coverage",
                    "Min Wavelength Coverage (%):",
                    value=50,
                    min=0,
                    max=100,
                    step=10
                ),
                ui.help_text(
                    "Only show spectra with at least this % coverage of the selected wavelength range"
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
                ui.download_button("download_full_spectrum_table", "Download Data", 
                                 class_="btn-success download-btn btn-sm"),
                style="float: right;"
            ),
            style="overflow: auto;"
        ),
        ui.output_data_frame("full_spectrum_selected_mineral_table")
    )