# app.py
from shiny import App, ui, render, reactive
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from pathlib import Path
import io
import base64
import asyncio
import os

# Import the USGS Spectra classes
from USGSSatelliteSpectra import USGSSatelliteSpectra
from USGSSpectralLibrary import USGSSpectralLibrary  

# Import the Plotly visualiser
from USGSPlotly import PlotlyUSGSVisualiser
from atmospheric_transmission import atmospheric_data

# Import the custom components
from components.satellite_tab import get_satellite_tab
from components.full_spectrum_tab import get_full_spectrum_tab
from components.ui_tags_setup import ui_tags
from components.header import get_header
from components.usage_tab import get_usage_info

# Configuration
BASE_DIR = "ASCIIdata"
DEFAULT_SATELLITE = "ASTER"
DEFAULT_COLLECTION = "b"
HTML_METADATA_DIR = "HTMLmetadata/"  

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
        
        # initialise full spectrum library with enhanced metadata support
        data_dir = f"{BASE_DIR}/ASCIIdata_splib07{DEFAULT_COLLECTION}"
        full_spectrum_lib = USGSSpectralLibrary(
            data_dir=data_dir,
            library_version=f'splib07{DEFAULT_COLLECTION}',
            html_metadata_dir=HTML_METADATA_DIR
        )
        
        # Load mineral spectra from pickle or create from ASCII files
        full_spectrum_lib.load_minerals_pickle('M')
        
        # Extract full spectrum mineral information
        all_full_spectrum_minerals = list(full_spectrum_lib.spectra.keys())
        full_spectrum_mineral_families = full_spectrum_lib.get_available_materials()
        
        print(f"Satellite library: {len(all_satellite_minerals)} spectra, {len(satellite_mineral_families)} families")
        print(f"Full spectrum library: {len(all_full_spectrum_minerals)} spectra, {len(full_spectrum_mineral_families)} families")
        
        # Print available spectrometers in full spectrum data
        spectrometers = full_spectrum_lib.get_available_spectrometers()
        print(f"Available spectrometers: {spectrometers}")
        
    except Exception as e:
        print(f"Error initialising libraries: {e}")

# initialise libraries when the app starts
initialise_libraries()

