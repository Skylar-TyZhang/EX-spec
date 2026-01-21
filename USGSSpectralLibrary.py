import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import re
import glob
import html
from bs4 import BeautifulSoup
import pickle
from USGSUtils import USGSUtils

class USGSSpectralLibrary:
    def __init__(self, data_dir, library_version='splib07b', html_metadata_dir=None):
        """
        Initialise the USGS Spectral Library loader
        
        Parameters:
        -----------
        data_dir : str
            Path to the directory containing the USGS Spectral Library files
        library_version : str
            Version of the library (default: 'splib07b' for original measurements)
        html_metadata_dir : str, optional
            Path to the directory containing HTML metadata files
            If None, will look for HTMLmetadata directory relative to data_dir
        """
        self.data_dir = Path(data_dir)
        self.library_version = library_version
        self.prefix = f"{library_version}_" if library_version.startswith('splib') else f"s07{library_version}_"
        
        # Set up HTML metadata directory
        if html_metadata_dir:
            self.html_metadata_dir = Path(html_metadata_dir)
        else:
            # Try to find HTMLmetadata directory relative to data_dir
            # Common patterns: ../HTMLmetadata or ../../HTMLmetadata
            potential_paths = [
                self.data_dir.parent / "HTMLmetadata",
                self.data_dir.parent.parent / "HTMLmetadata",
                self.data_dir / "HTMLmetadata"
            ]
            self.html_metadata_dir = None
            for path in potential_paths:
                if path.exists():
                    self.html_metadata_dir = path
                    break
            
            if self.html_metadata_dir is None:
                print("Warning: HTML metadata directory not found. HTML metadata will not be loaded.")
        
        if self.html_metadata_dir:
            print(f"HTML metadata directory: {self.html_metadata_dir}")
        
        # Define chapter directories
        self.chapters = {
            'M': 'ChapterM_Minerals',
            'S': 'ChapterS_SoilsAndMixtures',
            'C': 'ChapterC_Coatings',
            'L': 'ChapterL_Liquids',
            'O': 'ChapterO_OrganicCompounds',
            'A': 'ChapterA_ArtificialMaterials',
            'V': 'ChapterV_Vegetation'
        }
        
        # Define spectrometer codes
        self.spectrometers = {
            'BECK': {'description': 'Beckman 5270', 'range': '0.2-3.0 μm'},
            'ASDFR': {'description': 'ASD Full Range standard resolution', 'range': '0.35-2.5 μm'},
            'ASDHR': {'description': 'ASD FS3 High Resolution', 'range': '0.35-2.5 μm'},
            'ASDNG': {'description': 'ASD FS4 Next Generation high resolution', 'range': '0.35-2.5 μm'},
            'AVIRIS': {'description': 'AVIRIS imaging spectrometer', 'range': '0.37-2.5 μm'},
            'NIC4': {'description': 'Nicolet FTIR interferometer', 'range': '1.12-216 μm'}
        }
        
        # Create indices for loaded data
        self.spectra = {}  # Dictionary to store all loaded spectra
        self.wavelengths = {}  # Dictionary to store wavelength data for each spectrometer
        self.bandpass = {}  # Dictionary to store bandpass data for each spectrometer
        self.metadata = {}  # Dictionary to store metadata for each sample
        
        # Initialize utility functions
        self.utils = USGSUtils(self.data_dir, self.prefix)
        
        # Load wavelength and bandpass data for spectrometers
        self._load_wavelength_data()
    
    def load_minerals_pickle(self, chapter='M', max_samples=None):
        """
        Load mineral spectra from pre-saved pickle files
        Legacy method - now calls load_all_chapters_pickle
        
        Parameters:
        -----------
        chapter : str
            Chapter to load ('M' for minerals)
        max_samples : int or None
            Maximum number of samples to load (None for all)
            
        Returns:
        --------
        dict
            Dictionary of loaded mineral spectra
        """
        return self.load_all_chapters_pickle(chapters=[chapter], max_samples_per_chapter=max_samples)
    
    def _load_wavelength_data(self):
        """Load wavelength and bandpass data for all spectrometers"""
        for spectrometer in self.spectrometers.keys():
            wavelength_file = list(self.data_dir.glob(f"{self.prefix}Wavelengths*_{spectrometer}*.txt"))
            bandpass_file = list(self.data_dir.glob(f"{self.prefix}Bandpass*_{spectrometer}*.txt"))
            
            if wavelength_file:
                self.wavelengths[spectrometer] = np.loadtxt(wavelength_file[0], skiprows=1)
                print(f"Loaded wavelength data for {spectrometer}: {len(self.wavelengths[spectrometer])} channels")
            
            if bandpass_file:
                self.bandpass[spectrometer] = np.loadtxt(bandpass_file[0], skiprows=1)
                print(f"Loaded bandpass data for {spectrometer}: {len(self.bandpass[spectrometer])} channels")
            # add wavelengths for ASDHR and ASDNG
            if spectrometer == 'ASDHR' or spectrometer == 'ASDNG':
                # Load the wavelengths for ASDHR and ASDNG from the same file
                if 'ASDFR' in self.wavelengths:
                    self.wavelengths[spectrometer] = self.wavelengths['ASDFR']
    
    def get_available_spectrometers(self):
        """
        Get list of available spectrometers from loaded spectra
        
        Returns:
        --------
        list
            List of available spectrometer names
        """
        if not self.spectra:
            return []
        
        spectrometers = set()
        for data in self.spectra.values():
            spectrometers.add(data['metadata']['spectrometer'])
        
        return sorted(list(spectrometers))
    
    def get_available_materials(self):
        """
        Get list of available materials from loaded spectra
        
        Returns:
        --------
        list
            List of available material names
        """
        if not self.spectra:
            return []
        
        materials = set()
        for data in self.spectra.values():
            materials.add(data['metadata']['material'])
        
        return sorted(list(materials))
    
    def filter_spectra(self, spectrometer=None, materials=None, wavelength_range=None):
        """
        Filter loaded spectra based on criteria
        
        Parameters:
        -----------
        spectrometer : str, optional
            Spectrometer to filter by
        materials : list, optional
            List of materials to include
        wavelength_range : tuple, optional
            (min_wavelength, max_wavelength) in microns
        
        Returns:
        --------
        dict
            Filtered spectra dictionary
        """
        if not self.spectra:
            return {}
        
        filtered = {}
        
        for key, data in self.spectra.items():
            metadata = data['metadata']
            
            # Filter by spectrometer
            if spectrometer and metadata['spectrometer'] != spectrometer:
                continue
            
            # Filter by materials
            if materials and metadata['material'] not in materials:
                continue
            
            # Filter by wavelength range
            if wavelength_range:
                wavelengths = data['wavelength']
                if (wavelengths.min() > wavelength_range[1] or 
                    wavelengths.max() < wavelength_range[0]):
                    continue
            
            filtered[key] = data
        
        return filtered
    
    def _parse_filename(self, filename):
        """
        Parse the filename to extract sample information
        
        Pattern: prefix_material_sampleID_spectrometersettings.txt
        Example: splib07a_Acmite_NMNH133746_BECKa_AREF.txt
        """
        basename = os.path.basename(filename)
        # Remove the prefix and file extension
        parts = basename.replace(self.prefix, '').replace('.txt', '').split('_')
        
        if len(parts) < 3:
            return None
        
        # Extract spectrometer and purity code
        spec_code = parts[-2]
        # Match spectrometer code with regex to handle cases like BECKa, NIC4ccc, etc.
        spec_match = re.match(r'([A-Z]+[0-9]*)([a-z]+)', spec_code)
        
        if not spec_match:
            return None
            
        spectrometer = spec_match.group(1)
        purity = spec_match.group(2)
        
        # Extract material and sample ID
        material = parts[0]
        sample_id = '_'.join(parts[1:-2])  # Join all parts between material and spectrometer code
        
        # Extract measurement type (AREF, RREF, etc.)
        measurement_type = parts[-1]
        
        return {
            'material': material,
            'sample_id': sample_id,
            'spectrometer': spectrometer,
            'purity': purity,
            'measurement_type': measurement_type,
            'filename': basename,
            #'full_path': filename
        }
    
    def _find_html_metadata_file(self, spectrum_key):
        """
        Find the corresponding HTML metadata file for a spectrum
        
        Parameters:
        -----------
        spectrum_key : str
            Spectrum key (e.g., 'Acmite_NMNH133746_BECKa_AREF')
        
        Returns:
        --------
        str or None
            Path to HTML file if found, None otherwise
        """
        if not self.html_metadata_dir:
            return None
        
        html_filename = f"{spectrum_key}.html"
        html_path = self.html_metadata_dir / html_filename
        
        if html_path.exists():
            return str(html_path)
        return None
    
    def _parse_metadata_html_enhanced(self, html_content):
        """
        Enhanced HTML metadata parser focusing on formula, grainsize, and other key fields
        
        Parameters:
        -----------
        html_content : str
            HTML content as string
        
        Returns:
        --------
        dict
            Dictionary containing extracted metadata
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            metadata = {}
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text content
            text = soup.get_text()
            
            # Field patterns focusing on the requested fields plus some useful ones
            field_patterns = {
                # Primary requested fields
                'FORMULA': r'FORMULA:\s*(.+?)(?:\n|$)',
                'PARTICLE_SIZE': r'PARTICLE_SIZE:\s*(.+?)(?:\n|$)',
                'GRAIN_SIZE': r'GRAIN_SIZE:\s*(.+?)(?:\n|$)',
                
                # Additional useful fields
                'MINERAL_TYPE': r'MINERAL_TYPE:\s*(.+?)(?:\n|$)',
                'MINERAL': r'MINERAL:\s*(.+?)(?:\n|$)',
                'COLLECTION_LOCALITY': r'COLLECTION_LOCALITY:\s*(.+?)(?:\n|$)',
                'SAMPLE_DESCRIPTION': r'SAMPLE_DESCRIPTION:\s*(.+?)(?:\n|$)',
                'SPECTRAL_PURITY': r'SPECTRAL_PURITY:\s*(.+?)(?:\n|$)',
                'SPECTRAL_PURITY_DETAILS': r'SPECTRAL_PURITY_DETAILS:\s*(.+?)(?:\n|$)',
                # 'SAMPLE_ID': r'SAMPLE_ID:\s*(.+?)(?:\n|$)',
                # 'ORIGINAL_SAMPLE_ID': r'ORIGINAL_SAMPLE_ID:\s*(.+?)(?:\n|$)',
                # 'MUSEUM_SAMPLE_ID': r'MUSEUM_SAMPLE_ID:\s*(.+?)(?:\n|$)',
                'COLOR': r'COLOR:\s*(.+?)(?:\n|$)',
                'TEXTURE': r'TEXTURE:\s*(.+?)(?:\n|$)',
                'CRYSTAL_SYSTEM': r'CRYSTAL_SYSTEM:\s*(.+?)(?:\n|$)',
                'COLLECTOR': r'COLLECTOR:\s*(.+?)(?:\n|$)',
                'COLLECTION_DATE': r'COLLECTION_DATE:\s*(.+?)(?:\n|$)',
                'INSTITUTION': r'INSTITUTION:\s*(.+?)(?:\n|$)',
                'COUNTRY': r'COUNTRY:\s*(.+?)(?:\n|$)',
                'STATE_PROVINCE': r'STATE_PROVINCE:\s*(.+?)(?:\n|$)',
            }
            
            # Extract fields using regex patterns
            for field, pattern in field_patterns.items():
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    value = match.group(1).strip()
                    if value and value.lower() not in ['n/a', 'not available', 'none', '']:
                        metadata[field.lower()] = value
            
            # Handle grainsize/particle_size unification
            # USGS might use either PARTICLE_SIZE or GRAIN_SIZE
            if 'particle_size' in metadata and 'grain_size' not in metadata:
                metadata['grain_size'] = metadata['particle_size']
            elif 'grain_size' in metadata and 'particle_size' not in metadata:
                metadata['particle_size'] = metadata['grain_size']
            
            # Try to extract tabular data if present
            tables = soup.find_all('table')
            if tables:
                for table in tables:
                    rows = table.find_all('tr')
                    for row in rows:
                        cells = row.find_all(['td', 'th'])
                        if len(cells) >= 2:
                            key = cells[0].get_text().strip().lower().replace(' ', '_')
                            value = cells[1].get_text().strip()
                            if key and value and value.lower() not in ['n/a', 'not available', 'none', '']:
                                # Only add if we don't already have this field
                                if key not in metadata:
                                    metadata[key] = value
            
            # Clean up metadata values
            for key, value in metadata.items():
                if isinstance(value, str):
                    # Remove excessive whitespace
                    value = re.sub(r'\s+', ' ', value.strip())
                    # Remove common formatting artifacts
                    value = value.replace('\t', ' ').replace('\r', '')
                    metadata[key] = value
            
            return metadata
            
        except Exception as e:
            print(f"Error parsing HTML metadata: {str(e)}")
            return {'parsing_error': str(e)}
    
    def load_spectrum(self, filename):
        """
        Load a single spectrum from a file
        
        Parameters:
        -----------
        filename : str
            Path to the spectrum file
        
        Returns:
        --------
        dict
            Dictionary containing spectrum data and metadata
        """
        try:
            # Parse filename for metadata
            metadata = self._parse_filename(filename)
            if metadata is None:
                print(f"Could not parse filename: {filename}")
                return None
                
            # Load spectrum data skipping the first row (header)
            spectrum = np.loadtxt(filename, skiprows=1)
            
            # Replace deleted channels with NaN
            spectrum[spectrum < -1e30] = np.nan
            
            # Get wavelength data for this spectrometer
            if metadata['spectrometer'] in self.wavelengths:
                wavelength = self.wavelengths[metadata['spectrometer']]
                if len(wavelength) != len(spectrum):
                    print(f"Warning: Wavelength length ({len(wavelength)}) doesn't match spectrum length ({len(spectrum)})")
                    # Truncate to the shorter length
                    min_length = min(len(wavelength), len(spectrum))
                    wavelength = wavelength[:min_length]
                    spectrum = spectrum[:min_length]
            else:
                print(f"Warning: No wavelength data for spectrometer {metadata['spectrometer']}")
                wavelength = np.arange(len(spectrum))
            
            # Create spectrum key for HTML metadata lookup
            spectrum_key = f"{metadata['material']}_{metadata['sample_id']}_{metadata['spectrometer']}{metadata['purity']}_{metadata['measurement_type']}"
            
            # Try to find and load the enhanced HTML metadata
            html_path = self._find_html_metadata_file(spectrum_key)
            if html_path:
                try:
                    with open(html_path, 'r', encoding='utf-8') as f:
                        html_content = f.read()
                    
                    # Parse enhanced metadata
                    html_metadata = self._parse_metadata_html_enhanced(html_content)
                    
                    # Add HTML file path to metadata
                    html_metadata['html_file_path'] = html_path
                    
                    # Merge HTML metadata with existing metadata
                    metadata.update(html_metadata)
                    
                except Exception as e:
                    print(f"Error loading HTML metadata from {html_path}: {str(e)}")
                    metadata['html_error'] = str(e)
            else:
                # Try the old method for backward compatibility
                html_file = filename.replace('.txt', '.html')
                if os.path.exists(html_file):
                    try:
                        with open(html_file, 'r', encoding='utf-8') as f:
                            html_content = f.read()
                        metadata['html'] = html_content
                        # Add basic parsing
                        html_metadata = self._parse_metadata_html_enhanced(html_content)
                        html_metadata['html_file_path'] = html_file
                        metadata.update(html_metadata)
                    except Exception as e:
                        print(f"Error loading HTML metadata from {html_file}: {str(e)}")
                        metadata['html_error'] = str(e)
            
            result = {
                'metadata': metadata,
                'spectrum': spectrum,
                'wavelength': wavelength
            }
            
            # If bandpass data is available, include it
            if metadata['spectrometer'] in self.bandpass:
                bandpass = self.bandpass[metadata['spectrometer']]
                if len(bandpass) != len(spectrum):
                    min_length = min(len(bandpass), len(spectrum))
                    bandpass = bandpass[:min_length]
                result['bandpass'] = bandpass
            
            return result
            
        except Exception as e:
            print(f"Error loading spectrum {filename}: {str(e)}")
            return None
    
    def load_chapter(self, chapter, spectrometers=None, max_samples=None):
        """
        Load all spectra from a specific chapter
        
        Parameters:
        -----------
        chapter : str
            Chapter code (M, S, C, L, O, A, V)
        spectrometers : list
            List of spectrometer codes to include (default: all)
        max_samples : int
            Maximum number of samples to load (default: all)
        
        Returns:
        --------
        dict
            Dictionary containing all loaded spectra from the chapter
        """
        if chapter not in self.chapters:
            print(f"Unknown chapter: {chapter}")
            return {}
            
        chapter_dir = self.data_dir / self.chapters[chapter]
        if not chapter_dir.exists():
            print(f"Chapter directory not found: {chapter_dir}")
            return {}
        
        # Find all spectrum files in the chapter directory
        spectrum_files = list(chapter_dir.glob(f"{self.prefix}*.txt"))
        
        if max_samples and max_samples < len(spectrum_files):
            spectrum_files = spectrum_files[:max_samples]
            
        print(f"Found {len(spectrum_files)} spectra in chapter {chapter}")
        
        # Load each spectrum
        chapter_spectra = {}
        for i, filename in enumerate(spectrum_files):
            # Show progress
            if i % 100 == 0:
                print(f"Loading spectrum {i+1}/{len(spectrum_files)}")
                
            spectrum_data = self.load_spectrum(str(filename))
            if spectrum_data:
                metadata = spectrum_data['metadata']
                
                # Skip if spectrometer filter is active and this doesn't match
                if spectrometers and metadata['spectrometer'] not in spectrometers:
                    continue
                if metadata:
                    metadata['chapter'] = self.chapters[chapter].split('_')[1]  # Add chapter info to metadata
                    
                # Create a unique key for this spectrum
                key = f"{metadata['material']}_{metadata['sample_id']}_{metadata['spectrometer']}{metadata['purity']}_{metadata['measurement_type']}"
                chapter_spectra[key] = spectrum_data
        
        print(f"Loaded {len(chapter_spectra)} spectra from chapter {chapter}")
        return chapter_spectra
    
    def load_all_chapters_pickle(self, chapters=['M'], max_samples_per_chapter=None):
        """
        Load full spectrum data from multiple chapters with proper pickle handling
        
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
        
        for chapter in chapters:
            if chapter not in self.chapters:
                print(f"Unknown chapter: {chapter}, skipping...")
                continue
            
            chapter_dir_name = self.chapters[chapter]
            pickle_file = f'pickle_data/{self.prefix}{chapter}_data.pkl'
            
            print(f"\n{'='*60}")
            print(f"Processing Chapter {chapter}: {chapter_dir_name}")
            print(f"{'='*60}")
            
            # Try to load from pickle first
            try:
                with open(pickle_file, 'rb') as f:
                    chapter_spectra = pickle.load(f)
                print(f"Loaded {len(chapter_spectra)} spectra from pickle: {pickle_file}")
                
            except FileNotFoundError:
                print(f"Pickle file not found: {pickle_file}")
                print(f"Loading from ASCII files...")
                
                # Load from ASCII files
                chapter_spectra = self.load_chapter(chapter, max_samples=max_samples_per_chapter)
                
                if chapter_spectra:
                    # Save to pickle for future use
                    try:
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
                
                chapter_spectra = self.load_chapter(chapter, max_samples=max_samples_per_chapter)
                
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
                if 'metadata' in spectrum_data:
                    spectrum_data['metadata']['chapter'] = chapter_dir_name.split('_')[1]
                # Add chapter prefix to key to avoid conflicts between chapters
                unique_key = f"{chapter}_{key}"
                all_spectra[unique_key] = spectrum_data
        
        self.spectra = all_spectra
        print(f"\n{'='*60}")
        print(f"Total loaded: {len(all_spectra)} spectra from {len(chapters)} chapters")
        print(f"{'='*60}\n")
        
        return all_spectra

    # Update the original method to use the new one
    def load_minerals_pickle(self, chapter='M', max_samples=None):
        """
        Load mineral spectra from pre-saved pickle files
        Legacy method - now calls load_all_chapters_pickle
        
        Parameters:
        -----------
        chapter : str
            Chapter to load ('M' for minerals)
        max_samples : int or None
            Maximum number of samples to load (None for all)
            
        Returns:
        --------
        dict
            Dictionary of loaded mineral spectra
        """
        return self.load_all_chapters_pickle(chapters=[chapter], max_samples_per_chapter=max_samples)
    
    def search_spectra(self, query, fields=None):
        """
        Search for spectra matching a query string
        
        Parameters:
        -----------
        query : str
            Search query (case-insensitive)
        fields : list
            List of metadata fields to search in (default: material, sample_id)
        
        Returns:
        --------
        dict
            Dictionary of spectra matching the query
        """
        if not fields:
            fields = ['material', 'sample_id']
            
        query = query.lower()
        results = {}
        
        for key, data in self.spectra.items():
            metadata = data['metadata']
            
            # Check if any field matches the query
            match = False
            for field in fields:
                if field in metadata and query in str(metadata[field]).lower():
                    match = True
                    break
                    
            if match:
                results[key] = data
                
        print(f"Found {len(results)} spectra matching '{query}'")
        return results
    
    def get_metadata_summary(self):
        """
        Get a summary of available metadata fields across all loaded spectra
        
        Returns:
        --------
        pandas.DataFrame
            DataFrame showing metadata field coverage
        """
        if not self.spectra:
            print("No spectra loaded. Load some spectra first.")
            return pd.DataFrame()
        
        field_counts = {}
        total_spectra = len(self.spectra)
        
        for key, data in self.spectra.items():
            metadata = data['metadata']
            for field in metadata.keys():
                if field not in field_counts:
                    field_counts[field] = 0
                field_counts[field] += 1
        
        summary_data = []
        for field, count in sorted(field_counts.items()):
            summary_data.append({
                'field': field,
                'count': count,
                'coverage_percent': (count / total_spectra) * 100
            })
        
        summary_df = pd.DataFrame(summary_data)
        summary_df = summary_df.sort_values('coverage_percent', ascending=False)
        
        return summary_df
    
    def resample_spectrum(self, spectrum_data, target_wavelengths):
        """
        Resample a spectrum to a different set of wavelengths
        
        Parameters:
        -----------
        spectrum_data : dict
            Spectrum data dictionary
        target_wavelengths : array-like
            Target wavelength positions
            
        Returns:
        --------
        array-like
            Resampled spectrum values
        """
        from scipy.interpolate import interp1d
        
        # Get spectrum and wavelength data
        spectrum = spectrum_data['spectrum']
        wavelength = spectrum_data['wavelength']
        
        # Remove NaN values for interpolation
        valid_idx = ~np.isnan(spectrum)
        if np.sum(valid_idx) < 2:
            print("Warning: Too few valid points for interpolation")
            return np.full_like(target_wavelengths, np.nan)
            
        # Restrict target wavelengths to the range of the source spectrum
        valid_targets = (target_wavelengths >= np.min(wavelength[valid_idx])) & \
                        (target_wavelengths <= np.max(wavelength[valid_idx]))
                        
        # If no valid target wavelengths, return NaN
        if np.sum(valid_targets) == 0:
            print("Warning: No valid target wavelengths in range")
            return np.full_like(target_wavelengths, np.nan)
            
        # Create interpolation function
        f = interp1d(wavelength[valid_idx], spectrum[valid_idx], 
                     kind='linear', bounds_error=False, fill_value=np.nan)
                     
        # Apply interpolation to target wavelengths
        resampled = f(target_wavelengths)
        
        return resampled
        
    def export_to_dataframe(self, spectra_dict):
        """
        Export spectra to a pandas DataFrame
        
        Parameters:
        -----------
        spectra_dict : dict
            Dictionary of spectra as returned by load_chapter or search_spectra
            
        Returns:
        --------
        pandas.DataFrame
            DataFrame containing the spectra and metadata
        """
        # Create list to hold records
        records = []
        
        for key, data in spectra_dict.items():
            # Extract metadata
            metadata = data['metadata']
            
            # Create a record for this spectrum
            record = {
                'key': key,
                'material': metadata.get('material', ''),
                'sample_id': metadata.get('sample_id', ''),
                'spectrometer': metadata.get('spectrometer', ''),
                'purity': metadata.get('purity', ''),
                'measurement_type': metadata.get('measurement_type', ''),
                'formula': metadata.get('formula', ''),
                'grain_size': metadata.get('grain_size', ''),
                'particle_size': metadata.get('particle_size', ''),
                'html_file_path': metadata.get('html_file_path', ''),
                'min_wavelength': np.nanmin(data['wavelength']),
                'max_wavelength': np.nanmax(data['wavelength']),
                'num_channels': len(data['spectrum']),
                'spectrum': data['spectrum'],
                'wavelength': data['wavelength']
            }
            
            # Add any additional metadata
            for k, v in metadata.items():
                if k not in record and k != 'html':
                    record[k] = v
                    
            records.append(record)
            
        # Create DataFrame
        df = pd.DataFrame(records)
        return df