import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import re
import glob
from USGSUtils import USGSUtils
import pickle

class USGSSatelliteSpectra:
    def __init__(self, base_dir, satellite='ASTER'):
        """
        Initialize the USGS Spectral Library satellite data loader
        
        Parameters:
        -----------
        base_dir : str
            Base directory containing USGS Spectral Library files
        satellite : str
            Satellite sensor name (e.g., 'ASTER', 'LSAT8', 'SNTL2', 'WV3')
        """
        satellite_mapping = {
            'ASTER':'ASTER', 
            'Landsat8':'LSAT8', 
            'Sentinel2':'SNTL2',
            'WorldView3':'WV3'
        }
        
        self.base_dir = Path(base_dir)
        self.satellite = satellite
        self.prefix = f"S07{satellite_mapping[satellite]}_"
        
        # Find the appropriate data directory
        self.data_dir = list(self.base_dir.glob(f"**/ASCIIdata_splib07b_rs{satellite}"))[0]
        if not self.data_dir.exists():
            raise FileNotFoundError(f"Could not find data directory for {satellite}")
        
        print(f"Found data directory for {satellite}: {self.data_dir}")
        
        # Load utility functions
        self.utils = USGSUtils(self.data_dir, self.prefix)
        
        # Initialise collections
        
        self.spectra = self.load_all_chapters_pickle()  # Load mineral spectra from pickle or raw data
        self.wavelengths = None           # Normal wavelengths (for plotting with spectra)
        self.wavelengths_hp = None        # Hyperspectral wavelengths (for band data)
        self.bandpass_nm = None           # Bandpass in nanometers
        self.bandpass_micron = None       # Bandpass in microns
        self.bands = {}                   # Dictionary to store individual band response functions
        self.band_info = None             # DataFrame to store band information
        
        # Load wavelength data
        self._load_wavelength_data()
        # Load band information
        self._load_band_data()
        
        
    
    def _load_wavelength_data(self):
        """Load wavelength and bandpass data for the satellite sensor"""
        
        # Load normal wavelengths (with "bands" in filename)
        wavelength_pattern = f"{self.prefix}Wavelengths*bands*.txt"
        wavelength_files = list(self.data_dir.glob(wavelength_pattern))
        
        if wavelength_files:
            wavelength_file = wavelength_files[0]
            # print(f"Loading normal wavelength data from: {wavelength_file}")
            self.wavelengths = np.loadtxt(wavelength_file, skiprows=1)
            # print(f"Loaded normal wavelength data: {len(self.wavelengths)} bands")
        
        # Load hyperspectral wavelengths ()
        hp_wavelength_pattern = f"{self.prefix}Wavelengths_*S*R*F*.txt"
        hp_wavelength_files = list(self.data_dir.glob(hp_wavelength_pattern))
        
        if hp_wavelength_files:
            hp_wavelength_file = hp_wavelength_files[0]
            #print(f"Loading hyperspectral wavelength data from: {hp_wavelength_file}")
            self.wavelengths_hp = np.loadtxt(hp_wavelength_file, skiprows=1)
            print(f"Loaded hyperspectral wavelength data: {len(self.wavelengths_hp)} channels")
        
        # Load bandpass data in nanometers
        bandpass_nm_pattern = f"{self.prefix}Bandpass*nm.txt"
        bandpass_nm_files = list(self.data_dir.glob(bandpass_nm_pattern))
        
        if bandpass_nm_files:
            bandpass_nm_file = bandpass_nm_files[0]
            print(f"Loading bandpass data (nm) from: {bandpass_nm_file}")
            self.bandpass_nm = np.loadtxt(bandpass_nm_file, skiprows=1)
            print(f"Loaded bandpass data (nm): {len(self.bandpass_nm)} values")
        
        # Load bandpass data in microns
        bandpass_micron_pattern = f"{self.prefix}Bandpass*um.txt"
        bandpass_micron_files = list(self.data_dir.glob(bandpass_micron_pattern))
        
        if bandpass_micron_files:
            bandpass_micron_file = bandpass_micron_files[0]
            #print(f"Loading bandpass data (microns) from: {bandpass_micron_file}")
            self.bandpass_micron = np.loadtxt(bandpass_micron_file, skiprows=1)
            print(f"Loaded bandpass data (microns): {len(self.bandpass_micron)} values")
        
    def _load_band_data(self):
        """Load individual band response functions"""
        
        # Pattern to match band files: S07LSAT8_SRF_Band_3_Landsat8_Green.txt
        band_pattern = f"{self.prefix}*SRF*Band*.txt"
        band_files = list(self.data_dir.glob(band_pattern))
        
        #print(f"Found {len(band_files)} band response function files")
        
        for band_file in band_files:
            try:
                # Parse the band information from filename
                filename = band_file.name
                # Extract band number and name
               
                parts = filename.replace(self.prefix, '').replace('.txt', '').split('_')
                
                if len(parts) >= 4 and parts[0] == 'SRF' and 'Band' in parts:
                    # Extract band number
                    band_number = parts[parts.index('Band')+1]
                    # Extract band name (everything after the satellite name)
                    band_name_parts = parts[4:]  # Skip 'SRF', 'Band', number, and satellite name
                    band_name = '_'.join(band_name_parts) if band_name_parts else f"Band_{band_number}"
                    
                    # Load the band response function
                    band_data = np.loadtxt(band_file, skiprows=1)
                    
                    # Store band information
                    self.bands[band_number] = {
                        'band_name': band_name,
                        'response': band_data,
                        'filename': filename,
                        'wavelengths': self.wavelengths_hp if self.wavelengths_hp is not None else np.arange(len(band_data))
                    }
                    
                    print(f"Loaded Band {band_number} ({band_name}): {len(band_data)} values")
                    
            except Exception as e:
                print(f"Error loading band file {band_file}: {str(e)}")
        
        print(f"Successfully loaded {len(self.bands)} band response functions")
            
    def get_band_info(self):
        """
        Get summary information about loaded bands
        
        Returns:
        --------
        pandas.DataFrame
            DataFrame with band information
        """
        if not self.bands:
            print("No band data loaded")
            return None
        
        band_info = []
        
        for band_num, band_data in sorted(self.bands.items()):
            response = band_data['response']
            wavelengths_band = band_data['wavelengths']
            
            # Calculate band statistics
            min_len = min(len(wavelengths_band), len(response))
            wavelengths_band = wavelengths_band[:min_len]
            response = response[:min_len]
            
            peak_idx = np.argmax(response)
            peak_wavelength = wavelengths_band[peak_idx]
            peak_response = response[peak_idx]
            
            # Calculate effective wavelength (weighted average)
            total_response = np.sum(response)
            if total_response > 0:
                eff_wavelength = np.sum(wavelengths_band * response) / total_response
            else:
                eff_wavelength = peak_wavelength
            
            # Calculate FWHM
            half_max = peak_response / 2
            indices = np.where(response >= half_max)[0]
            if len(indices) > 0:
                fwhm_start = wavelengths_band[indices[0]]
                fwhm_end = wavelengths_band[indices[-1]]
                fwhm = fwhm_end - fwhm_start
            else:
                fwhm = 0
            
            band_info.append({
                # 'Band_Number': band_num,
                'Band_Name': band_data['band_name'],
                'Peak_Wavelength_um': peak_wavelength,
                'Effective_Wavelength_um': eff_wavelength,
                'FWHM_um': fwhm,
                'FWHM_start': fwhm_start,
                'FWHM_end': fwhm_end,                
                'Peak_Response': peak_response,
                'Min_Wavelength_um': np.min(wavelengths_band),
                'Max_Wavelength_um': np.max(wavelengths_band)
            })

        return pd.DataFrame(band_info)
    
    def plot_band_responses_detailed(self, figsize=(15, 10)):
        """
        Plot detailed band response functions for the satellite
        
        Parameters:
        -----------
        figsize : tuple
            Figure size
            
        Returns:
        --------
        matplotlib.figure.Figure
            The figure object
        """
        if not self.bands or self.wavelengths_hp is None:
            print("No band response data available")
            return None
        
        # Sort bands by band number
        sorted_bands = sorted(self.bands.items())
        num_bands = len(sorted_bands)
        
        # Create subplots
        cols = min(3, num_bands)
        rows = (num_bands + cols - 1) // cols
        
        fig, axes = plt.subplots(rows, cols, figsize=figsize)
        if rows == 1 and cols == 1:
            axes = [axes]
        elif rows == 1 or cols == 1:
            axes = axes.flatten()
        else:
            axes = axes.flatten()
        
        # Plot each band
        for i, (band_num, band_info) in enumerate(sorted_bands):
            if i >= len(axes):
                break
                
            ax = axes[i]
            response = band_info['response']
            wavelengths_band = band_info['wavelengths']
            
            # Ensure wavelengths and response have same length
            min_len = min(len(wavelengths_band), len(response))
            wavelengths_band = wavelengths_band[:min_len]
            response = response[:min_len]
            
            # Plot the response function
            ax.fill_between(wavelengths_band, 0, response, alpha=0.6, color=f'C{i}')
            ax.plot(wavelengths_band, response, color=f'C{i}', linewidth=2)
            
            # Calculate and display band statistics
            peak_idx = np.argmax(response)
            peak_wavelength = wavelengths_band[peak_idx]
            peak_response = response[peak_idx]
            
            # Calculate FWHM
            half_max = peak_response / 2
            indices = np.where(response >= half_max)[0]
            if len(indices) > 0:
                fwhm_start = wavelengths_band[indices[0]]
                fwhm_end = wavelengths_band[indices[-1]]
                fwhm = fwhm_end - fwhm_start
            else:
                fwhm = 0
            
            ax.set_title(f"Band {band_num}: {band_info['band_name']}\n"
                        f"Peak: {peak_wavelength:.3f} μm\n"
                        f"FWHM: {fwhm:.3f} μm",fontsize=6)
            ax.set_xlabel('Wavelength (μm)')
            ax.set_ylabel('Response')
            ax.grid(True, linestyle='--', alpha=0.3)
            
            # Add vertical line at peak
            ax.axvline(x=peak_wavelength, color='red', linestyle='--', alpha=0.8)
            
            # Add FWHM markers
            if fwhm > 0:
                ax.axvspan(fwhm_start, fwhm_end, alpha=0.2, color='gray')
        
        # Hide unused subplots
        for i in range(num_bands, len(axes)):
            axes[i].set_visible(False)
        
        plt.tight_layout()
        plt.suptitle(f'{self.satellite} Band Response Functions Detail', fontsize=10, y=1)
        
        return fig

    def plot_mineral_family(self, mineral_family, max_samples=10, figsize=(12, 8)):
        """
        Plot spectra for a mineral family
        
        Parameters:
        -----------
        mineral_family : str
            Partial name of the mineral family to plot
        max_samples : int
            Maximum number of samples to include
        figsize : tuple
            Figure size
            
        Returns:
        --------
        matplotlib.figure.Figure
            The figure object
        """
        # Find matching spectra
        matching_keys = [key for key in self.spectra.keys() 
                         if mineral_family in key]
        
        # Limit the number of samples
        if max_samples and max_samples < len(matching_keys):
            matching_keys = matching_keys[:max_samples]
        
        if not matching_keys:
            print(f"No spectra found matching mineral family: {mineral_family}")
            return None
        
        print(f"Found {len(matching_keys)} matching samples for {mineral_family}")
        
        # Plot the spectra
        return self.compare_spectra(matching_keys, figsize=figsize, 
                                   title=f"{self.satellite} {mineral_family.title()} Family Spectra")
        
    def compare_spectra(self, keys, figsize=(12, 8), title=None):
        """
        Compare multiple spectra on a single plot
        
        Parameters:
        -----------
        keys : list
            List of spectrum keys to compare
        figsize : tuple
            Figure size
        title : str
            Plot title (optional)
            
        Returns:
        --------
        matplotlib.figure.Figure
            The figure object
        """
        fig, ax = plt.subplots(figsize=figsize)
        
        for key in keys:
            if key in self.spectra:
                # get the spectrum and metadata
                spectrum = self.spectra[key]['spectrum']
                metadata = self.spectra[key]['metadata']
                
                # Plot the spectrum
                ax.plot(self.wavelengths, spectrum, 'o-', label=f"{metadata['material']} {metadata['sample_id']}")
        
        # Add labels
        ax.set_xlabel('Wavelength (μm)')
        ax.set_ylabel('Reflectance / Transmission')
        
        if title:
            ax.set_title(title)
        else:
            ax.set_title(f"{self.satellite} Spectral Comparison")
        
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.legend()
        
        plt.tight_layout()
        return fig  
      
    def plot_spectrum_with_bands(self, mineral_family, figsize=(14, 8), show_response_functions=True, 
                                show_band_centers=True, show_band_ranges=True):
        """
        Plot a spectrum with band information overlaid
        
        Parameters:
        -----------
        spectrum_key : str
            Key of the spectrum to plot
        figsize : tuple
            Figure size
        show_response_functions : bool
            Whether to show the band response functions
        show_band_centers : bool
            Whether to show vertical lines at band centers
        show_band_ranges : bool
            Whether to show shaded regions for band ranges
            
        Returns:
        --------
        matplotlib.figure.Figure
            The figure object
        """
        # Check if the spectrum exists
        # Find matching spectra
        spectrum_keys = [key for key in self.spectra.keys() 
                         if mineral_family in key]
        if not spectrum_keys:
            raise KeyError(f"Spectrum key not found: {spectrum_keys}")
        
        # Create figure with subplots for bands and response functions
        if show_response_functions and self.bands:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize, height_ratios=[3, 1])
        else:
            fig, ax1 = plt.subplots(figsize=figsize)
            ax2 = None
        
        # Get the spectrum data of samples in the mineral family 
        for spectrum_key in spectrum_keys:
            if spectrum_key in self.spectra:
                spectrum = self.spectra[spectrum_key]['spectrum']
                metadata = self.spectra[spectrum_key]['metadata']   
                
                # Plot the main spectrum
                ax1.plot(self.wavelengths, 
                         spectrum, 
                         'o-', 
                         label=f"{metadata['material']} {metadata['sample_id']}")
            
        # Add band information if available
        if self.bands and self.wavelengths is not None:
            # Sort bands by band number
            sorted_bands = sorted(self.bands.items())
            # Create colormap for bands
            colors = plt.cm.Set3(np.linspace(0, 1, len(sorted_bands)))
               
            for i, (band_num, band_info) in enumerate(sorted_bands):
                # Extract the band number for index
                band_num = ''.join([char for char in band_num if char.isdigit()])
                band_num = int(band_num)
        
                color = colors[i]
                band_center = self.wavelengths[band_num - 1] if band_num <= len(self.wavelengths) else None
                
                # Show band center as vertical line
                if show_band_centers and band_center is not None:
                    ax1.axvline(x=band_center, color=color, linestyle='--', alpha=0.8, linewidth=1.5)
                
                # Show band range as shaded region (using bandpass if available)
                if show_band_ranges and band_center is not None:
                    if self.bandpass_micron is not None and band_num <= len(self.bandpass_micron):
                        bandpass = self.bandpass_micron[band_num - 1]
                        band_min = band_center - bandpass / 2
                        band_max = band_center + bandpass / 2
                        
                        ax1.axvspan(band_min, band_max, alpha=0.2, color=color)
                '''
                # Add band annotation
                if band_center is not None:
                    y_pos = ax1.get_ylim()[1] * (0.95)  # Stagger annotations
                    
                    ax1.annotate(f"{band_info['band_name']}", 
                               xy=(band_center, y_pos), 
                               xytext=(5, 0), textcoords='offset points',
                               ha='left', va='top', fontsize=8,
                               bbox=dict(boxstyle='round,pad=0.2', facecolor=color, alpha=0.6),
                               rotation=0)
                '''
        
        # Set labels for main plot
        ax1.set_xlabel('Wavelength (μm)')
        if metadata['measurement_type'] == 'AREF':
            ax1.set_ylabel('Absolute Reflectance')
        elif metadata['measurement_type'] == 'RREF':
            ax1.set_ylabel('Relative Reflectance')
        elif metadata['measurement_type'] == 'TRAN':
            ax1.set_ylabel('Transmission')
        else:
            ax1.set_ylabel('Value')
        
        ax1.set_title(f"{metadata['material']} - {self.satellite}")
        ax1.grid(True, linestyle='--', alpha=0.3)
        ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        
        # Plot band response functions if requested and available
        if show_response_functions and ax2 is not None and self.bands and self.wavelengths_hp is not None:
            
            # Plot each band response function
            sorted_bands = sorted(self.bands.items())
            colors = plt.cm.Set3(np.linspace(0, 1, len(sorted_bands)))
            
            for i, (band_num, band_info) in enumerate(sorted_bands):
                color = colors[i]
                response = band_info['response']
                wavelengths_band = band_info['wavelengths']
                
                # Ensure wavelengths and response have same length
                min_len = min(len(wavelengths_band), len(response))
                wavelengths_band = wavelengths_band[:min_len]
                response = response[:min_len]
                
                # Plot the response function
                ax2.fill_between(wavelengths_band, 0, response, alpha=0.6, color=color, 
                               label=f"{band_info['band_name']}")
                ax2.plot(wavelengths_band, response, color=color, linewidth=1)
            
            ax2.set_xlabel('Wavelength (μm)')
            ax2.set_ylabel('Response')
            ax2.set_title(f'{self.satellite} Band Response Functions')
            ax2.grid(True, linestyle='--', alpha=0.3)
            ax2.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            
            # Match x-axis limits
            ax2.set_xlim(ax1.get_xlim())
        
        plt.tight_layout()
        return fig
    
    def compare_spectra_with_bands(self, keys, figsize=(12, 10), show_response_functions=True, 
                                show_band_centers=True, show_band_ranges=True, title=None):
        """
        Compare multiple spectra on a single plot with band information
        
        Parameters:
        -----------
        keys : list
            List of spectrum keys to compare
        figsize : tuple
            Figure size
        show_response_functions : bool
            Whether to show band response functions
        show_band_centers : bool
            Whether to show band center lines
        show_band_ranges : bool
            Whether to show band ranges
        title : str
            Plot title (optional)
            
        Returns:
        --------
        matplotlib.figure.Figure
            The figure object
        """
        # Create figure with subplots for bands and response functions
        if show_response_functions and self.bands:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize, height_ratios=[3, 1])
        else:
            fig, ax1 = plt.subplots(figsize=figsize)
            ax2 = None
            
        for key in keys:
            if key in self.spectra:
                # get the spectrum and metadata
                spectrum = self.spectra[key]['spectrum']
                metadata = self.spectra[key]['metadata']
                
                # Plot the spectrum
                ax1.plot(self.wavelengths, spectrum, 'o-', label=f"{metadata['material']} {metadata['sample_id']}")
        
        # Add band information if available
        if self.bands and self.wavelengths is not None:
            # Sort bands by band number
            sorted_bands = sorted(self.bands.items())
            # Create colormap for bands
            colors = plt.cm.Set3(np.linspace(0, 1, len(sorted_bands)))
               
            for i, (band_num, band_info) in enumerate(sorted_bands):
                # Extract the band number for index
                band_num_int = ''.join([char for char in band_num if char.isdigit()])
                band_num_int = int(band_num_int)
        
                color = colors[i]
                band_center = self.wavelengths[band_num_int - 1] if band_num_int <= len(self.wavelengths) else None
                
                # Show band center as vertical line
                if show_band_centers and band_center is not None:
                    ax1.axvline(x=band_center, color=color, linestyle='--', alpha=0.8, linewidth=1.5)
                
                # Show band range as shaded region (using bandpass if available)
                if show_band_ranges and band_center is not None:
                    if self.bandpass_micron is not None and band_num_int <= len(self.bandpass_micron):
                        bandpass = self.bandpass_micron[band_num_int - 1]
                        band_min = band_center - bandpass / 2
                        band_max = band_center + bandpass / 2
                        
                        ax1.axvspan(band_min, band_max, alpha=0.2, color=color)
        
        # Set labels for main plot
        ax1.set_xlabel('Wavelength (μm)')
        if keys and keys[0] in self.spectra:
            metadata = self.spectra[keys[0]]['metadata']
            if metadata['measurement_type'] == 'AREF':
                ax1.set_ylabel('Absolute Reflectance')
            elif metadata['measurement_type'] == 'RREF':
                ax1.set_ylabel('Relative Reflectance')
            elif metadata['measurement_type'] == 'TRAN':
                ax1.set_ylabel('Transmission')
            else:
                ax1.set_ylabel('Value')
        else:
            ax1.set_ylabel('Reflectance / Transmission')
        
        if title:
            ax1.set_title(title)
        else:
            ax1.set_title(f"{self.satellite} Spectral Comparison")
        ax1.grid(True, linestyle='--', alpha=0.3)
        ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        
        # Plot band response functions if requested and available
        if show_response_functions and ax2 is not None and self.bands and self.wavelengths_hp is not None:
            
            # Plot each band response function
            sorted_bands = sorted(self.bands.items())
            colors = plt.cm.Set3(np.linspace(0, 1, len(sorted_bands)))
            
            for i, (band_num, band_info) in enumerate(sorted_bands):
                color = colors[i]
                response = band_info['response']
                wavelengths_band = band_info['wavelengths']
                
                # Ensure wavelengths and response have same length
                min_len = min(len(wavelengths_band), len(response))
                wavelengths_band = wavelengths_band[:min_len]
                response = response[:min_len]
                
                # Plot the response function
                ax2.fill_between(wavelengths_band, 0, response, alpha=0.6, color=color, 
                               label=f"{band_info['band_name']}")
                ax2.plot(wavelengths_band, response, color=color, linewidth=1)
            
            ax2.set_xlabel('Wavelength (μm)')
            ax2.set_ylabel('Response')
            ax2.set_title(f'{self.satellite} Band Response Functions')
            ax2.grid(True, linestyle='--', alpha=0.3)
            ax2.legend(bbox_to_anchor=(1.05, 1), loc='upper left', ncol=2)
            
            # Match x-axis limits
            ax2.set_xlim(ax1.get_xlim())
        
        plt.tight_layout()
        return fig
    
    def load_all_chapters_pickle(self, chapters=['A', 'C', 'L', 'M', 'O', 'S', 'V'], max_samples_per_chapter=None):
        """
        Load satellite spectra from multiple chapters with proper pickle handling
        
        Parameters:
        -----------
        chapters : list
            List of chapter codes to load (e.g., ['M', 'S', 'V'])
        max_samples_per_chapter : int or None
            Maximum number of samples per chapter
            
        Returns:
        --------
        dict
            Dictionary of loaded spectra from all chapters
        """
        all_spectra = {}
        
        # Chapter directory mapping
        chapter_dirs = {
            'M': 'ChapterM_Minerals',
            'S': 'ChapterS_SoilsAndMixtures',
            'C': 'ChapterC_Coatings',
            'L': 'ChapterL_Liquids',
            'O': 'ChapterO_OrganicCompounds',
            'A': 'ChapterA_ArtificialMaterials',
            'V': 'ChapterV_Vegetation'
        }
        
        for chapter in chapters:
            if chapter not in chapter_dirs:
                print(f"Unknown chapter: {chapter}, skipping...")
                continue
            
            chapter_dir_name = chapter_dirs[chapter]
            pickle_file = f'pickle_data/{self.prefix}{chapter}_data.pkl'
            
            # Try to load from pickle first
            try:
                with open(pickle_file, 'rb') as f:
                    chapter_spectra = pickle.load(f)
                print(f"Loaded {len(chapter_spectra)} spectra from pickle: {pickle_file}")
                
            except FileNotFoundError:
                print(f"Pickle file not found: {pickle_file} \nNow loading from ASCII files instead")
                
                # Load from ASCII files
                chapter_spectra = self._load_chapter_from_ascii(
                    chapter, 
                    chapter_dir_name, 
                    max_samples_per_chapter
                )
                
                if chapter_spectra:
                    # Save to pickle for future use
                    try:
                        # Ensure pickle directory exists
                        import os
                        os.makedirs('pickle_data', exist_ok=True)
                        
                        with open(pickle_file, 'wb') as f:
                            pickle.dump(chapter_spectra, f)
                        print(f"Saved {len(chapter_spectra)} spectra to pickle: {pickle_file}")
                    except Exception as save_error:
                        print(f"Error saving pickle: {save_error}")
                else:
                    print(f"No spectra loaded from chapter {chapter}")
                    continue
                    
            except Exception as e:
                print(f"Error loading pickle: {str(e)}")
                print(f"Attempting to load from ASCII files...")
                
                chapter_spectra = self._load_chapter_from_ascii(
                    chapter, 
                    chapter_dir_name, 
                    max_samples_per_chapter
                )
                
                if chapter_spectra:
                    try:
                        import os
                        os.makedirs('pickle_data', exist_ok=True)
                        with open(pickle_file, 'wb') as f:
                            pickle.dump(chapter_spectra, f)
                        print(f"Saved {len(chapter_spectra)} spectra to pickle: {pickle_file}")
                    except Exception as save_error:
                        print(f"Error saving pickle: {save_error}")
            
            # Add chapter info to metadata and update keys to avoid conflicts
            for key, spectrum_data in chapter_spectra.items():
                spectrum_data['metadata']['chapter'] = chapter_dir_name.split('_')[1]
                # Add chapter prefix to key to avoid conflicts between chapters
                unique_key = f"{chapter}_{key}"
                all_spectra[unique_key] = spectrum_data
        
        self.spectra = all_spectra
        print(f"\n{'='*60}")
        print(f"Total loaded: {len(all_spectra)} spectra from {len(chapters)} chapters")
        print(f"{'='*60}\n")
        
        return all_spectra

    def _load_chapter_from_ascii(self, chapter_code, chapter_dir_name, max_samples=None):
        """
        Load spectra from a specific chapter directory
        
        Parameters:
        -----------
        chapter_code : str
            Single letter chapter code (e.g., 'M', 'S')
        chapter_dir_name : str
            Full chapter directory name (e.g., 'ChapterM_Minerals')
        max_samples : int or None
            Maximum number of samples to load
            
        Returns:
        --------
        dict
            Dictionary of loaded spectra
        """
        # Try multiple possible locations for the chapter directory
        possible_paths = [
            self.data_dir / chapter_dir_name,  # Direct subdirectory
            self.data_dir.parent / chapter_dir_name,  # Parent directory
            self.data_dir / "ChapterM_Minerals" / ".." / chapter_dir_name  # Sibling to Minerals
        ]
        
        chapter_dir = None
        for path in possible_paths:
            if path.exists():
                chapter_dir = path
                break
        
        if chapter_dir is None:
            print(f"Chapter directory not found: {chapter_dir_name}")
            print(f"  Searched in:")
            for path in possible_paths:
                print(f"    - {path}")
            return {}
        
        print(f"Found chapter directory for ASCII data: {chapter_dir}")
        
        # Find all spectrum files matching the pattern
        spectrum_files = list(chapter_dir.glob(f"{self.prefix}*.txt"))
        
        if not spectrum_files:
            print(f"No spectrum files found matching pattern: {self.prefix}*.txt")
            return {}
        
        print(f"Found {len(spectrum_files)} spectrum files")
        
        if max_samples and max_samples < len(spectrum_files):
            spectrum_files = spectrum_files[:max_samples]
            print(f"  Limited to {max_samples} samples")
        
        chapter_spectra = {}
        successful = 0
        failed = 0
        
        for i, filename in enumerate(spectrum_files):
            if i % 50 == 0:  # Progress update every 50 files
                print(f"  Progress: {i+1}/{len(spectrum_files)} files processed...")
            
            try:
                # Parse filename for metadata
                metadata = self.utils._parse_filename(str(filename))
                
                if not metadata:
                    print(f"! No metadata, skipping file with unrecognized format: {filename.name}")
                    failed += 1
                    continue
                
                # Load spectrum data
                spectrum = np.loadtxt(filename, skiprows=1)

                
                # Replace deleted channels with NaN
                spectrum[spectrum < -1e30] = np.nan
                
                # Create a unique key (without chapter prefix here - added later)
                key = f"{metadata['material']}_{metadata['sample_id']}"
                
                chapter_spectra[key] = {
                    'metadata': metadata,
                    'spectrum': spectrum
                }
                successful += 1
                
            except Exception as e:
                failed += 1
                if failed <= 5:  # Only print first 5 errors
                    print(f"Error loading {filename.name}: {str(e)}")
        
        print(f"Successfully loaded: {successful} spectra")
        if failed > 0:
            print(f"Failed to load: {failed} files")
        
        return chapter_spectra