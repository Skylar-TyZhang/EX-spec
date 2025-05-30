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

# Improt the custom components
from components.band_info_tab import get_band_info_tab
from components.spectra_data import get_spectral_data_tab
from components.ui_tags_setup import ui_tags
from components.header import get_header
from components.control_panel import get_satellite_selection, get_mineral_family_selection, get_individual_mineral_selection, get_display_options

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

# Define the UI with card-based design
app_ui = ui.page_fluid(
    ui_tags(),
    ui.div(
        {"class": "main-container"},
        
        # Header
        get_header(),
        
        # Control Panel
        ui.div(
            {"class": "card control-card"},
            ui.h3("Control Panel", style="margin-top: 0;"),
            # change the layout if necessary
            ui.layout_columns(
                # Satellite Selection
                get_satellite_selection(SATELLITE),
                
                # Mineral Family Selection
                get_mineral_family_selection(mineral_families),
                
                # Individual Mineral Selection
                get_individual_mineral_selection(),
                
                # Display options
                get_display_options(),
                
                col_widths=[3, 3, 3, 3]
            ),
            
            # Status Info
            ui.output_ui("status_info")
        ),
        
        # Main Content Tabs
        ui.navset_tab(            
            # Spectral Data Tab
            get_spectral_data_tab(),
            # Band Information Tab
            get_band_info_tab(),
        ),
        
        # Download Status
        ui.div(
            {"class": "card"},
            ui.h5("Download Status"),
            ui.output_text("download_status")
        )
    )
)

