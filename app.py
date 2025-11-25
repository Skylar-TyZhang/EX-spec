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
from USGSSpectra import USGSSpectra

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
            get_full_spectrum_tab(full_spectrum_mineral_families, DEFAULT_COLLECTION, DEFAULT_SPECTROMETER),
            
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
        print('satellite_main_plot called')
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
        """Display data for selected satellite minerals including per-wavelength spectrum data"""
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
            
            # Get reference wavelengths from library
            reference_wavelengths = getattr(lib_obj, "wavelengths", None)
            if reference_wavelengths is None or len(reference_wavelengths) == 0:
                # fallback to stats-only table if no wavelength grid available
                table_data = []
                for key in selected_keys:
                    if key in lib_obj.spectra:
                        metadata = lib_obj.spectra[key]['metadata']
                        spectrum = lib_obj.spectra[key]['spectrum']
                        table_data.append({
                            'Sample_Key': key,
                            'Material': metadata.get('material', 'N/A'),
                            'Spectrometer': metadata.get('spectrometer', 'N/A'),
                            'Purity': metadata.get('purity', 'N/A'),
                            'Measurement_Type': metadata.get('measurement_type', 'N/A'),
                        })
                df = pd.DataFrame(table_data)
                if not df.empty:
                    numerical_cols = df.select_dtypes(include=[np.number]).columns
                    df[numerical_cols] = df[numerical_cols].round(4)
                return df
            
            # Create column names for wavelengths
            wl_cols = [f"WL_{float(w):.4f}" for w in reference_wavelengths]
            
            table_rows = []
            for key in selected_keys:
                if key not in lib_obj.spectra:
                    continue
                data = lib_obj.spectra[key]
                metadata = data.get('metadata', {})
                spectrum = np.asarray(data.get('spectrum', []), dtype=float)
                
                # Align/interpolate to reference wavelengths if needed
                if spectrum.shape[0] == reference_wavelengths.shape[0]:
                    aligned = spectrum
                else:
                    # try to use per-sample wavelength array if available
                    sample_wl = np.asarray(data.get('wavelength')) if data.get('wavelength') is not None else None
                    if sample_wl is not None and sample_wl.shape[0] == spectrum.shape[0]:
                        try:
                            valid = ~np.isnan(spectrum)
                            if valid.sum() >= 2:
                                f = interp1d(sample_wl[valid], spectrum[valid], kind='linear',
                                             bounds_error=False, fill_value=np.nan)
                                aligned = f(reference_wavelengths)
                            else:
                                aligned = np.full_like(reference_wavelengths, np.nan, dtype=float)
                        except Exception:
                            # fallback: attempt numpy.interp (requires sorted and finite)
                            try:
                                aligned = np.interp(reference_wavelengths, sample_wl, np.nan_to_num(spectrum, nan=0.0))
                                # where extrapolated values exist, set to nan if outside sample wl range
                                aligned[(reference_wavelengths < sample_wl.min()) | (reference_wavelengths > sample_wl.max())] = np.nan
                            except Exception:
                                aligned = np.full_like(reference_wavelengths, np.nan, dtype=float)
                    else:
                        aligned = np.full_like(reference_wavelengths, np.nan, dtype=float)
                
                row = {
                    'Sample_Key': key,
                    'Material': metadata.get('material', 'N/A'),
                    'Spectrometer': metadata.get('spectrometer', 'N/A'),
                    'Purity': metadata.get('purity', 'N/A'),
                    'Measurement_Type': metadata.get('measurement_type', 'N/A'),
                    
                }
                
                # add spectrum columns
                for col, val in zip(wl_cols, aligned):
                    row[col] = np.nan if np.isnan(val) else float(val)
                
                table_rows.append(row)
            
            df = pd.DataFrame(table_rows)
            if not df.empty:
                # round numeric columns (including spectrum columns) to sensible precision
                numerical_cols = df.select_dtypes(include=[np.number]).columns
                df[numerical_cols] = df[numerical_cols].round(6)
            
            return df
        except Exception as e:
            return pd.DataFrame({"Error": [f"Error creating table: {str(e)}"]})

    @render.download(
        filename=lambda: f"{input.satellite()}_selected_minerals.csv"
    )
    async def download_satellite_selected_table():
        """Download the satellite_selected_mineral_table as CSV (async generator)"""
        if not current_satellite_lib() or not input.satellite_mineral_families():
            yield "Error,Message\n"
            yield "No Data,Select mineral families to enable download\n"
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

            # Get reference wavelengths from library
            reference_wavelengths = getattr(lib_obj, "wavelengths", None)
            if reference_wavelengths is None or len(reference_wavelengths) == 0:
                # Emit metadata-only CSV
                header = "Sample_Key,Material,Spectrometer,Purity,Measurement_Type\n"
                yield header
                for i, key in enumerate(selected_keys, start=1):
                    if key not in lib_obj.spectra:
                        continue
                    metadata = lib_obj.spectra[key]['metadata']
                    row = [
                        key,
                        metadata.get('material', 'N/A'),
                        metadata.get('spectrometer', 'N/A'),
                        metadata.get('purity', 'N/A'),
                        metadata.get('measurement_type', 'N/A')
                    ]
                    yield ",".join(map(str, row)) + "\n"
                    if i % 5 == 0:
                        download_message.set(f"Generating CSV: {i}/{len(selected_keys)} samples...")
                        await asyncio.sleep(0.01)
                download_message.set(f"Download complete ({len(selected_keys)} samples)")
                return

            # Build CSV header with wavelength columns
            wl_cols = [f"WL_{float(w):.4f}" for w in reference_wavelengths]
            metadata_columns = ["Sample_Key", "Material", "Spectrometer", "Purity", "Measurement_Type"]
            header = ",".join(metadata_columns + wl_cols) + "\n"
            yield header

            # Process each sample and yield rows
            processed = 0
            for key in selected_keys:
                if key not in lib_obj.spectra:
                    continue
                data = lib_obj.spectra[key]
                metadata = data.get('metadata', {})
                spectrum = np.asarray(data.get('spectrum', []), dtype=float)

                # Align/interpolate to reference wavelengths if needed
                if spectrum.shape[0] == reference_wavelengths.shape[0]:
                    aligned = spectrum
                else:
                    sample_wl = np.asarray(data.get('wavelength')) if data.get('wavelength') is not None else None
                    if sample_wl is not None and sample_wl.shape[0] == spectrum.shape[0]:
                        try:
                            valid = ~np.isnan(spectrum)
                            if valid.sum() >= 2:
                                f = interp1d(sample_wl[valid], spectrum[valid], kind='linear',
                                             bounds_error=False, fill_value=np.nan)
                                aligned = f(reference_wavelengths)
                            else:
                                aligned = np.full_like(reference_wavelengths, np.nan, dtype=float)
                        except Exception:
                            try:
                                aligned = np.interp(reference_wavelengths, sample_wl, np.nan_to_num(spectrum, nan=0.0))
                                aligned[(reference_wavelengths < sample_wl.min()) | (reference_wavelengths > sample_wl.max())] = np.nan
                            except Exception:
                                aligned = np.full_like(reference_wavelengths, np.nan, dtype=float)
                    else:
                        aligned = np.full_like(reference_wavelengths, np.nan, dtype=float)

                metadata_values = [
                    key,
                    metadata.get('material', 'N/A'),
                    metadata.get('spectrometer', 'N/A'),
                    metadata.get('purity', 'N/A'),
                    metadata.get('measurement_type', 'N/A'),
                ]

                spectrum_values = [f"{float(v):.6f}" if not np.isnan(v) else "NaN" for v in aligned]
                row = ",".join(map(str, metadata_values + spectrum_values)) + "\n"
                yield row

                processed += 1
                if processed % 5 == 0:
                    download_message.set(f"🔄 Generating CSV: {processed}/{len(selected_keys)} samples...")
                    await asyncio.sleep(0.01)

            download_message.set(f" Download complete ({processed} spectra, {len(reference_wavelengths)} wavelength points)")
        except Exception as e:
            download_message.set(f" Error exporting selected minerals CSV: {str(e)}")
            yield f"Error,{str(e)}\n"
    
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
        wl_range = f"{input.wavelength_range()[0]:.1f}-{input.wavelength_range()[1]:.1f} μm"
        
        return ui.div(
            {"class": "status-text"},
            ui.p(f"🔬 {input.spectrometer()} | 📊 {num_spectra} spectra | 🔬 {num_families} families | 📈 {num_samples} samples | 📏 {wl_range}",
                 style="margin: 5px 0;")
        )
    
    @output
    @render.ui
    def full_spectrum_main_plot():
        """Generate the interactive full spectrum plot using Plotly"""
        if not current_full_spectrum_lib() or not input.full_spectrum_mineral_families():
            return ui.div(
                {"style": "text-align: center; padding: 50px; color: #666;"},
                ui.h4("Select mineral families to view full spectral data"),
                ui.p("Choose one or more mineral families and adjust the wavelength range")
            )
        
        try:
            lib_obj = current_full_spectrum_lib()
            
            # Use individual selection if available, otherwise use families
            if input.full_spectrum_individual_minerals():
                selected_minerals = input.full_spectrum_individual_minerals()
            else:
                selected_minerals = get_filtered_full_spectrum_minerals()
            
            if not selected_minerals:
                return ui.div(
                    {"style": "text-align: center; padding: 50px; color: #666;"},
                    ui.h4("No minerals selected"),
                    ui.p("Adjust your selection criteria or increase the maximum samples per family")
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
                return pd.DataFrame({"Status": ["No minerals selected"]})
            
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
                        'Wavelength_Range': f"{input.wavelength_range()[0]:.2f}-{input.wavelength_range()[1]:.2f} μm"
                    })
            
            df = pd.DataFrame(table_data)
            if not df.empty:
                numerical_cols = df.select_dtypes(include=[np.number]).columns
                df[numerical_cols] = df[numerical_cols].round(4)
            
            return df
        except Exception as e:
            return pd.DataFrame({"Error": [f"Error creating table: {str(e)}"]})
    
    # === ASYNC DOWNLOAD HANDLERS ===
    @output
    @render.download(
        filename=lambda: f"{current_full_spectrum_lib().spectrometer if current_full_spectrum_lib() else 'unknown'}_full-spectrum.csv"
    )
    async def download_full_spectrum_table():
        """Download selected full spectrum mineral data in wide format (one row per spectrum)"""
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
            
            # Update status
            download_message.set(f"🔄 Generating wide format data for {len(selected_keys)} samples...")
            
            # First pass: determine common wavelength grid
            # We'll use the wavelength range filter
            if input.wavelength_range():
                min_wl, max_wl = input.wavelength_range()
            else:
                min_wl, max_wl = 0.2, 25.0
            
            # Get wavelengths from first spectrum as reference
            reference_wavelengths = None
            for key in selected_keys:
                if key in lib_obj.spectra:
                    data = lib_obj.spectra[key]
                    wavelengths = data['wavelength']
                    mask = (wavelengths >= min_wl) & (wavelengths <= max_wl)
                    reference_wavelengths = wavelengths[mask]
                    break
            
            if reference_wavelengths is None or len(reference_wavelengths) == 0:
                yield "Error,Message\n"
                yield "No Data,No wavelength data available\n"
                return
            
            # Create header with metadata columns and wavelength columns
            metadata_columns = [
                "Sample_Key", "Material", "Sample_ID", "Spectrometer", "Purity", 
                "Measurement_Type", "Chapter", "Formula", "Grain_Size", "Mineral_Type",
                "Wavelength_Range", "HTML_File_Path"
            ]
            
            # Add wavelength columns (formatted to 4 decimal places)
            wavelength_columns = [f"WL_{wl:.4f}" for wl in reference_wavelengths]
            
            header = ",".join(metadata_columns + wavelength_columns) + "\n"
            yield header
            
            await asyncio.sleep(0.01)
            
            # Process each sample
            processed_count = 0
            wavelength_range_str = f"{min_wl:.2f}-{max_wl:.2f} μm"
            
            for key in selected_keys:
                if key in lib_obj.spectra:
                    data = lib_obj.spectra[key]
                    spectrum = data['spectrum']
                    metadata = data['metadata']
                    wavelengths = data['wavelength']
                    
                    # Apply wavelength filtering
                    mask = (wavelengths >= min_wl) & (wavelengths <= max_wl)
                    filtered_wavelengths = wavelengths[mask]
                    filtered_spectrum = spectrum[mask]
                    
                    # Interpolate spectrum to reference wavelengths if needed
                    if not np.array_equal(filtered_wavelengths, reference_wavelengths):
                        from scipy.interpolate import interp1d
                        valid_idx = ~np.isnan(filtered_spectrum)
                        if np.sum(valid_idx) >= 2:
                            f = interp1d(filtered_wavelengths[valid_idx], filtered_spectrum[valid_idx],
                                    kind='linear', bounds_error=False, fill_value=np.nan)
                            interpolated_spectrum = f(reference_wavelengths)
                        else:
                            interpolated_spectrum = np.full_like(reference_wavelengths, np.nan)
                    else:
                        interpolated_spectrum = filtered_spectrum
                    
                    # Build metadata row
                    html_path = metadata.get('html_file_path', 'N/A')
                    metadata_values = [
                        key,
                        metadata['material'],
                        metadata.get('sample_id', 'N/A'),
                        metadata['spectrometer'],
                        metadata['purity'],
                        metadata['measurement_type'],
                        metadata.get('chapter', 'N/A'),
                        metadata.get('formula', 'N/A'),
                        metadata.get('grain_size', 'N/A'),
                        metadata.get('mineral_type', 'N/A'),
                        wavelength_range_str,
                        html_path
                    ]
                    
                    # Add spectrum values
                    spectrum_values = [f"{val:.6f}" if not np.isnan(val) else "NaN" 
                                    for val in interpolated_spectrum]
                    
                    row = ",".join(map(str, metadata_values + spectrum_values)) + "\n"
                    yield row
                    
                    processed_count += 1
                    
                    # Update progress periodically
                    if processed_count % 5 == 0:
                        download_message.set(f"🔄 Processing wide format: {processed_count}/{len(selected_keys)} samples...")
                        await asyncio.sleep(0.01)
            
            # Final status update
            download_message.set(f" Wide format data download completed ({processed_count} spectra, {len(reference_wavelengths)} wavelength points)")
            
        except Exception as e:
            download_message.set(f" Error exporting wide format data: {str(e)}")
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