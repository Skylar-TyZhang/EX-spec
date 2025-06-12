from shiny import ui


def get_usage_info():
    """Usage information tab for the application"""
    return ui.nav_panel(
        "About",
        
        ui.markdown(
            """
    
            An interactive web application for exploring and visualising mineral spectral data from the USGS Spectral Library. This tool provides access to both satellite-resampled and full spectrum data with filtering and visualisation capabilities.
    
            ## Usage Instructions

            ### Using the Interface

            #### Satellite Resampled Spectra Tab

            1. **Select Satellite Sensor**: Choose from ASTER, Landsat8, Sentinel2, or WorldView3
            2. **Choose Mineral Families**: Select one or more mineral families from the dropdown (if you are using PC, press Ctrl to select multiple)
            3. **Refine Selection**: Optionally select specific individual samples
            4. **Adjust Display Options**: Toggle band centers, ranges, and response functions
            5. **View Results**: Explore the spectral plots and band information

            #### Full Spectrum Data Tab

            1. **Choose Spectrometer**: Select from available spectrometers (BECK, ASD variants, etc.)
            2. **Select Mineral Families**: Choose multiple families for comparison (if you are using PC, press Ctrl to select multiple)
            3. **Set Wavelength Range**: Use the slider to focus on specific wavelength regions
            4. **Analyse Data**: View high-resolution spectral data and export results

            ### Key Controls

            | Control | Description |
            |---------|-------------|
            | **Mineral Families** | Multi-select dropdown for choosing mineral types |
            | **Individual Samples** | Refined selection of specific samples |
            | **Max Samples per Family** | Limit the number of samples displayed per family |
            | **Wavelength Range** | Filter full spectrum data by wavelength (μm) |
            | **Band Options** | Toggle display of band centers, ranges, and response functions |
    
    """
        ),
    )