# Define server logic
def server(input, output, session):
    # Reactive values
    current_lib = reactive.Value(lib)
    current_plot = reactive.Value(None)
    current_band_plot = reactive.Value(None)
    download_message = reactive.Value("")
    
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
            selected=choices[:min(5, len(choices))] if choices else []
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
                ui.p("⚠️ No spectral library loaded. Please check the data path and try loading data.", 
                     style="color: #dc3545; margin: 0;")
            )
        
        lib_obj = current_lib()
        num_spectra = len(lib_obj.spectra)
        num_bands = len(lib_obj.bands) if lib_obj.bands else 0
        
        return ui.div(
            {"class": "status-text"},
            ui.p(f"📡 {input.satellite()} | 📊 {num_spectra} spectra | 🎛️ {num_bands} bands | 🔬 {input.mineral_family() or 'None'} | 📈 {len(get_filtered_minerals())} samples",
                 style="margin: 5px 0;")
        )
    
    # Auto-update plots when selections change
    @reactive.Effect
    @reactive.event(input.mineral_family, input.individual_mineral, input.show_band_centers, 
                   input.show_band_ranges, input.show_response_functions)
    def auto_update_plots():
        """Automatically update plots when selections change"""
        # Trigger plot updates by updating reactive values
        pass
    
    @output
    @render.plot
    def main_plot():
        """Generate the main spectral plot - auto-updates"""
        if not current_lib() or not input.mineral_family():
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.text(0.5, 0.5, 'Select a mineral family to view spectral data',
                   ha='center', va='center', transform=ax.transAxes, fontsize=14, color='#666')
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
            return fig
        
        try:
            lib_obj = current_lib()
            
            # Use individual selection if available, otherwise use family
            if input.individual_mineral():
                fig = lib_obj.compare_spectra_with_bands(
                    input.individual_mineral(),
                    figsize=(12, 6),
                    title=f"{input.satellite()} - Selected Minerals {len(input.individual_mineral())}",
                    show_response_functions=input.show_response_functions(),
                    show_band_centers=input.show_band_centers(),
                    show_band_ranges=input.show_band_ranges()
                )
            else:
                fig = lib_obj.plot_spectrum_with_bands(
                    input.mineral_family(),
                    figsize=(12, 6),
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
            ax.axis('off')
            return fig
    
    @output
    @render.plot
    def band_plot():
        """Generate band response function plot - auto-updates"""
        if not current_lib():
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.text(0.5, 0.5, 'No band data available',
                   ha='center', va='center', transform=ax.transAxes, fontsize=14, color='#666')
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
            return fig
        
        try:
            lib_obj = current_lib()
            fig = lib_obj.plot_band_responses_detailed(figsize=(12, 6))
            current_band_plot.set(fig)
            return fig if fig else plt.figure(figsize=(12, 6))
            
        except Exception as e:
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.text(0.5, 0.5, f'Error generating band plot:\n{str(e)}',
                   ha='center', va='center', transform=ax.transAxes, fontsize=12, color='red')
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
            return fig
    
    @output
    @render.data_frame
    def band_info_table():
        """Display band information table"""
        if not current_lib():
            return pd.DataFrame({"Status": ["No data loaded"]})
        
        try:
            lib_obj = current_lib()
            band_info = lib_obj.get_band_info()
            
            if band_info is not None and not band_info.empty:
                numerical_cols = band_info.select_dtypes(include=[np.number]).columns
                band_info[numerical_cols] = band_info[numerical_cols].round(4)
                return band_info
            else:
                return pd.DataFrame({"Status": ["No band information available"]})
                
        except Exception as e:
            return pd.DataFrame({"Error": [f"Error loading band info: {str(e)}"]})
    
    @output
    @render.data_frame
    def selected_mineral_table():
        """Display data for selected minerals"""
        if not current_lib() or not input.mineral_family():
            return pd.DataFrame({"Status": ["Select a mineral family to view data"]})
        
        try:
            lib_obj = current_lib()
            
            # Get selected minerals or use family
            if input.individual_mineral():
                selected_keys = input.individual_mineral()
            else:
                selected_keys = get_filtered_minerals()
            
            if not selected_keys:
                return pd.DataFrame({"Status": ["No minerals selected"]})
            
            # Create summary table
            table_data = []
            for key in selected_keys:
                if key in lib_obj.spectra:
                    metadata = lib_obj.spectra[key]['metadata']
                    spectrum = lib_obj.spectra[key]['spectrum']
                    
                    table_data.append({
                        'Sample_Key': key,
                        'Material': metadata['material'],
                        #'Sample_ID': metadata['sample_id'],
                        'Spectrometer': metadata['spectrometer'],
                        'Purity': metadata['purity'],
                        'Measurement_Type': metadata['measurement_type'],
                        'Mean_Reflectance': np.nanmean(spectrum),
                        'Std_Reflectance': np.nanstd(spectrum),
                        'Min_Reflectance': np.nanmin(spectrum),
                        'Max_Reflectance': np.nanmax(spectrum)
                    })
            
            df = pd.DataFrame(table_data)
            if not df.empty:
                numerical_cols = df.select_dtypes(include=[np.number]).columns
                df[numerical_cols] = df[numerical_cols].round(4)
            
            return df
        except Exception as e:
            return pd.DataFrame({"Error": [f"Error creating table: {str(e)}"]})
    
    # Download handlers
    @reactive.Effect
    @reactive.event(input.download_band_table)
    def download_band_table():
        """Download band information table"""
        if not current_lib():
            download_message.set("No data available for download")
            return
        
        try:
            lib_obj = current_lib()
            band_info = lib_obj.get_band_info()
            
            if band_info is not None and not band_info.empty:
                filename = f"band_info_{input.satellite()}.csv"
                band_info.to_csv(filename, index=False)
                download_message.set(f"✅ Band information downloaded as {filename}")
            else:
                download_message.set("❌ No band information available")
                
        except Exception as e:
            download_message.set(f"❌ Error downloading band table: {str(e)}")
    
    @reactive.Effect
    @reactive.event(input.download_band_plot)
    def download_band_plot():
        """Download band plot"""
        if not current_band_plot():
            download_message.set("No band plot available for download")
            return
        
        try:
            fig = current_band_plot()
            filename = f"band_plot_{input.satellite()}.png"
            fig.savefig(filename, dpi=300, bbox_inches='tight')
            download_message.set(f"✅ Band plot saved as {filename}")
            
        except Exception as e:
            download_message.set(f"❌ Error saving band plot: {str(e)}")
    
    @reactive.Effect
    @reactive.event(input.download_spectra_table)
    def download_spectra_table():
        """Download selected mineral data"""
        if not current_lib() or not input.mineral_family():
            download_message.set("No spectral data available for download")
            return
        
        try:
            lib_obj = current_lib()
            
            # Get selected minerals
            if input.individual_mineral():
                selected_keys = input.individual_mineral()
            else:
                selected_keys = get_filtered_minerals()
            
            if not selected_keys:
                download_message.set("No minerals selected")
                return
            
            # Create detailed export data
            export_data = []
            for key in selected_keys:
                if key in lib_obj.spectra:
                    spectrum = lib_obj.spectra[key]['spectrum']
                    metadata = lib_obj.spectra[key]['metadata']
                    
                    for i, (wl, refl) in enumerate(zip(lib_obj.wavelengths, spectrum)):
                        export_data.append({
                            'Sample_Key': key,
                            'Material': metadata['material'],
                            'Sample_ID': metadata['sample_id'],
                            'Spectrometer': metadata['spectrometer'],
                            'Purity': metadata['purity'],
                            'Measurement_Type': metadata['measurement_type'],
                            'Wavelength_um': wl,
                            'Band_Number': i + 1,
                            'Reflectance_Value': refl
                        })
            
            df = pd.DataFrame(export_data)
            filename = f"spectral_data_{input.satellite()}_{input.mineral_family()}.csv"
            df.to_csv(filename, index=False)
            
            download_message.set(f"✅ Spectral data exported as {filename} ({len(df)} records)")
            
        except Exception as e:
            download_message.set(f"❌ Error exporting spectral data: {str(e)}")
    
    @reactive.Effect
    @reactive.event(input.download_spectra_plot)
    def download_spectra_plot():
        """Download spectral plot"""
        if not current_plot():
            download_message.set("No spectral plot available for download")
            return
        
        try:
            fig = current_plot()
            filename = f"spectral_plot_{input.satellite()}_{input.mineral_family()}.png"
            fig.savefig(filename, dpi=300, bbox_inches='tight')
            download_message.set(f"✅ Spectral plot saved as {filename}")
            
        except Exception as e:
            download_message.set(f"❌ Error saving spectral plot: {str(e)}")
    
    @output
    @render.text
    def download_status():
        """Display download status"""
        return download_message.get()

# Create the Shiny app
app = App(app_ui, server)

if __name__ == "__main__":
    app.run()