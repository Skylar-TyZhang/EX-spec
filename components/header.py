from shiny import ui 
def get_header():
    return ui.div(
            {"class": "card"},
            ui.h1("USGS Spectral Library Visualisation Tool", 
                  style="color: #1976d2; text-align: center; margin-bottom: 10px;"),
            ui.p("Interactive tool for exploring satellite sensor spectral data", 
                 style="text-align: center; color: #666; margin: 0;")
        )