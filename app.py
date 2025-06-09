# app.py
from shiny import App, ui, render, reactive
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from pathlib import Path
import io
import base64

# Import the USGS Spectra classes
from USGSSatelliteSpectra import USGSSatelliteSpectra
from USGSSpectra import USGSSpectra

# Import the custom components
from components.satellite_tab import get_satellite_tab
from components.full_spectrum_tab import get_full_spectrum_tab
from components.ui_tags_setup import ui_tags
from components.header import get_header

# Configuration
BASE_DIR = "E:/OneDrive - SRK Consulting/Projects/R&D/Spectral Data for minerals/usgs_splib07/ASCIIdata"
DEFAULT_SATELLITE = "ASTER"
DEFAULT_COLLECTION = "b"
DEFAULT_SPECTROMETER = "BECK"

# Global variables to store libraries and data
satellite_lib = None
full_spectrum_lib = None
satellite_mineral_families = []
full_spectrum_mineral_families = []
all_satellite_minerals = []
all_full_spectrum_minerals = []

def initialise_libraries():
    """initialise both spectral libraries"""
    global satellite_lib, full_spectrum_lib
    global satellite_mineral_families, full_spectrum_mineral_families
    global all_satellite_minerals, all_full_spectrum_minerals
    
    try:
        # initialise satellite library
        satellite_lib = USGSSatelliteSpectra(BASE_DIR, DEFAULT_SATELLITE)
        
        # Extract satellite mineral information
        all_satellite_minerals = list(satellite_lib.spectra.keys())
        satellite_mineral_families = []
        for key in all_satellite_minerals:
            material = satellite_lib.spectra[key]['metadata']['material']
            if material not in satellite_mineral_families:
                satellite_mineral_families.append(material)
        satellite_mineral_families.sort()
        
        # initialise full spectrum library
        full_spectrum_lib = USGSSpectra(BASE_DIR, DEFAULT_COLLECTION, DEFAULT_SPECTROMETER)
        
        # Extract full spectrum mineral information
        all_full_spectrum_minerals = list(full_spectrum_lib.spectra.keys())
        full_spectrum_mineral_families = []
        for key in all_full_spectrum_minerals:
            material = full_spectrum_lib.spectra[key]['metadata']['material']
            if material not in full_spectrum_mineral_families:
                full_spectrum_mineral_families.append(material)
        full_spectrum_mineral_families.sort()
        
        print(f"Satellite library: {len(all_satellite_minerals)} spectra, {len(satellite_mineral_families)} families")
        print(f"Full spectrum library: {len(all_full_spectrum_minerals)} spectra, {len(full_spectrum_mineral_families)} families")
        
    except Exception as e:
        print(f"Error initialising libraries: {e}")

# initialise libraries when the app starts
initialise_libraries()

