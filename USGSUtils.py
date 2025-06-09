import os
import re
import pickle
import numpy as np
class USGSUtils:
    def __init__(self, data_dir, prefix):
        """
        Initialise the Utils class with data directory and prefix.
        
        :param data_dir: Directory where data files are stored.
        """
        self.data_dir = data_dir
        self.prefix = prefix
        self.spectra = {}
        # print(f"USGSUtils initialized with data directory: {data_dir} and prefix: {prefix}")
            
    def save_to_pickle(self, data):
        """
        Save data to a pickle file.
        
        :param data: Data to be saved.
        :param filename: Name of the file where data will be saved.
        """
        filename = f'pickle_data/{self.prefix}data.pkl'
        
        with open(filename, 'wb') as f:
            pickle.dump(data, f)
            
    def load_from_pickle(self):
        """
        Load data from a pickle file.
        
        :param filename: Name of the file from which data will be loaded.
        :return: Loaded data.
        """
        filename = f'pickle_data/{self.prefix}data.pkl'
        with open(filename, 'rb') as f:
            data = pickle.load(f)
            return data
        
    def _parse_filename(self, filename):
        """
        Parse the spectrum filename to extract metadata
        
        Example: S07ASTER_Actinolite_HS22.4B_ASDFRb_AREF.txt
        """
        basename = os.path.basename(filename)
        # Remove prefix and file extension
        parts = basename.replace(self.prefix,'').replace('.txt', '').split('_')
        
        if len(parts) < 3:
            return None
        
        # Extract material, sample ID, and measurement info
        material = parts[0]
        
        # Extract spectrometer and purity code
        spec_code = parts[-2]
        spec_match = re.match(r'([A-Z]+[0-9]*)([a-z]+)', spec_code)
        
        if not spec_match:
            return None
            
        spectrometer = spec_match.group(1)
        purity = spec_match.group(2)
        
        # Extract sample ID (everything between material and spectrometer)
        sample_id = '_'.join(parts[1:-2])
        
        # Extract measurement type
        measurement_type = parts[-1]
        
        return {
            'material': material,
            'sample_id': sample_id,
            'spectrometer': spectrometer,
            'purity': purity,
            'measurement_type': measurement_type,
            'filename': basename,
            'full_path': filename,
        }
        

    def load_minerals(self, max_samples=None):
        """
        Load mineral spectra from Chapter M
        
        Parameters:
        -----------
        max_samples : int or None
            Maximum number of samples to load (None for all)
            
        Returns:
        --------
        dict
            Dictionary of loaded mineral spectra
        """
        # Find the minerals directory
        minerals_dir = self.data_dir / "ChapterM_Minerals"
        if not minerals_dir.exists():
            raise FileNotFoundError(f"Could not find minerals directory: {minerals_dir}")
        
        # Find all spectrum files
        spectrum_files = list(minerals_dir.glob(f"{self.prefix}*.txt"))
        
        
        print(f"Found {len(spectrum_files)} mineral spectra files")
        
        # Load each spectrum
        for i, filename in enumerate(spectrum_files):
            if i % 100 == 0:
                print(f"Loading spectrum {i+1}/{len(spectrum_files)}")
            
            try:
                # Parse filename for metadata
                metadata = self._parse_filename(str(filename))
                if not metadata:
                    print(f"Could not parse filename: {filename}")
                    continue
                
                # Load spectrum data
                spectrum = np.loadtxt(filename, skiprows=1)
                
                # Replace deleted channels with NaN
                spectrum[spectrum < -1e30] = np.nan
                
                # Create a unique key
                key = f"{metadata['material']}_{metadata['sample_id']}"
                
                # Store the data
                self.spectra[key] = {
                    'metadata': metadata,
                    'spectrum': spectrum
                }
                
            except Exception as e:
                print(f"Error loading spectrum {filename}: {str(e)}")
        
        # print(f"Successfully loaded {len(self.spectra)} mineral spectra")
        return self.spectra