# initialise the Plotly visualiser
plotly_visualiser = PlotlyUSGSVisualiser()

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
            get_full_spectrum_tab(full_spectrum_mineral_families, DEFAULT_COLLECTION),
            
            # Usage Information Tab
            get_usage_info()
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
            new_lib.load_minerals_pickle()
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
    @render.ui
    def satellite_main_plot():
        """Generate the interactive satellite spectral plot using Plotly"""
        if not current_satellite_lib() or not input.satellite_mineral_families():
            return ui.div(
                {"style": "text-align: center; padding: 50px; color: #666;"},
                ui.h4("Select mineral families to view satellite spectral data"),
                ui.p("Choose one or more mineral families from the control panel above")
            )
        
        try:
            lib_obj = current_satellite_lib()
            
            # Use individual selection if available, otherwise use families
            if input.satellite_individual_minerals():
                selected_minerals = input.satellite_individual_minerals()
            else:
                selected_minerals = get_filtered_satellite_minerals()
            
            if not selected_minerals:
                return ui.div(
                    {"style": "text-align: center; padding: 50px; color: #666;"},
                    ui.h4("No minerals selected"),
                    ui.p("Adjust your selection criteria or increase the maximum samples per family")
                )
            
            # Create interactive Plotly figure
            fig = plotly_visualiser.create_satellite_spectra_plot(
                lib_obj,
                selected_minerals,
                show_band_centers=input.satellite_show_band_centers(),
                show_band_ranges=input.satellite_show_band_ranges(),
                show_response_functions=input.satellite_show_response_functions(),
                show_atmospheric_transmission=input.satellite_show_atmospheric_transmission(),
                height=700
            )
            
            # Return Plotly plot as HTML
            return ui.HTML(fig.to_html(include_plotlyjs="cdn", div_id="satellite_plot"))
            
        except Exception as e:
            return ui.div(
                {"style": "text-align: center; padding: 50px; color: red;"},
                ui.h4("Error generating satellite plot"),
                ui.p(f"Error details: {str(e)}")
            )
    
    @output
    @render.ui
    def satellite_band_plot():
        """Generate satellite band response function plot using Plotly"""
        if not current_satellite_lib():
            return ui.div(
                {"style": "text-align: center; padding: 50px; color: #666;"},
                ui.h4("No satellite band data available")
            )
        
        try:
            lib_obj = current_satellite_lib()
            fig = plotly_visualiser.create_band_response_plot(lib_obj, height=500)
            return ui.HTML(fig.to_html(include_plotlyjs="cdn", div_id="band_plot"))
            
        except Exception as e:
            return ui.div(
                {"style": "text-align: center; padding: 50px; color: red;"},
                ui.h4("Error generating band plot"),
                ui.p(f"Error details: {str(e)}")
            )
    
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
    
    # === FULL SPECTRUM TAB LOGIC (Updated for USGSSpectralLibrary) ===
    @reactive.Calc
    def get_filtered_full_spectrum_minerals():
        """Get full spectrum minerals that match the selected criteria"""
        if not current_full_spectrum_lib():
            return []
        
        lib_obj = current_full_spectrum_lib()
        
        # Start with all spectra
        filtered_spectra = lib_obj.spectra.copy()
        
        # Apply material search filter
        if input.material_search():
            search_term = input.material_search().lower()
            filtered_spectra = {
                key: data for key, data in filtered_spectra.items()
                if search_term in data['metadata']['material'].lower()
            }
        
        # Apply material family filter
        if input.full_spectrum_mineral_families():
            filtered_spectra = {
                key: data for key, data in filtered_spectra.items()
                if data['metadata']['material'] in input.full_spectrum_mineral_families()
            }
        
        # Apply spectrometer filter
        if input.spectrometer() and input.spectrometer() != "All":
            filtered_spectra = {
                key: data for key, data in filtered_spectra.items()
                if data['metadata']['spectrometer'] == input.spectrometer()
            }
        
        # Apply wavelength range filter
        if input.wavelength_range():
            min_wl, max_wl = input.wavelength_range()
            min_coverage = input.min_wavelength_coverage() / 100.0
            
            filtered_keys = []
            for key, data in filtered_spectra.items():
                wavelengths = data['wavelength']
                
                # Calculate coverage within the selected range
                in_range = (wavelengths >= min_wl) & (wavelengths <= max_wl)
                coverage = np.sum(in_range) / len(wavelengths)
                
                if coverage >= min_coverage:
                    filtered_keys.append(key)
            
            # Apply max samples per family limit
            if input.full_spectrum_max_samples():
                family_counts = {}
                final_keys = []
                
                for key in filtered_keys:
                    material = filtered_spectra[key]['metadata']['material']
                    if material not in family_counts:
                        family_counts[material] = 0
                    
                    if family_counts[material] < input.full_spectrum_max_samples():
                        final_keys.append(key)
                        family_counts[material] += 1
                
                return final_keys
            else:
                return filtered_keys
        
        return list(filtered_spectra.keys())
    
    @reactive.Effect
    def update_full_spectrum_individual_choices():
        """Update individual full spectrum mineral choices based on selected criteria"""
        choices = get_filtered_full_spectrum_minerals()
        ui.update_select(
            "full_spectrum_individual_minerals",
            choices=choices,
            selected=choices[:min(5, len(choices))] if choices else []
        )
    
    @reactive.Effect
    def update_material_families_based_on_search():
        """Update material families based on search input"""
        if not current_full_spectrum_lib():
            return
        
        lib_obj = current_full_spectrum_lib()
        
        if input.material_search():
            search_term = input.material_search().lower()
            filtered_materials = [
                material for material in lib_obj.get_available_materials()
                if search_term in material.lower()
            ]
        else:
            filtered_materials = lib_obj.get_available_materials()
        
        # Update the choices but keep current selection if still valid
        current_selection = input.full_spectrum_mineral_families() or []
        new_selection = [mat for mat in current_selection if mat in filtered_materials]
        
        ui.update_select(
            "full_spectrum_mineral_families",
            choices=filtered_materials,
            selected=new_selection
        )
    
    @output
    @render.ui
    def full_spectrum_status_info():
        """Display current full spectrum status"""
        if not current_full_spectrum_lib():
            return ui.div(
                ui.p("⚠️ No full spectrum library loaded.", style="color: #dc3545; margin: 0;")
            )
        
        lib_obj = current_full_spectrum_lib()
        total_spectra = len(lib_obj.spectra)
        
        # Count spectra for current filters
        filtered_spectra = get_filtered_full_spectrum_minerals()
        num_filtered = len(filtered_spectra)
        
        # Get spectrometer info
        spectrometer_info = input.spectrometer() if input.spectrometer() != "All" else "All"
        
        # Get wavelength range
        wl_range = f"{input.wavelength_range()[0]:.1f}-{input.wavelength_range()[1]:.1f} μm"
        
        # Get material families count
        num_families = len(input.full_spectrum_mineral_families()) if input.full_spectrum_mineral_families() else 0
        
        return ui.div(
            {"class": "status-text"},
            ui.p(f"🔬 {spectrometer_info} | 📊 {num_filtered}/{total_spectra} spectra | 🔬 {num_families} families | 📏 {wl_range}",
                 style="margin: 5px 0;")
        )
    
    @output
    @render.ui
    def full_spectrum_main_plot():
        """Generate the interactive full spectrum plot using Plotly"""
        if not current_full_spectrum_lib():
            return ui.div(
                {"style": "text-align: center; padding: 50px; color: #666;"},
                ui.h4("No full spectrum data loaded"),
                ui.p("Please check the data directory and try again")
            )
        
        try:
            lib_obj = current_full_spectrum_lib()
            
            # Use individual selection if available, otherwise use filtered results
            if input.full_spectrum_individual_minerals():
                selected_minerals = input.full_spectrum_individual_minerals()
            else:
                selected_minerals = get_filtered_full_spectrum_minerals()
            
            if not selected_minerals:
                return ui.div(
                    {"style": "text-align: center; padding: 50px; color: #666;"},
                    ui.h4("No minerals match your current filters"),
                    ui.p("Try adjusting your search criteria, wavelength range, or spectrometer filter")
                )
            
            # Create interactive Plotly figure
            fig = plotly_visualiser.create_full_spectrum_plot(
                lib_obj,
                selected_minerals,
                wavelength_range=tuple(input.wavelength_range()),
                show_atmospheric_transmission=input.full_spectrum_show_atmospheric_transmission(),
                height=600
            )
            
            # Return Plotly plot as HTML
            return ui.HTML(fig.to_html(include_plotlyjs="cdn", div_id="full_spectrum_plot"))
            
        except Exception as e:
            return ui.div(
                {"style": "text-align: center; padding: 50px; color: red;"},
                ui.h4("Error generating full spectrum plot"),
                ui.p(f"Error details: {str(e)}")
            )
    
    @output
    @render.data_frame
    def full_spectrum_selected_mineral_table():
        """Display data for selected full spectrum minerals with enhanced metadata"""
        if not current_full_spectrum_lib():
            return pd.DataFrame({"Status": ["No full spectrum data loaded"]})
        
        try:
            lib_obj = current_full_spectrum_lib()
            
            # Get selected minerals
            if input.full_spectrum_individual_minerals():
                selected_keys = input.full_spectrum_individual_minerals()
            else:
                selected_keys = get_filtered_full_spectrum_minerals()
            
            if not selected_keys:
                return pd.DataFrame({"Status": ["No minerals match current filters"]})
            
            # Create summary table with enhanced metadata
            table_data = []
            for key in selected_keys:
                if key in lib_obj.spectra:
                    data = lib_obj.spectra[key]
                    metadata = data['metadata']
                    spectrum = data['spectrum']
                    wavelengths = data['wavelength']
                    
                    # Apply wavelength filter for statistics
                    wavelength_mask = (wavelengths >= input.wavelength_range()[0]) & \
                                    (wavelengths <= input.wavelength_range()[1])
                    filtered_spectrum = spectrum[wavelength_mask]
                    
                    table_data.append({
                        'Sample_Key': key,
                        'Material': metadata['material'],
                        'Sample_ID': metadata.get('sample_id', 'N/A'),
                        'Spectrometer': metadata['spectrometer'],
                        'Purity': metadata['purity'],
                        'Measurement_Type': metadata['measurement_type'],
                        'Formula': metadata.get('formula', 'N/A'),
                        'Grain_Size': metadata.get('grain_size', 'N/A'),
                        'Chapter': metadata.get('chapter', 'N/A'),
                        'Mean_Value': np.nanmean(filtered_spectrum),
                        'Std_Value': np.nanstd(filtered_spectrum),
                        'Min_Value': np.nanmin(filtered_spectrum),
                        'Max_Value': np.nanmax(filtered_spectrum),
                        'Wavelength_Range': f"{input.wavelength_range()[0]:.2f}-{input.wavelength_range()[1]:.2f} μm",
                        'HTML_Available': 'Yes' if metadata.get('html_file_path') else 'No'
                    })
            
            df = pd.DataFrame(table_data)
            if not df.empty:
                numerical_cols = df.select_dtypes(include=[np.number]).columns
                df[numerical_cols] = df[numerical_cols].round(4)
            
            return df
        except Exception as e:
            return pd.DataFrame({"Error": [f"Error creating table: {str(e)}"]})
    
    # === ASYNC DOWNLOAD HANDLERS ===
    @render.download(
        filename=lambda: f"{input.satellite()}_data.csv"
    )
    async def download_satellite_table():
        """Download selected satellite mineral data using async generator"""
        if not current_satellite_lib() or not input.satellite_mineral_families():
            yield "Error,Message\n"
            yield "No Data,No satellite data available for download\n"
            return
        
        try:
            lib_obj = current_satellite_lib()
            
            # Get selected minerals
            if input.satellite_individual_minerals():
                selected_keys = input.satellite_individual_minerals()
            else:
                selected_keys = get_filtered_satellite_minerals()
            
            if not selected_keys:
                yield "Error,Message\n"
                yield "No Selection,No minerals selected\n"
                return
            
            # Yield CSV header
            yield "Sample_Key,Material,Sample_ID,Spectrometer,Purity,Measurement_Type,Satellite,Wavelength_um,Band_Number,Reflectance_Value\n"
            
            # Update status
            download_message.set(f"🔄 Generating satellite data for {len(selected_keys)} samples...")
            
            # Process each sample
            processed_count = 0
            for key in selected_keys:
                if key in lib_obj.spectra:
                    spectrum = lib_obj.spectra[key]['spectrum']
                    metadata = lib_obj.spectra[key]['metadata']
                    
                    # Process in batches to provide feedback
                    for i, (wl, refl) in enumerate(zip(lib_obj.wavelengths, spectrum)):
                        row = f"{key},{metadata['material']},{metadata['sample_id']},{metadata['spectrometer']},{metadata['purity']},{metadata['measurement_type']},{lib_obj.satellite},{wl},{i+1},{refl}\n"
                        yield row
                        
                        # Small delay every 100 rows to not overwhelm
                        if i % 100 == 0:
                            await asyncio.sleep(0.001)
                    
                    processed_count += 1
                    
                    # Update progress periodically
                    if processed_count % 5 == 0:
                        download_message.set(f"🔄 Processing satellite data: {processed_count}/{len(selected_keys)} samples...")
                        await asyncio.sleep(0.01)
            
            # Final status update
            total_rows = len(selected_keys) * len(lib_obj.wavelengths)
            download_message.set(f"✅ Satellite data download completed ({total_rows} records)")
            
        except Exception as e:
            download_message.set(f"❌ Error exporting satellite data: {str(e)}")
            yield f"Error,{str(e)}\n"

    @render.download(
        filename=lambda: f"full_spectrum_{input.spectrometer()}.csv"
    )
    async def download_full_spectrum_table():
        """Download selected full spectrum mineral data using async generator"""
        if not current_full_spectrum_lib():
            yield "Error,Message\n"
            yield "No Data,No full spectrum data available for download\n"
            return
        
        try:
            lib_obj = current_full_spectrum_lib()
            
            # Get selected minerals
            if input.full_spectrum_individual_minerals():
                selected_keys = input.full_spectrum_individual_minerals()
            else:
                selected_keys = get_filtered_full_spectrum_minerals()
            
            if not selected_keys:
                yield "Error,Message\n"
                yield "No Selection,No minerals selected\n"
                return
            
            # Yield CSV header with enhanced metadata
            yield "Sample_Key,Material,Sample_ID,Spectrometer,Purity,Measurement_Type,Chapter,Formula,Grain_Size,Wavelength_um,Spectral_Value,Wavelength_Range,HTML_Available\n"
            
            # Update status
            download_message.set(f"🔄 Generating full spectrum data for {len(selected_keys)} samples...")
            
            # Process each sample
            processed_count = 0
            wavelength_range_str = f"{input.wavelength_range()[0]:.2f}-{input.wavelength_range()[1]:.2f} μm" if input.wavelength_range() else "Full Range"
            
            for key in selected_keys:
                if key in lib_obj.spectra:
                    data = lib_obj.spectra[key]
                    spectrum = data['spectrum']
                    metadata = data['metadata']
                    wavelengths = data['wavelength']
                    
                    # Apply wavelength filtering if specified
                    if input.wavelength_range():
                        mask = (wavelengths >= input.wavelength_range()[0]) & (wavelengths <= input.wavelength_range()[1])
                        wavelengths = wavelengths[mask]
                        spectrum = spectrum[mask]
                    
                    # Process in batches
                    for i, (wl, val) in enumerate(zip(wavelengths, spectrum)):
                        row = f"{key},{metadata['material']},{metadata.get('sample_id', 'N/A')},{metadata['spectrometer']},{metadata['purity']},{metadata['measurement_type']},{metadata.get('chapter', 'N/A')},{metadata.get('formula', 'N/A')},{metadata.get('grain_size', 'N/A')},{wl},{val},{wavelength_range_str},{'Yes' if metadata.get('html_file_path') else 'No'}\n"
                        yield row
                        
                        # Small delay every 200 rows for full spectrum (larger datasets)
                        if i % 200 == 0:
                            await asyncio.sleep(0.001)
                    
                    processed_count += 1
                    
                    # Update progress periodically
                    if processed_count % 3 == 0:
                        download_message.set(f"🔄 Processing full spectrum data: {processed_count}/{len(selected_keys)} samples...")
                        await asyncio.sleep(0.01)
            
            # Final status update
            total_rows = sum(len(lib_obj.spectra[key]['spectrum']) for key in selected_keys if key in lib_obj.spectra)
            download_message.set(f"✅ Full spectrum data download completed ({total_rows} records)")
            
        except Exception as e:
            download_message.set(f"❌ Error exporting full spectrum data: {str(e)}")
            yield f"Error,{str(e)}\n"
    
    @render.download(
        filename=lambda: f"{input.satellite()}_band_info.csv"
    )
    async def download_satellite_band_table():
        """Download satellite band information table using async generator"""
        if not current_satellite_lib():
            yield "Error,Message\n"
            yield "No Data,No satellite data available for download\n"
            return
        
        try:
            lib_obj = current_satellite_lib()
            band_info = lib_obj.get_band_info()
            
            if band_info is not None and not band_info.empty:
                # Update status
                download_message.set("🔄 Generating band information...")
                await asyncio.sleep(0.1)
                
                # Yield header
                yield ",".join(band_info.columns) + "\n"
                
                # Yield rows
                for _, row in band_info.iterrows():
                    yield ",".join(str(val) for val in row.values) + "\n"
                    await asyncio.sleep(0.01)  # Small delay between rows
                
                download_message.set("✅ Band information download completed")
            else:
                yield "Error,Message\n"
                yield "No Data,No band information available\n"
                
        except Exception as e:
            download_message.set(f"❌ Error downloading band table: {str(e)}")
            yield f"Error,{str(e)}\n"
    
    @output
    @render.text
    def download_status():
        """Display download status"""
        return download_message.get()

# Create the Shiny app
app = App(app_ui, server)

if __name__ == "__main__":
    app.run()