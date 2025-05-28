# app.py
from shiny import App, ui, render, reactive
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from pathlib import Path
import io
import base64

# Import the USGS Spectra Lib class
from spec_lib_ascii import USGSSatelliteSpectra

# Initialise the spectral library (you may want to make this configurable)
BASE_DIR = "ASCIIdata"  # Update this path
SATELLITE = "ASTER"  # Default satellite

# Global variables to store the library and data
lib = None
mineral_families = []
all_minerals = []

def Initialise_library():
    """Initialise the spectral library and extract mineral information"""
    global lib, mineral_families, all_minerals
    
    try:
        lib = USGSSatelliteSpectra(BASE_DIR, SATELLITE)
        lib.load_minerals()
        
        # Extract unique mineral families and all minerals
        all_minerals = list(lib.spectra.keys())
        
        # Extract mineral families (base mineral names)
        mineral_families = []
        for key in all_minerals:
            material = lib.spectra[key]['metadata']['material']
            if material not in mineral_families:
                mineral_families.append(material)
        
        mineral_families.sort()
        print(f"Initialised library with {len(all_minerals)} spectra and {len(mineral_families)} mineral families")
        
    except Exception as e:
        print(f"Error initialising library: {e}")
        lib = None
        mineral_families = []
        all_minerals = []

# Initialise the library when the app starts
Initialise_library()

# Define the UI
app_ui = ui.page_fluid(
    ui.tags.head(
        ui.tags.style("""
            .content-wrapper {
                padding: 20px;
            }
            .plot-container {
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 15px;
                margin: 10px 0;
                background-color: #f9f9f9;
            }
            .control-panel {
                background-color: #f5f5f5;
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 20px;
            }
            .info-box {
                background-color: #e3f2fd;
                border-left: 4px solid #2196f3;
                padding: 15px;
                margin: 10px 0;
            }
            .error-box {
                background-color: #ffebee;
                border-left: 4px solid #f44336;
                padding: 15px;
                margin: 10px 0;
            }
        """)
    ),
    
    ui.div(
        {"class": "content-wrapper"},
        
        # Header
        ui.div(
            ui.h1("USGS Spectral Library Visualisation Tool", style="color: #1976d2; text-align: center;"),
            ui.hr(),
        ),
        
        # Control Panel
        ui.div(
            {"class": "control-panel"},
            ui.h3("Control Panel"),
            
            ui.layout_sidebar(
                ui.panel_sidebar(
                    # Satellite selection
                    ui.input_select(
                        "satellite",
                        "Select Satellite Sensor:",
                        choices=["ASTER", "LSAT8", "SNTL2", "WV3"],
                        selected=SATELLITE
                    ),
                    
                    ui.br(),
                    
                    # Mineral family selection
                    ui.input_select(
                        "mineral_family",
                        "Select Mineral Family:",
                        choices=mineral_families if mineral_families else ["No data loaded"],
                        selected=mineral_families[0] if mineral_families else None
                    ),
                    
                    ui.br(),
                    
                    # Individual mineral selection (updated based on mineral family)
                    ui.input_select(
                        "individual_mineral",
                        "Select Individual Mineral Sample:",
                        choices=[],
                        selected=None,
                        multiple=True
                    ),
                    
                    ui.br(),
                    
                    # Maximum samples slider
                    ui.input_slider(
                        "max_samples",
                        "Maximum Samples to Display:",
                        min=1,
                        max=20,
                        value=5,
                        step=1
                    ),
                    
                    ui.br(),
                    
                    # Visualisation options for spectra band comparison 
                    ui.h4("Visualisation Options"),
                    ui.input_checkbox("show_band_centers", "Show Band Centers", value=True),
                    ui.input_checkbox("show_band_ranges", "Show Band Ranges", value=True),
                    ui.input_checkbox("show_response_functions", "Show Response Functions", value=True),
                    
                    width=3
                ),
                
                ui.panel_main(
                    # Action buttons
                    ui.div(
                        ui.input_action_button("load_data", "Load/Reload Data", class_="btn-primary"),
                        ui.input_action_button("plot_family", "Plot Mineral Family", class_="btn-success"),
                        ui.input_action_button("plot_individual", "Plot Selected Minerals", class_="btn-info"),
                        ui.input_action_button("plot_bands", "Show Band Details", class_="btn-warning"),
                        ui.input_action_button("export_data", "Export Data", class_="btn-secondary"),
                        style="margin-bottom: 20px;"
                    ),
                    
                    # Status/Info display
                    ui.output_ui("status_info"),
                    
                    width=9
                )
            )
        ),
        
        # Tabs for different visualisations
        ui.navset_tab(
            ui.nav_panel(
                "Spectral Plots",
                ui.div(
                    {"class": "plot-container"},
                    ui.output_plot("main_plot", height="600px")
                )
            ),
            
            ui.nav_panel(
                "Band Response Functions",
                ui.div(
                    {"class": "plot-container"},
                    ui.output_plot("band_plot", height="600px")
                )
            ),
            
            ui.nav_panel(
                "Band Information",
                ui.div(
                    {"class": "plot-container"},
                    ui.output_table("band_info_table")
                )
            ),
            
            ui.nav_panel(
                "Data Summary",
                ui.div(
                    {"class": "plot-container"},
                    ui.output_table("data_summary")
                )
            ),
            
            ui.nav_panel(
                "Export/Download",
                ui.div(
                    {"class": "plot-container"},
                    ui.h4("Export Options"),
                    ui.input_action_button("download_csv", "Download Data as CSV", class_="btn-primary"),
                    ui.br(), ui.br(),
                    ui.input_action_button("download_plots", "Download Current Plot", class_="btn-success"),
                    ui.br(), ui.br(),
                    ui.output_text("export_status")
                )
            )
        )
    )
)

