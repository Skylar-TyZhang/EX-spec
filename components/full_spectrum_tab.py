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
            # Column 1: Spectrometer & Chapter Selection
            ui.div(
                ui.h5("Spectrometer"),
                ui.input_select(
                    "spectrometer",
                    None,
                    choices=[
                        "All",
                        "BECK",
                        "ASDFR",
                        "ASDHR",
                        "ASDNG",
                        "NIC4",
                        "AVIRIS"
                    ],
                    selected="All"
                ),
                ui.h5("Data Chapters", style="margin-top: 15px;"),
                ui.input_checkbox_group(
                    "full_spectrum_chapters",
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
            
            # Column 2: Material Search & Selection
            ui.div(
                ui.h5("Material Families"),
                ui.input_text(
                    "material_search",
                    None,
                    placeholder="Search materials...",
                    value=""
                ),
                ui.input_select(
                    "full_spectrum_material_families",
                    None,
                    choices=mineral_families if mineral_families else ["Loading..."],
                    selected=[],
                    multiple=True,
                    size="6"
                ),
                ui.help_text("Type to search, then select materials", style="font-size: 0.85em; color: #666;")
            ),
            
            # Column 3: Wavelength Range & Coverage
            ui.div(
                ui.h5("Wavelength Range"),
                ui.input_slider(
                    "wavelength_range",
                    "Range (μm):",
                    min=0.2, max=25.0, value=[0.4, 2.5], step=0.1
                ),
                ui.input_numeric(
                    "min_wavelength_coverage",
                    "Min Coverage (%):",
                    value=50,
                    min=0,
                    max=100,
                    step=10
                ),
                ui.help_text("Only show spectra with sufficient wavelength coverage", style="font-size: 0.85em; color: #666;"),
                ui.h6("Display Options", style="margin-top: 15px;"),
                ui.input_checkbox("full_spectrum_show_atmospheric_transmission", "Atmospheric Transmission", value=False)
            ),
            
            # Column 4: Individual Sample Selection
            ui.div(
                ui.h5("Individual Samples"),
                ui.input_select(
                    "full_spectrum_individual_material",
                    None,
                    choices=[],
                    selected=None,
                    multiple=True,
                    size="8"
                ),
                ui.help_text("Select specific samples for plotting", style="font-size: 0.85em; color: #666;")
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
            ui.h4("Selected Full Spectrum Material Data", style="margin-top: 0;"),
            ui.p("Note: Spectrum data available in download only (too many columns to display)", 
                 style="font-size: 0.9em; color: #666; font-style: italic;"),
            ui.div(
                ui.download_button("download_full_spectrum_table", "Download Data", 
                                 class_="btn-success download-btn btn-sm"),
                style="float: right;"
            ),
            style="overflow: auto;"
        ),
        ui.output_data_frame("full_spectrum_selected_mineral_table")
    )