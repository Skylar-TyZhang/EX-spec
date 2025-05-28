# USGS Spectral Library Shiny App - Project Structure

## Directory Structure

```{markdown}
usgs_spectral_app/
├── app.py                      # Main Shiny application
├── requirements.txt            # Python dependencies
├── README.md                  # Project documentation
├── config.py                  # Configuration settings
├── modules/
│   ├── __init__.py
│   ├── spectral_loader.py     # Modified USGS spectral library class
│   ├── data_processing.py     # Data processing utilities
│   └── plotting.py           # Plotting utilities
├── data/
│   └── cache/                # Cached data files
├── logs/
│   └── app.log              # Application logs
└── tests/
    ├── __init__.py
    ├── test_spectral_loader.py
    └── test_data_processing.py
```

## Key Features of the Shiny App

### 1. **Data Loading Panel**

- Directory selection for USGS Spectral Library
- Satellite sensor selection (ASTER, LSAT8, SNTL2, WV3)
- Progress indicators for data loading
- Cache management

### 2. **Spectral Analysis Dashboard**

- Interactive mineral family selection
- Spectrum visualisation  with band overlays
- Comparative analysis tools
- Band response function plots

### 3. **Export and Reporting**

- Export plots as PNG/PDF
- Generate spectral analysis reports
- Data export in CSV format

### 4. **Interactive Features**

- Real-time plot updates
- Zoom and pan capabilities
- Hover information
- Dynamic filtering

## File Descriptions

### `app.py`

Main Shiny application with UI and server logic, including:

- Sidebar for controls and settings
- Main panel with tabbed interface
- Reactive functions for data processing
- Plot rendering and updates

### `modules/spectral_loader.py`

Enhanced version of your USGSSatelliteSpectra class with:
- Caching mechanisms
- Progress reporting
- Error handling improvements
- Shiny-specific optimizations

### `modules/data_processing.py`

Data processing utilities including:

- Spectrum filtering and selection
- Statistical analysis functions
- Data validation and cleaning

### `modules/plotting.py`

Plotting utilities with:

- Interactive plot generation
- Consistent styling
- Export functionality
- Performance optimizations

### `config.py`

Configuration management:

- Default settings
- File paths
- Plotting parameters
- Cache settings

## Technology Stack

- **Shiny for Python**: Web application framework
- **Plotly**: Interactive plotting
- **Pandas**: Data manipulation
- **NumPy**: Numerical computing
- **Matplotlib**: Static plotting (fallback)
- **pathlib**: File system operations

## Installation and Setup

1. Create virtual environment
2. Install dependencies from requirements.txt
3. Configure data directory path
4. Run the Shiny app

## Usage Workflow

1. **Setup**: Select USGS data directory and satellite sensor
2. **Load Data**: Load mineral spectra and band response functions
3. **Explore**: Browse mineral families and individual spectra
4. **Analyze**: Compare spectra and examine band characteristics
5. **Export**: Save plots and generate reports