# Define server logic
def server(input, output, session):
    # Reactive values
    current_lib = reactive.Value(lib)
    #current_data = reactive.Value({})
    current_plot = reactive.Value(None)
    
    @reactive.Calc
    def get_filtered_minerals():
        """Get minerals that match the selected family"""
        if not current_lib() or not input.mineral_family():
            return []
        
        filtered = [key for key in current_lib().spectra.keys() 
                   if input.mineral_family() in key]
        return filtered[:input.max_samples()]
    
    @reactive.Effect
    def update_individual_mineral_choices():
        """Update individual mineral choices based on selected family"""
        choices = get_filtered_minerals()
        ui.update_select(
            "individual_mineral",
            choices=choices,
            selected=choices[:min(3, len(choices))] if choices else []
        )
    
    @reactive.Effect
    @reactive.event(input.load_data)
    def load_satellite_data():
        """Load data for the selected satellite"""
        try:
            new_lib = USGSSatelliteSpectra(BASE_DIR, input.satellite())
            new_lib.load_minerals()
            current_lib.set(new_lib)
            
            # Update mineral family choices
            new_families = []
            for key in new_lib.spectra.keys():
                material = new_lib.spectra[key]['metadata']['material']
                if material not in new_families:
                    new_families.append(material)
            
            new_families.sort()
            ui.update_select("mineral_family", choices=new_families, selected=new_families[0] if new_families else None)
            
        except Exception as e:
            print(f"Error loading satellite data: {e}")
    
    @output
    @render.ui
    def status_info():
        """Display current status and library information"""
        if not current_lib():
            return ui.div(
                {"class": "error-box"},
                ui.h4("Error"),
                ui.p("No spectral library loaded. Please check the data path and try loading data.")
            )
        
        lib_obj = current_lib()
        num_spectra = len(lib_obj.spectra)
        num_bands = len(lib_obj.bands) if lib_obj.bands else 0
        
        return ui.div(
            {"class": "info-box"},
            ui.h4(f"Current Satellite: {input.satellite()}"),
            ui.p(f"Total Spectra Loaded: {num_spectra}"),
            ui.p(f"Number of Bands: {num_bands}"),
            ui.p(f"Selected Mineral Family: {input.mineral_family() or 'None'}"),
            ui.p(f"Available Samples: {len(get_filtered_minerals())}")
        )
    
    @output
    @render.plot
    @reactive.event(input.plot_family)
    def main_plot():
        """Generate the main spectral plot"""
        if not current_lib() or not input.mineral_family():
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.text(0.5, 0.5, 'No data to display.\nSelect a mineral family and click "Plot Mineral Family"',
                   ha='center', va='center', transform=ax.transAxes, fontsize=14)
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            return fig
        
        try:
            lib_obj = current_lib()
            
            # Create the plot based on user selections
            fig = lib_obj.plot_spectrum_with_bands(
                input.mineral_family(),
                figsize=(14, 8),
                show_response_functions=input.show_response_functions(),
                show_band_centers=input.show_band_centers(),
                show_band_ranges=input.show_band_ranges()
            )
            
            current_plot.set(fig)
            return fig
            
        except Exception as e:
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.text(0.5, 0.5, f'Error generating plot:\n{str(e)}',
                   ha='center', va='center', transform=ax.transAxes, fontsize=12, color='red')
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            return fig
    
    @output
    @render.plot
    @reactive.event(input.plot_individual)
    def individual_plot():
        """Plot selected individual minerals"""
        if not current_lib() or not input.individual_mineral():
            return main_plot()
        
        try:
            lib_obj = current_lib()
            selected_minerals = input.individual_mineral()
            
            fig = lib_obj.compare_spectra(
                selected_minerals,
                figsize=(12, 8),
                title=f"{input.satellite()} - Selected Minerals Comparison"
            )
            
            return fig
            
        except Exception as e:
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.text(0.5, 0.5, f'Error generating individual plot:\n{str(e)}',
                   ha='center', va='center', transform=ax.transAxes, fontsize=12, color='red')
            return fig
    
    @output
    @render.plot
    @reactive.event(input.plot_bands)
    def band_plot():
        """Generate band response function plot"""
        if not current_lib():
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.text(0.5, 0.5, 'No band data available',
                   ha='center', va='center', transform=ax.transAxes, fontsize=14)
            return fig
        
        try:
            lib_obj = current_lib()
            fig = lib_obj.plot_band_responses_detailed(figsize=(12, 8))
            return fig if fig else plt.figure(figsize=(12, 6))
            
        except Exception as e:
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.text(0.5, 0.5, f'Error generating band plot:\n{str(e)}',
                   ha='center', va='center', transform=ax.transAxes, fontsize=12, color='red')
            return fig
    
    @output
    @render.table
    def band_info_table():
        """Display band information table"""
        if not current_lib():
            return pd.DataFrame({"Message": ["No data loaded"]})
        
        try:
            lib_obj = current_lib()
            band_info = lib_obj.get_band_info()
            
            if band_info is not None and not band_info.empty:
                # Round numerical columns for better display
                numerical_cols = band_info.select_dtypes(include=[np.number]).columns
                band_info[numerical_cols] = band_info[numerical_cols].round(4)
                return band_info
            else:
                return pd.DataFrame({"Message": ["No band information available"]})
                
        except Exception as e:
            return pd.DataFrame({"Error": [f"Error loading band info: {str(e)}"]})
    
    @output
    @render.table
    def data_summary():
        """Display data summary table"""
        if not current_lib():
            return pd.DataFrame({"Message": ["No data loaded"]})
        
        try:
            lib_obj = current_lib()
            
            # Create summary statistics
            summary_data = []
            mineral_counts = {}
            
            for key, data in lib_obj.spectra.items():
                material = data['metadata']['material']
                mineral_counts[material] = mineral_counts.get(material, 0) + 1
            
            for material, count in sorted(mineral_counts.items()):
                summary_data.append({
                    'Mineral': material,
                    'Number_of_Samples': count,
                    'Satellite': input.satellite()
                })
            
            return pd.DataFrame(summary_data)
            
        except Exception as e:
            return pd.DataFrame({"Error": [f"Error creating summary: {str(e)}"]})
    
    @output
    @render.text
    @reactive.event(input.download_csv)
    def download_csv_handler():
        """Handle CSV download"""
        if not current_lib():
            return "No data available for download"
        
        try:
            lib_obj = current_lib()
            
            # Create a comprehensive dataset
            export_data = []
            
            for key, data in lib_obj.spectra.items():
                spectrum = data['spectrum']
                metadata = data['metadata']
                
                base_record = {
                    'Sample_Key': key,
                    'Material': metadata['material'],
                    'Sample_ID': metadata['sample_id'],
                    'Spectrometer': metadata['spectrometer'],
                    'Purity': metadata['purity'],
                    'Measurement_Type': metadata['measurement_type'],
                    'Satellite': metadata['satellite']
                }
                
                # Add spectral values
                for i, (wl, refl) in enumerate(zip(lib_obj.wavelengths, spectrum)):
                    record = base_record.copy()
                    record.update({
                        'Wavelength_um': wl,
                        'Band_Number': i + 1,
                        'Reflectance_Value': refl
                    })
                    export_data.append(record)
            
            df = pd.DataFrame(export_data)
            
            # Save to CSV (in a real app, you'd want to use a proper download mechanism)
            filename = f"usgs_spectral_data_{input.satellite()}.csv"
            df.to_csv(filename, index=False)
            
            return f"Data exported to {filename} ({len(df)} records)"
            
        except Exception as e:
            return f"Error exporting data: {str(e)}"
    
    @output
    @render.text
    @reactive.event(input.download_plots)
    def download_plots_handler():
        """Handle plot download"""
        if not current_plot():
            return "No plot available for download"
        
        try:
            fig = current_plot()
            filename = f"usgs_spectral_plot_{input.satellite()}_{input.mineral_family()}.png"
            fig.savefig(filename, dpi=300, bbox_inches='tight')
            
            return f"Plot saved as {filename}"
            
        except Exception as e:
            return f"Error saving plot: {str(e)}"

# Create the Shiny app
app = App(app_ui, server)

if __name__ == "__main__":
    app.run()