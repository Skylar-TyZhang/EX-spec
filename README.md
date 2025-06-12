# USGS Spectral Library Visualisation Tool

An interactive web application for exploring and visualising mineral spectral data from the USGS Spectral Library. This tool provides access to both satellite-resampled and full spectrum data with filtering and visualisation capabilities. The app is currently hosted on [Posit Cloud](https://connect.posit.cloud/skylar-tyzhang/content/0197561a-5093-a45b-d3bc-517663c301c9).

## Features

### Dual Data Type Support

- **Satellite Resampled Spectra**: Band-specific data for ASTER, Landsat8, Sentinel2, WorldView3
- **Full Spectrum Data**: High-resolution spectrometer measurements (BECK, ASD variants, NIC4, AVIRIS)

### Advanced Selection & Filtering

- Multiple mineral family selection
- Individual sample selection within selected mineral families
- Wavelength range filtering (0.2-25 μm) for full spectrum data
- Maximum samples per family control

### Interactive Visualisations

- Multi-mineral spectral plots with band overlays
- Satellite band response function visualisation
- Real-time plot updates
- Customisable display options (band centers, ranges, response functions)

### Data Export Capabilities

- Download plots as high-resolution PNG files (supported by plotly)
- Export spectral data as CSV files
- Band information table downloads

## Data Structure

The application expects the following USGS Spectral Library structure:

```{md}
ASCIIdata/
├── ASCIIdata_splib07b/          # Collection B - Interpolated spectra
│   └── ChapterM_Minerals/
├── ASCIIdata_splib07b_rsASTER/  # ASTER resampled data
├── ASCIIdata_splib07b_rsLandsat8/
├── ASCIIdata_splib07b_rsSentinel2/
└── ASCIIdata_splib07b_rsWorldView3/
```

## Usage Instructions

### Using the Interface

#### Satellite Resampled Spectra Tab

1. **Select Satellite Sensor**: Choose from ASTER, Landsat8, Sentinel2, or WorldView3
2. **Choose Mineral Families**: Select one or more mineral families from the dropdown (if you are using PC, press Ctrl to select multiple)
3. **Refine Selection**: Optionally select specific individual samples
4. **Adjust Display Options**: Toggle band centers, ranges, and response functions
5. **View Results**: Explore the spectral plots and band information

#### Full Spectrum Data Tab

1. **Choose Spectrometer**: Select from available spectrometers (BECK, ASD variants, etc.)
2. **Select Mineral Families**: Choose multiple families for comparison (if you are using PC, press Ctrl to select multiple)
3. **Set Wavelength Range**: Use the slider to focus on specific wavelength regions
4. **Analyse Data**: View high-resolution spectral data and export results

### Key Controls

| Control | Description |
|---------|-------------|
| **Mineral Families** | Multi-select dropdown for choosing mineral types |
| **Individual Samples** | Refined selection of specific samples |
| **Max Samples per Family** | Limit the number of samples displayed per family |
| **Wavelength Range** | Filter full spectrum data by wavelength (μm) |
| **Band Options** | Toggle display of band centers, ranges, and response functions |

## Application Structure

```
├── app.py                          # Main application file
├── requirements.txt                # Python dependencies
├── components/                     # UI components
│   ├── satellite_tab.py           # Satellite data interface
│   ├── full_spectrum_tab.py       # Full spectrum interface
│   ├── header.py                  # Application header
│   └── ui_tags_setup.py          # CSS styling
├── USGSSatelliteSpectra.py     # Satellite data handler
├── USGSSpectra.py                 # Full spectrum data handler
├── USGSUtils.py                   # Utility functions
├── USGSVisualisation.py           # Static visualisation functions using matplotlib
├── USGSPlotly.py           # Interactive visualisation functions using plotly
└── pickle_data/                   # Cached data files for better performance
   
```

### Supported Satellites:

- **ASTER**: Advanced Spaceborne Thermal Emission and Reflection Radiometer
- **Landsat8**: Operational Land Imager (OLI) and Thermal Infrared Sensor (TIRS)
- **Sentinel2**: MultiSpectral Instrument (MSI)
- **WorldView3**: High-resolution multispectral satellite

### Supported Spectrometers:

- **BECK**: Beckman 5270 (0.2-3.0 μm)
- **ASDFR**: ASD FieldSpec Standard Resolution (0.35-2.5 μm)
- **ASDHR**: ASD FieldSpec High Resolution (0.35-2.5 μm)
- **ASDNG**: ASD FieldSpec Next Generation (0.35-2.5 μm)
- **NIC4**: Nicolet FTIR (1.12-216 μm)
- **AVIRIS**: NASA AVIRIS Imaging Spectrometer (0.37-2.5 μm)

## Data Caching

The application automatically caches processed data in the `pickle_data/` directory:
- `S07{satellite}.pkl`: Cached satellite data
- `SPLIB07{collection}_data.pkl`: Cached full spectrum data

This improves loading times for subsequent uses.

## Performance Tips

1. **Memory Management**: Start with smaller sample sizes when exploring large datasets
2. **Wavelength Filtering**: Use wavelength range filtering to focus analysis and improve performance

This tool is valuable for:

- **Remote Sensing**: Satellite sensor analysis and band selection
- **Mineral Identification**: Spectral signature comparison and analysis
- **Geological Research**: Mineral composition studies
- **Sensor Calibration**: Understanding instrument response characteristics
- **Education**: Teaching spectroscopy and remote sensing concepts

## Data Sources

This application uses the **USGS Spectral Library Version 7** (splib07):

- Kokaly, R., Clark, R.N., Swayze, G.A., Livo, K.E., Hoefen, T.M., Pearson, N.C., Wise, R.A., Benzel, W.M., Lowers, H.A., Driscoll, R.L., and Klein, A.J., 2017, <i>USGS Spectral Library Version 7 Data</i>: U.S. Geological Survey data release, https://dx.doi.org/10.5066/F7RR1WDJ.

