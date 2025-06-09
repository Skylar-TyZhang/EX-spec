import os
import numpy as np
import pandas as pd
import glob
import matplotlib.pyplot as plt
from pathlib import Path
from USGSUtils import USGSUtils
import pickle


class USGSSpectra:
    def __init__(self, base_dir, collection, spectrometer=None):
        """
        Initialise the USGS Spectral Library collection data loader

        Parameters:
        -----------
        base_dir : str
            Base directory containing USGS Spectral Library ASCII files
        collection : str
            - a : measured spectra (ASCIIdata_splib07a.zip), including wavelength positions and bandpass (FullWidth
            at HalfMaximum;FWHM) values of channels in the spectrometers utilised
            - b: spectra interpolated to a higher number of more finely-spaced channels (ASCIIdata_splib07b.zip))
        specrometer : str
            Spectrometer type to filter spectra.
            - "BECK":Beckman 5270 (0.2-3.0 μm)
            - "ASDFR": Standard resolution - Analytical Spectral Devices (ASD) field spectrometers (0.35-2.5 μm)
            - "ASDHR": high resolution - Analytical Spectral Devices (ASD) field spectrometers (0.35-2.5 μm)
            - "ASDNG": high resolution next generation - Analytical Spectral Devices (ASD) field spectrometers (0.35-2.5 μm)
            - "NIC4": Nicolet FTIR interferometer spectrometers (1.12-216 μm)
            - "AVIRIS": NASA AVIRIS imaging spectrometer (0.37-2.5 μm)
        """
        self.base_dir = Path(base_dir)
        self.collection = collection
        self.prefix = f"splib07{collection}_"
        self.spectrometer = spectrometer

        # Find the appropriate data directory
        self.data_dir = list(self.base_dir.glob(f"**/ASCIIdata_splib07{collection}"))[0]
        if not self.data_dir.exists():
            raise FileNotFoundError(f"Could not find data directory for {collection}")

        print(f"Found data directory: {self.data_dir}")

        # Initialise collections
        self.spectra = self.load_minerals_pickle()  # Load mineral spectra from pickle or raw data
        self.wavelengths = None  # Normal wavelengths (for plotting with spectra)
        self.bandpass = None  # Bandpass in nanometers
        self.bands = {}  # Dictionary to store individual band response functions
        self.band_info = None  # DataFrame to store band information

        # Load wavelength data
        self._load_wavelength_data()
        # Load utility functions
        self.utils = USGSUtils(self.data_dir, self.prefix)

    def _load_wavelength_data(self):
        """Load wavelength and bandpass data for the collection sensor"""
        # Load normal wavelengths (with "bands" in filename)
        wavelength_pattern = f"{self.prefix}Wavelengths*_{self.spectrometer}*.txt"

        wavelength_files = list(self.data_dir.glob(wavelength_pattern))

        if wavelength_files:
            wavelength_file = wavelength_files[0]
            print(f"Loading {self.spectrometer} wavelength data")
            self.wavelengths = np.loadtxt(wavelength_file, skiprows=1)
            print(f"Loaded normal wavelength data: {len(self.wavelengths)} measures")

        # Load bandpass data in nanometers
        bandpass_pattern = f"{self.prefix}Bandpass*_{self.spectrometer}*.txt"
        bandpass_files = list(self.data_dir.glob(bandpass_pattern))

        if bandpass_files:
            bandpass_file = bandpass_files[0]
            print(f"Loading {self.spectrometer} bandpass data ")
            self.bandpass = np.loadtxt(bandpass_file, skiprows=1)
            print(f"Loaded bandpass data: {len(self.bandpass)} values")

    def load_minerals_pickle(self, max_samples=None):
        """
        Load mineral spectra from pre-saved pickle files

        Parameters:
        -----------
        max_samples : int or None
            Maximum number of samples to load (None for all)

        Returns:
        --------
        dict
            Dictionary of loaded mineral spectra
        """
        try:
            with open(f"pickle_data/{self.prefix}data.pkl", "rb") as f:
                self.spectra = pickle.load(f)
            print(f"Loaded {len(self.spectra)} spectra from pickle file")
            return self.spectra

        except Exception as e:
            print(f"Error loading spectrum from pickle file: {str(e)}")
            self.spectra = self.utils.load_minerals()
            self.utils.save_to_pickle(self, self.spectra)

    
