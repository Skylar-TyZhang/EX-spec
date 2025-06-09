from shiny import ui 

def get_header():
    """Enhanced header with description of both data types"""
    return ui.div(
        {"class": "card"},
        ui.h1("USGS Spectral Library Visualisation Tool", 
              style="color: #1976d2; text-align: center; margin-bottom: 10px;"),
        ui.div(
            {"style": "text-align: center; color: #666;"},
            ui.p("Interactive tool for exploring satellite sensor and full spectrum mineral data", 
                 style="margin: 5px 0;"),
            ui.p("• Satellite Resampled: Band-specific data for ASTER, Landsat8, Sentinel2, WorldView3", 
                 style="margin: 2px 0; font-size: 0.9em;"),
            ui.p("• Full Spectrum: High-resolution spectrometer data (BECK, ASD, NIC4, AVIRIS)", 
                 style="margin: 2px 0; font-size: 0.9em;")
        )
    )