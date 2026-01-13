import os
import re
import pickle
import numpy as np
from pathlib import Path

class USGSUtils:
    def __init__(self, data_dir, prefix):
        """
        Initialise the Utils class with data directory and prefix.
        
        :param data_dir: Directory where data files are stored.
        :param prefix: Prefix for the data files.
        """
        self.data_dir = Path(data_dir)
        self.prefix = prefix
        self.spectra = {}
        # Ensure pickle directory exists
        pickle_dir = Path('pickle_data')
        pickle_dir.mkdir(exist_ok=True)
        # print(f"USGSUtils initialized with data directory: {data_dir} and prefix: {prefix}")
            
    def save_to_pickle(self, data, chapter_name=None):
        """
        Save data to a pickle file.
        
        :param data: Data to be saved.
        :param chapter_name: Optional chapter name to include in filename
        """
        if chapter_name:
            filename = f'pickle_data/{self.prefix}{chapter_name}_data.pkl'
        else:
            filename = f'pickle_data/{self.prefix}data.pkl'
        
        with open(filename, 'wb') as f:
            pickle.dump(data, f)
        print(f"Saved {len(data)} spectra to {filename}")

    def load_from_pickle(self, chapter_name=None):
        """
        Load data from a pickle file.
        
        :param chapter_name: Optional chapter name to load specific chapter
        :return: Loaded data.
        """
        if chapter_name:
            filename = f'pickle_data/{self.prefix}{chapter_name}_data.pkl'
        else:
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
        
        if max_samples and max_samples < len(spectrum_files):
            spectrum_files = spectrum_files[:max_samples]
        
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
    
    def load_chapter(self, chapter_name, max_samples=None):
        """
        Load spectra from any chapter
        
        Parameters:
        -----------
        chapter_name : str
            Name of the chapter directory (e.g., 'ChapterM_Minerals', 'ChapterS_Soils')
        max_samples : int or None
            Maximum number of samples to load (None for all)
            
        Returns:
        --------
        dict
            Dictionary of loaded spectra
        """
        # Find the chapter directory
        chapter_dir = self.data_dir / chapter_name
        if not chapter_dir.exists():
            raise FileNotFoundError(f"Could not find chapter directory: {chapter_dir}")
        
        # Find all spectrum files
        spectrum_files = list(chapter_dir.glob(f"{self.prefix}*.txt"))
        
        print(f"Found {len(spectrum_files)} spectra files in {chapter_name}")
        
        # Load each spectrum
        for i, filename in enumerate(spectrum_files):
            if max_samples and i >= max_samples:
                break
                
            if i % 100 == 0:
                print(f"Loading spectrum {i+1}/{len(spectrum_files)}")
            
            try:
                # Parse filename for metadata
                metadata = self._parse_filename(str(filename))
                if not metadata:
                    print(f"Could not parse filename: {filename}")
                    continue
                
                # Add chapter information to metadata
                metadata['chapter'] = chapter_name
                
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
        
        return self.spectra

    def load_all_chapters(self, max_samples_per_chapter=None):
        """
        Load spectra from all available chapters
        
        Parameters:
        -----------
        max_samples_per_chapter : int or None
            Maximum number of samples to load per chapter (None for all)
            
        Returns:
        --------
        dict
            Dictionary of all loaded spectra
        """
        # Find all chapter directories
        chapter_dirs = [d for d in self.data_dir.iterdir() 
                    if d.is_dir() and d.name.startswith('Chapter')]
        
        print(f"Found {len(chapter_dirs)} chapters: {[d.name for d in chapter_dirs]}")
        
        for chapter_dir in sorted(chapter_dirs):
            try:
                print(f"\nLoading chapter: {chapter_dir.name}")
                self.load_chapter(chapter_dir.name, max_samples_per_chapter)
            except Exception as e:
                print(f"Error loading chapter {chapter_dir.name}: {str(e)}")
        
        return self.spectra