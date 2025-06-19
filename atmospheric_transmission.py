import numpy as np
import pandas as pd
from pathlib import Path
import openpyxl
from typing import Tuple, Optional

class AtmosphericTransmission:
    """Class to handle atmospheric transmission data for remote sensing applications"""
    
    def __init__(self, data_file_path: Optional[str] = None):
        """
        Initialise atmospheric data loader
        
        Parameters:
        -----------
        data_file_path : str, optional
            Path to atmospheric transmission Excel file
        """
        self.wavelengths = None
        self.transmission = None
        self.data_loaded = False
        
        if data_file_path:
            self.load_data(data_file_path)
        else:
            # Use default atmospheric transmission data (simplified model)
            #self._load_default_data()
            print("No atmospheric data found")
    
    def load_data(self, file_path: str):
        """
        Load atmospheric transmission data from Excel file
        
        Parameters:
        -----------
        file_path : str
            Path to the Excel file containing atmospheric data
        """
        try:
            # Read the Excel file
            df = pd.read_excel(file_path, sheet_name=0, header=None)
            
            # Extract data starting from row 12 (0-indexed: row 11)
            # Column 0: wavelength (μm), Column 1: transmission
            data_start_row = 11  # 0-indexed
            
            wavelengths = []
            transmissions = []
            
            for i in range(data_start_row, len(df)):
                try:
                    wl = df.iloc[i, 0]
                    trans = df.iloc[i, 1]
                    
                    # Check if both values are numeric and reasonable
                    if (isinstance(wl, (int, float)) and isinstance(trans, (int, float)) and
                        0.1 <= wl <= 50.0 and 0.0 <= trans <= 1.0):
                        wavelengths.append(float(wl))
                        transmissions.append(float(trans))
                except (IndexError, ValueError, TypeError):
                    continue
            
            if wavelengths and transmissions:
                self.wavelengths = np.array(wavelengths)
                self.transmission = np.array(transmissions)
                self.data_loaded = True
                print(f"Loaded atmospheric data: {len(self.wavelengths)} points, "
                      f"range {self.wavelengths.min():.3f}-{self.wavelengths.max():.3f} μm")
            else:
                print("No valid atmospheric data found, using default model")
                #self._load_default_data()
                
        except Exception as e:
            print(f"Error loading atmospheric data: {e}")
            print("Using default atmospheric model")
            
       
    def get_transmission(self, wavelength_range: Optional[Tuple[float, float]] = None):
        """
        Get atmospheric transmission data for plotting
        
        Parameters:
        -----------
        wavelength_range : tuple, optional
            (min_wavelength, max_wavelength) in microns
            
        Returns:
        --------
        tuple
            (wavelengths, transmission_values)
        """
        if not self.data_loaded:
            return None, None
        
        if wavelength_range is None:
            return self.wavelengths, self.transmission
        
        # Filter data to wavelength range
        mask = ((self.wavelengths >= wavelength_range[0]) & 
                (self.wavelengths <= wavelength_range[1]))
        
        return self.wavelengths[mask], self.transmission[mask]
    
    def get_atmospheric_windows(self, threshold: float = 0.5):
        """
        Identify atmospheric windows (high transmission regions)
        
        Parameters:
        -----------
        threshold : float
            Minimum transmission value to consider as a window
            
        Returns:
        --------
        list
            List of tuples (start_wavelength, end_wavelength) for each window
        """
        if not self.data_loaded:
            return []
        
        windows = []
        in_window = False
        start_wl = None
        
        for i, (wl, trans) in enumerate(zip(self.wavelengths, self.transmission)):
            if trans >= threshold and not in_window:
                # Start of a window
                start_wl = wl
                in_window = True
            elif trans < threshold and in_window:
                # End of a window
                windows.append((start_wl, wl))
                in_window = False
        
        # Handle case where data ends while in a window
        if in_window:
            windows.append((start_wl, self.wavelengths[-1]))
        
        return windows
    
    def interpolate_transmission(self, target_wavelengths):
        """
        Interpolate transmission values for specific wavelengths
        
        Parameters:
        -----------
        target_wavelengths : array-like
            Wavelengths to interpolate transmission for
            
        Returns:
        --------
        numpy.ndarray
            Interpolated transmission values
        """
        if not self.data_loaded:
            return np.zeros_like(target_wavelengths)
        
        return np.interp(target_wavelengths, self.wavelengths, self.transmission)

# Global instance for easy access
atmospheric_data = AtmosphericTransmission(data_file_path="data/Atmos_constits.xls")