# Define the UI
app_ui = ui.page_fluid(
    ui_tags(),
    ui.div(
        {"class": "main-container"},
        
        # Header
        get_header(),
        
        # Main Content Tabs
        ui.navset_tab(
            # Satellite Resampled Data Tab
            get_satellite_tab(satellite_mineral_families, DEFAULT_SATELLITE),
            
            # Full Spectrum Data Tab
            get_full_spectrum_tab(full_spectrum_mineral_families, DEFAULT_COLLECTION, DEFAULT_SPECTROMETER),
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
    current_satellite_lib = reactive.Value(satellite_lib)
    current_full_spectrum_lib = reactive.Value(full_spectrum_lib)
    current_satellite_plot = reactive.Value(None)
    current_full_spectrum_plot = reactive.Value(None)
    current_band_plot = reactive.Value(None)
    download_message = reactive.Value("")
    
    # === SATELLITE TAB LOGIC ===
    @reactive.Calc
    def get_filtered_satellite_minerals():
        """Get satellite minerals that match the selected families"""
        if not current_satellite_lib() or not input.satellite_mineral_families():
            return []
        
        filtered = []
        for family in input.satellite_mineral_families():
            family_minerals = [key for key in current_satellite_lib().spectra.keys() 
                             if family in key]
            filtered.extend(family_minerals[:input.satellite_max_samples()])
        return filtered
    
    @reactive.Effect
    def update_satellite_individual_choices():
        """Update individual satellite mineral choices based on selected families"""
        choices = get_filtered_satellite_minerals()
        ui.update_select(
            "satellite_individual_minerals",
            choices=choices,
            selected=choices[:min(5, len(choices))] if choices else []
        )
    
    @reactive.Effect
    def load_satellite_data():
        """Load data for the selected satellite"""
        try:
            new_lib = USGSSatelliteSpectra(BASE_DIR, input.satellite())
            #new_lib.load_minerals_pickle()
            current_satellite_lib.set(new_lib)
            
            # Update mineral family choices
            new_families = []
            for key in new_lib.spectra.keys():
                material = new_lib.spectra[key]['metadata']['material']
                if material not in new_families:
                    new_families.append(material)
            
            new_families.sort()
            ui.update_select("satellite_mineral_families", choices=new_families)
            
        except Exception as e:
            print(f"Error loading satellite data: {e}")
    
    @output
    @render.ui
    def satellite_status_info():
        """Display current satellite status"""
        if not current_satellite_lib():
            return ui.div(
                ui.p("⚠️ No satellite library loaded.", style="color: #dc3545; margin: 0;")
            )
        
        lib_obj = current_satellite_lib()
        num_spectra = len(lib_obj.spectra)
        num_bands = len(lib_obj.bands) if lib_obj.bands else 0
        num_families = len(input.satellite_mineral_families()) if input.satellite_mineral_families() else 0
        num_samples = len(get_filtered_satellite_minerals())
        
        return ui.div(
            {"class": "status-text"},
            ui.p(f"📡 {input.satellite()} | 📊 {num_spectra} spectra | 🎛️ {num_bands} bands | 🔬 {num_families} families | 📈 {num_samples} samples",
                 style="margin: 5px 0;")
        )
    
    @output
    @render.plot
    def satellite_main_plot():
        """Generate the satellite spectral plot"""
        if not current_satellite_lib() or not input.satellite_mineral_families():
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.text(0.5, 0.5, 'Select mineral families to view satellite spectral data',
                   ha='center', va='center', transform=ax.transAxes, fontsize=14, color='#666')
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
            return fig
        
        try:
            lib_obj = current_satellite_lib()
            
            # Use individual selection if available, otherwise use families
            if input.satellite_individual_minerals():
                selected_minerals = input.satellite_individual_minerals()
            else:
                selected_minerals = get_filtered_satellite_minerals()
            
            if not selected_minerals:
                fig, ax = plt.subplots(figsize=(12, 6))
                ax.text(0.5, 0.5, 'No minerals selected',
                       ha='center', va='center', transform=ax.transAxes, fontsize=14, color='#666')
                ax.set_xlim(0, 1)
                ax.set_ylim(0, 1)
                ax.axis('off')
                return fig
            
            fig = lib_obj.compare_spectra_with_bands(
                selected_minerals,
                figsize=(12, 8),
                title=f"{input.satellite()} - Selected Minerals ({len(selected_minerals)})",
                show_response_functions=input.satellite_show_response_functions(),
                show_band_centers=input.satellite_show_band_centers(),
                show_band_ranges=input.satellite_show_band_ranges()
            )
            
            current_satellite_plot.set(fig)
            return fig
            
        except Exception as e:
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.text(0.5, 0.5, f'Error generating satellite plot:\n{str(e)}',
                   ha='center', va='center', transform=ax.transAxes, fontsize=12, color='red')
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
            return fig
    
    @output
    @render.plot
    def satellite_band_plot():
        """Generate satellite band response function plot"""
        if not current_satellite_lib():
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.text(0.5, 0.5, 'No satellite band data available',
                   ha='center', va='center', transform=ax.transAxes, fontsize=14, color='#666')
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
            return fig
        
        try:
            lib_obj = current_satellite_lib()
            fig = lib_obj.plot_band_responses_detailed(figsize=(12, 6))
            current_band_plot.set(fig)
            return fig if fig else plt.figure(figsize=(12, 6))
            
        except Exception as e:
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.text(0.5, 0.5, f'Error generating band plot:\n{str(e)}',
                   ha='center', va='center', transform=ax.transAxes, fontsize=12, color='red')
            return fig
    
    @output
    @render.data_frame
    def satellite_band_info_table():
        """Display satellite band information table"""
        if not current_satellite_lib():
            return pd.DataFrame({"Status": ["No satellite data loaded"]})
        
        try:
            lib_obj = current_satellite_lib()
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
    def satellite_selected_mineral_table():
        """Display data for selected satellite minerals"""
        if not current_satellite_lib() or not input.satellite_mineral_families():
            return pd.DataFrame({"Status": ["Select mineral families to view data"]})
        
        try:
            lib_obj = current_satellite_lib()
            
            # Get selected minerals
            if input.satellite_individual_minerals():
                selected_keys = input.satellite_individual_minerals()
            else:
                selected_keys = get_filtered_satellite_minerals()
            
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
    
    # === FULL SPECTRUM TAB LOGIC ===
    @reactive.Calc
    def get_filtered_full_spectrum_minerals():
        """Get full spectrum minerals that match the selected families"""
        if not current_full_spectrum_lib() or not input.full_spectrum_mineral_families():
            return []
        
        filtered = []
        for family in input.full_spectrum_mineral_families():
            family_minerals = [key for key in current_full_spectrum_lib().spectra.keys() 
                             if family in key and input.spectrometer() in key]
            filtered.extend(family_minerals[:input.full_spectrum_max_samples()])
        return filtered
    
    @reactive.Effect
    def update_full_spectrum_individual_choices():
        """Update individual full spectrum mineral choices based on selected families"""
        choices = get_filtered_full_spectrum_minerals()
        ui.update_select(
            "full_spectrum_individual_minerals",
            choices=choices,
            selected=choices[:min(5, len(choices))] if choices else []
        )
    
    @reactive.Effect
    def load_full_spectrum_data():
        """Load data for the selected spectrometer"""
        try:
            new_lib = USGSSpectra(BASE_DIR, DEFAULT_COLLECTION, input.spectrometer())
            current_full_spectrum_lib.set(new_lib)
            
            # Update mineral family choices
            new_families = []
            for key in new_lib.spectra.keys():
                material = new_lib.spectra[key]['metadata']['material']
                if material not in new_families:
                    new_families.append(material)
            
            new_families.sort()
            ui.update_select("full_spectrum_mineral_families", choices=new_families)
            
        except Exception as e:
            print(f"Error loading full spectrum data: {e}")
    
    @output
    @render.ui
    def full_spectrum_status_info():
        """Display current full spectrum status"""
        if not current_full_spectrum_lib():
            return ui.div(
                ui.p("⚠️ No full spectrum library loaded.", style="color: #dc3545; margin: 0;")
            )
        
        lib_obj = current_full_spectrum_lib()
        num_spectra = len(lib_obj.spectra)
        num_families = len(input.full_spectrum_mineral_families()) if input.full_spectrum_mineral_families() else 0
        num_samples = len(get_filtered_full_spectrum_minerals())
        
        return ui.div(
            {"class": "status-text"},
            ui.p(f"🔬 {input.spectrometer()} | 📊 {num_spectra} spectra | 🔬 {num_families} families | 📈 {num_samples} samples",
                 style="margin: 5px 0;")
        )
    
    @output
    @render.plot
    def full_spectrum_main_plot():
        """Generate the full spectrum plot"""
        if not current_full_spectrum_lib() or not input.full_spectrum_mineral_families():
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.text(0.5, 0.5, 'Select mineral families to view full spectral data',
                   ha='center', va='center', transform=ax.transAxes, fontsize=14, color='#666')
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
            return fig
        
        try:
            lib_obj = current_full_spectrum_lib()
            
            # Use individual selection if available, otherwise use families
            if input.full_spectrum_individual_minerals():
                selected_minerals = input.full_spectrum_individual_minerals()
            else:
                selected_minerals = get_filtered_full_spectrum_minerals()
            
            if not selected_minerals:
                fig, ax = plt.subplots(figsize=(12, 6))
                ax.text(0.5, 0.5, f"No sample of selected minerals found in {input.spectrometer()} \n Please select anther spectrometer.",
                       ha='center', va='center', transform=ax.transAxes, fontsize=14, color='#666')
                ax.set_xlim(0, 1)
                ax.set_ylim(0, 1)
                ax.axis('off')
                return fig
            
            # Create the plot
            fig, ax = plt.subplots(figsize=(12, 6))
            
            for key in selected_minerals:
                if key in lib_obj.spectra:
                    spectrum = lib_obj.spectra[key]['spectrum']
                    metadata = lib_obj.spectra[key]['metadata']
                    
                    # Apply wavelength filter
                    wavelength_mask = (lib_obj.wavelengths >= input.wavelength_range()[0]) & \
                                    (lib_obj.wavelengths <= input.wavelength_range()[1])
                    if not wavelength_mask.any():
                        ax.text(0.5, 0.5, f'Error generating full spectrum plot:\n Please adjust the wavelength range according to the selected spectrometer.\n{str(e)}',
                        ha='center', va='center', transform=ax.transAxes, fontsize=12, color='red')
                    filtered_wavelengths = lib_obj.wavelengths[wavelength_mask]
                    filtered_spectrum = spectrum[wavelength_mask]
                    
                    ax.plot(filtered_wavelengths, filtered_spectrum, '-', 
                           label=f"{metadata['material']} {metadata['sample_id']}")
            
            ax.set_xlabel('Wavelength (μm)')
            ax.set_ylabel('Reflectance / Transmission')
            ax.set_title(f"{input.spectrometer()} - Selected Minerals ({len(selected_minerals)})")
            ax.grid(True, linestyle='--', alpha=0.7)
            ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            
            plt.tight_layout()
            current_full_spectrum_plot.set(fig)
            return fig
            
        except Exception as e:
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.text(0.5, 0.5, f'Error generating full spectrum plot:\n Please adjust the wavelength range according to the selected spectrometer.\n{str(e)}',
                   ha='center', va='center', transform=ax.transAxes, fontsize=12, color='red')
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
            return fig
    
    @output
    @render.data_frame
    def full_spectrum_selected_mineral_table():
        """Display data for selected full spectrum minerals"""
        if not current_full_spectrum_lib() or not input.full_spectrum_mineral_families():
            return pd.DataFrame({"Status": ["Select mineral families to view data"]})
        
        try:
            lib_obj = current_full_spectrum_lib()
            
            # Get selected minerals
            if input.full_spectrum_individual_minerals():
                selected_keys = input.full_spectrum_individual_minerals()
            else:
                selected_keys = get_filtered_full_spectrum_minerals()
            
            if not selected_keys:
                return pd.DataFrame({"Status": [f"No sample of selected minerals found in {input.spectrometer()}"]})
            
            # Create summary table
            table_data = []
            for key in selected_keys:
                if key in lib_obj.spectra:
                    metadata = lib_obj.spectra[key]['metadata']
                    spectrum = lib_obj.spectra[key]['spectrum']
                    
                    # Apply wavelength filter for statistics
                    wavelength_mask = (lib_obj.wavelengths >= input.wavelength_range()[0]) & \
                                    (lib_obj.wavelengths <= input.wavelength_range()[1])
                    filtered_spectrum = spectrum[wavelength_mask]
                    
                    table_data.append({
                        'Sample_Key': key,
                        'Material': metadata['material'],
                        'Spectrometer': metadata['spectrometer'],
                        'Purity': metadata['purity'],
                        'Measurement_Type': metadata['measurement_type'],
                        'Mean_Reflectance': np.nanmean(filtered_spectrum),
                        'Std_Reflectance': np.nanstd(filtered_spectrum),
                        'Min_Reflectance': np.nanmin(filtered_spectrum),
                        'Max_Reflectance': np.nanmax(filtered_spectrum),
                        'Wavelength_Range': f"{input.wavelength_range()[0]:.2f}-{input.wavelength_range()[1]:.2f} μm"
                    })
            
            df = pd.DataFrame(table_data)
            if not df.empty:
                numerical_cols = df.select_dtypes(include=[np.number]).columns
                df[numerical_cols] = df[numerical_cols].round(4)
            
            return df
        except Exception as e:
            return pd.DataFrame({"Error": [f"Error creating table: {str(e)}"]})
    
    # === DOWNLOAD HANDLERS ===
    @reactive.Effect
    @reactive.event(input.download_satellite_plot)
    def download_satellite_plot():
        """Download satellite spectral plot"""
        if not current_satellite_plot():
            download_message.set("No satellite plot available for download")
            return
        
        try:
            fig = current_satellite_plot()
            filename = f"satellite_plot_{input.satellite()}.png"
            fig.savefig(filename, dpi=300, bbox_inches='tight')
            download_message.set(f"✅ Satellite plot saved as {filename}")
        except Exception as e:
            download_message.set(f"❌ Error saving satellite plot: {str(e)}")
    
    @reactive.Effect
    @reactive.event(input.download_full_spectrum_plot)
    def download_full_spectrum_plot():
        """Download full spectrum plot"""
        if not current_full_spectrum_plot():
            download_message.set("No full spectrum plot available for download")
            return
        
        try:
            fig = current_full_spectrum_plot()
            filename = f"full_spectrum_plot_{input.spectrometer()}.png"
            fig.savefig(filename, dpi=300, bbox_inches='tight')
            download_message.set(f"✅ Full spectrum plot saved as {filename}")
        except Exception as e:
            download_message.set(f"❌ Error saving full spectrum plot: {str(e)}")
    
    @reactive.Effect
    @reactive.event(input.download_satellite_band_plot)
    def download_satellite_band_plot():
        """Download satellite band plot"""
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
    
    @output
    @render.text
    def download_status():
        """Display download status"""
        return download_message.get()

# Create the Shiny app
app = App(app_ui, server)

if __name__ == "__main__":
    app.run()