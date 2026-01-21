import plotly.graph_objects as go
import plotly.subplots as sp
from plotly.subplots import make_subplots
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional
from atmospheric_transmission import AtmosphericTransmission

class PlotlyUSGSVisualiser:
    """Enhanced visualization class using Plotly for interactive spectral analysis"""
    
    def __init__(self):
        self.default_colors = [
            '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
            '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
        ]
        
    def create_satellite_spectra_plot(self, lib_obj, selected_keys: List[str], 
                                    show_band_centers: bool = True,
                                    show_band_ranges: bool = True,
                                    show_response_functions: bool = True,
                                    show_atmospheric_transmission: bool = False,
                                    height: int = 700) -> go.Figure:
        """
        Create interactive satellite spectra plot with band information
        
        Parameters:
        -----------
        lib_obj : USGSSatelliteSpectra
            Satellite spectral library object
        selected_keys : List[str]
            List of spectrum keys to plot
        show_band_centers : bool
            Show vertical lines at band centers
        show_band_ranges : bool
            Show shaded regions for band ranges
        show_response_functions : bool
            Show band response functions subplot
        show_atmospheric_transmission : bool
            Show atmospheric transmission overlay
        height : int
            Total figure height in pixels
            
        Returns:
        --------
        plotly.graph_objects.Figure
            Interactive Plotly figure
        """
        
        # Determine subplot configuration
        if show_response_functions and lib_obj.bands:
            fig = make_subplots(
                rows=2, cols=1,
                row_heights=[0.7, 0.3],
                subplot_titles=[
                    " ",
                    f"{lib_obj.satellite} Band Response Functions"
                ],
                vertical_spacing=0.08,
                shared_xaxes=True,
                specs=[[{"secondary_y": True}], [{"secondary_y": False}]]  # Enable secondary y-axis for top subplot
            )
            response_row = 2
        else:
            fig = make_subplots(specs=[[{"secondary_y": True}]])  # Enable secondary y-axis for single plot
            response_row = None
        
        # Add atmospheric transmission first (background layer)
        if show_atmospheric_transmission:
            self._add_atmospheric_transmission(fig, lib_obj.wavelengths, subplot_row=1 if response_row else None)
        
        # Plot mineral spectra 
        for i, key in enumerate(selected_keys):
            if key in lib_obj.spectra:
                spectrum = lib_obj.spectra[key]['spectrum']
                metadata = lib_obj.spectra[key]['metadata']
                
                # Create hover text with detailed information
                hover_text = [
                    #f"Wavelength: {wl:.3f} μm<br>"
                    f"Reflectance: {refl:.4f}<br>"
                    #f"Material: {metadata['material']}<br>"
                    #f"Sample: {metadata['sample_id']}<br>"
                    #f"Type: {metadata['measurement_type']}"
                    for wl, refl in zip(lib_obj.wavelengths, spectrum)
                ]
                
                color = self.default_colors[i % len(self.default_colors)]
                
                trace = go.Scatter(
                    x=lib_obj.wavelengths,
                    y=spectrum,
                    mode='lines+markers',
                    name=f"{metadata['material']} {metadata['sample_id']}",
                    line=dict(color=color, width=2),
                    marker=dict(size=4, color=color),
                    hovertext=hover_text,
                    hoverinfo='text',
                    legendgroup='spectra',
                    showlegend=True
                )
                
                if response_row:
                    fig.add_trace(trace, row=1, col=1)
                else:
                    fig.add_trace(trace)
        
        # Get wavelength range for consistent x-axis
        if lib_obj.wavelengths is not None:
            x_range = [lib_obj.wavelengths.min(), lib_obj.wavelengths.max()]
        
        # Add band information with consistent colors
        if lib_obj.bands and lib_obj.wavelengths is not None:
            self._add_band_overlays(fig, lib_obj, show_band_centers, show_band_ranges, 
                                  subplot_row=1 if response_row else None)
        
        # Add band response functions with matching colors
        if show_response_functions and response_row and lib_obj.bands:
            self._add_band_response_functions(fig, lib_obj, response_row)
            
            # Ensure x-axis range matches between main plot and response functions
            fig.update_xaxes(range=x_range, row=1, col=1)
            fig.update_xaxes(range=x_range, row=2, col=1)
        
        # Update layout
        self._update_satellite_layout(fig, lib_obj, height, response_row is not None)
        
        return fig
    
    def create_full_spectrum_plot(self, lib_obj, selected_keys: List[str],
                                    wavelength_range: Optional[Tuple[float, float]] = None,
                                    show_atmospheric_transmission: bool = False,
                                    height: int = 600) -> go.Figure:
            """
            Create interactive full spectrum plot with wavelength filtering
            Updated to work with USGSSpectralLibrary structure
            
            Parameters:
            -----------
            lib_obj : USGSSpectralLibrary
                Full spectrum library object
            selected_keys : List[str]
                List of spectrum keys to plot
            wavelength_range : Tuple[float, float], optional
                Wavelength range (min, max) in microns
            show_atmospheric_transmission : bool
                Show atmospheric transmission overlay
            height : int
                Figure height in pixels
                
            Returns:
            --------
            plotly.graph_objects.Figure
                Interactive Plotly figure
            """
            
            fig = make_subplots(specs=[[{"secondary_y": True}]])  # Enable secondary y-axis
            
            # Determine wavelength range for atmospheric data
            if selected_keys and lib_obj.spectra:
                # Get wavelength range from first spectrum
                first_key = selected_keys[0]
                if first_key in lib_obj.spectra:
                    plot_wavelengths = lib_obj.spectra[first_key]['wavelength']
                    if wavelength_range:
                        mask = (plot_wavelengths >= wavelength_range[0]) & (plot_wavelengths <= wavelength_range[1])
                        plot_wavelengths = plot_wavelengths[mask]
                else:
                    plot_wavelengths = np.linspace(0.4, 2.5, 1000)
            else:
                plot_wavelengths = np.linspace(0.4, 2.5, 1000)
            
            # Add atmospheric transmission first (background layer)
            if show_atmospheric_transmission:
                self._add_atmospheric_transmission(fig, plot_wavelengths)
                
            for i, key in enumerate(selected_keys):
                if key in lib_obj.spectra:
                    data = lib_obj.spectra[key]
                    spectrum = data['spectrum']
                    metadata = data['metadata']
                    wavelengths = data['wavelength']
                    
                    # Apply wavelength filtering
                    if wavelength_range:
                        mask = (wavelengths >= wavelength_range[0]) & (wavelengths <= wavelength_range[1])
                        wavelengths = wavelengths[mask]
                        spectrum = spectrum[mask]
                    
                    # Create detailed hover information
                    hover_text = [
                        f"Wavelength: {wl:.3f} μm<br>"
                        f"Value: {val:.4f}<br>"
                        f"Material: {metadata['material']}<br>"
                        f"Sample: {metadata.get('sample_id', 'N/A')}<br>"
                        #f"Spectrometer: {metadata['spectrometer']}<br>"
                        #f"Type: {metadata['measurement_type']}"
                        for wl, val in zip(wavelengths, spectrum)
                    ]
                    
                    color = self.default_colors[i % len(self.default_colors)]
                    
                    # Add spectrum trace 
                    fig.add_trace(
                        go.Scatter(
                            x=wavelengths,
                            y=spectrum,
                            mode='lines',
                            name=f"{metadata['material']} {metadata.get('sample_id', 'N/A')}",
                            line=dict(color=color, width=2),
                            hovertext=hover_text,
                            hoverinfo='text',
                            connectgaps=False,  # Don't connect across NaN values
                            showlegend=True  
                        )
                    )
            
            # Update layout for full spectrum
            self._update_full_spectrum_layout(fig, lib_obj, height, wavelength_range)
            
            return fig
    
    def create_band_response_plot(self, lib_obj, height: int = 500) -> go.Figure:
        """
        Create detailed band response function plot
        
        Parameters:
        -----------
        lib_obj : USGSSatelliteSpectra
            Satellite library object
        height : int
            Figure height in pixels
            
        Returns:
        --------
        plotly.graph_objects.Figure
            Interactive Plotly figure
        """
        
        if not lib_obj.bands or lib_obj.wavelengths_hp is None:
            # Return empty figure with message
            fig = go.Figure()
            fig.add_annotation(
                text="No band response data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16, color="gray")
            )
            return fig
        
        # Calculate subplot dimensions
        sorted_bands = sorted(lib_obj.bands.items())
        num_bands = len(sorted_bands)
        cols = min(3, num_bands)
        rows = (num_bands + cols - 1) // cols
        
        # Create subplots
        subplot_titles = [f"Band {band_num}: {band_info['band_name']}" 
                         for band_num, band_info in sorted_bands]
        
        fig = make_subplots(
            rows=rows, cols=cols,
            subplot_titles=subplot_titles,
            vertical_spacing=0.08,
            horizontal_spacing=0.06
        )
        
        # Plot each band
        for i, (band_num, band_info) in enumerate(sorted_bands):
            row = (i // cols) + 1
            col = (i % cols) + 1
            
            response = band_info['response']
            wavelengths_band = band_info['wavelengths']
            
            # Ensure equal lengths
            min_len = min(len(wavelengths_band), len(response))
            wavelengths_band = wavelengths_band[:min_len]
            response = response[:min_len]
            
            # Calculate statistics for hover
            peak_idx = np.argmax(response)
            peak_wavelength = wavelengths_band[peak_idx]
            peak_response = response[peak_idx]
            
            hover_text = [
                f"Wavelength: {wl:.3f} μm<br>"
                f"Response: {resp:.4f}<br>"
                f"Band: {band_info['band_name']}<br>"
                f"Peak: {peak_wavelength:.3f} μm"
                for wl, resp in zip(wavelengths_band, response)
            ]
            
            color = self.default_colors[i % len(self.default_colors)]
            
            # Add filled area
            fig.add_trace(
                go.Scatter(
                    x=wavelengths_band,
                    y=response,
                    mode='lines',
                    fill='tozeroy',
                    name=f"Band {band_num}",
                    line=dict(color=color, width=2),
                    fillcolor=f"rgba{tuple(list(int(color[i:i+2], 16) for i in (1, 3, 5)) + [0.3])}",
                    hovertext=hover_text,
                    hoverinfo='text',
                    showlegend=False
                ),
                row=row, col=col
            )
            
            # Add peak marker
            fig.add_trace(
                go.Scatter(
                    x=[peak_wavelength],
                    y=[peak_response],
                    mode='markers',
                    marker=dict(color='red', size=8, symbol='star'),
                    name=f"Peak {band_num}",
                    hovertext=f"Peak: {peak_wavelength:.3f} μm, {peak_response:.4f}",
                    hoverinfo='text',
                    showlegend=False
                ),
                row=row, col=col
            )
        
        # Update layout
        fig.update_layout(
            title=f"{lib_obj.satellite} Band Response Functions",
            height=height,
            showlegend=True,
            hovermode='closest'
        )
        
        # Update all x and y axes
        fig.update_xaxes(title_text="Wavelength (μm)", showgrid=True, gridcolor='lightgray')
        fig.update_yaxes(title_text="Response", showgrid=True, gridcolor='lightgray')
        
        return fig
    
    def _add_band_overlays(self, fig: go.Figure, lib_obj, show_centers: bool, 
                          show_ranges: bool, subplot_row: Optional[int] = None):
        """Add band center lines and range overlays to existing plot"""
        
        if not lib_obj.bands or lib_obj.wavelengths is None:
            return
        
        sorted_bands = lib_obj.bands.items()
        band_colors = self.default_colors
        
        for i, (band_num, band_info) in enumerate(sorted_bands):
            band_num_int = int(''.join([char for char in band_num if char.isdigit()]))
            
            if band_num_int <= len(lib_obj.wavelengths):
                band_center = lib_obj.wavelengths[band_num_int - 1]
                color = band_colors[i % len(band_colors)]
                
                # Add band center line
                if show_centers:
                    fig.add_vline(
                        x=band_center,
                        line=dict(color=color, width=2, dash="dash"),
                        annotation_text=f"{band_info['band_name']}",
                        annotation_position="top",
                        row=subplot_row, col=1 if subplot_row else None
                    )
                
                # Add band range
                if show_ranges and lib_obj.bandpass_micron is not None and band_num_int <= len(lib_obj.bandpass_micron):
                    bandpass = lib_obj.bandpass_micron[band_num_int - 1]
                    band_min = band_center - bandpass / 2
                    band_max = band_center + bandpass / 2
                    
                    fig.add_vrect(
                        x0=band_min, x1=band_max,
                        fillcolor=color,
                        opacity=0.2,
                        line_width=0,
                        row=subplot_row, col=1 if subplot_row else None
                    )
    
    def _add_band_response_functions(self, fig: go.Figure, lib_obj, row: int):
        """Add band response functions to subplot"""
        
        sorted_bands = sorted(lib_obj.bands.items())
        
        for i, (band_num, band_info) in enumerate(sorted_bands):
            response = band_info['response']
            wavelengths_band = band_info['wavelengths']
            
            min_len = min(len(wavelengths_band), len(response))
            wavelengths_band = wavelengths_band[:min_len]
            response = response[:min_len]
            
            color = self.default_colors[i % len(self.default_colors)]
            
            fig.add_trace(
                go.Scatter(
                    x=wavelengths_band,
                    y=response,
                    mode='lines',
                    fill='tozeroy',
                    name=f"Band {band_num}",
                    line=dict(color=color, width=1),
                    fillcolor=f"rgba{tuple(list(int(color[i:i+2], 16) for i in (1, 3, 5)) + [0.4])}",
                    legendgroup='bands',
                    showlegend=False,
                    hovertemplate=f"<b>{band_info['band_name']}</b><br>" +
                                "Wavelength: %{x:.3f} μm<br>" +
                                "Response: %{y:.4f}<extra></extra>"
                ),
                row=row, col=1
            )
    
    def _update_satellite_layout(self, fig: go.Figure, lib_obj, height: int, has_subplots: bool):
        """Update layout for satellite plots"""
        
        fig.update_layout(
            title=f"{lib_obj.satellite} Satellite Spectral Analysis",
            height=height,
            hovermode='x unified',
            showlegend=True,  
            margin=dict(t=100, b=50, l=50, r=100)  # Right margin for secondary y-axis
        )
        
        # Update x and y axes
        if has_subplots:
            fig.update_xaxes(title_text="Wavelength (μm)", row=2, col=1, showgrid=True)
            fig.update_yaxes(title_text="Reflectance", row=1, col=1, showgrid=True)
            fig.update_yaxes(title_text="Response", row=2, col=1, showgrid=True)
        else:
            fig.update_xaxes(title_text="Wavelength (μm)", showgrid=True)
            fig.update_yaxes(title_text="Reflectance", showgrid=True)
        
        # Add crosshair cursor
        fig.update_layout(
            hoverlabel=dict(
                bgcolor="white",
                font_size=12,
                font_family="Arial"
            )
        )
    
    def _update_full_spectrum_layout(self, fig: go.Figure, lib_obj, height: int, 
                                   wavelength_range: Optional[Tuple[float, float]]):
        """Update layout for full spectrum plots"""
        
        range_text = ""
        if wavelength_range:
            range_text = f" ({wavelength_range[0]:.1f}-{wavelength_range[1]:.1f} μm)"
        
        fig.update_layout(
            title=f"Full Spectrum Analysis{range_text}",
            height=height,
            hovermode='x unified',
            showlegend=True,  
            margin=dict(t=80, b=50, l=50, r=100)  # Right margin for secondary y-axis
        )
        
        fig.update_xaxes(
            title_text="Wavelength (μm)",
            showgrid=True,
            gridcolor='lightgray',
            zeroline=False
        )
        
        fig.update_yaxes(
            title_text="Reflectance / Transmission",
            showgrid=True,
            gridcolor='lightgray',
            zeroline=False
        )
        
        # Enhanced hover behavior
        fig.update_layout(
            hoverlabel=dict(
                bgcolor="rgba(255,255,255,0.9)",
                font_size=11,
                font_family="Arial",
                bordercolor="gray"
            )
        )

    def _add_atmospheric_transmission(self, fig: go.Figure, wavelengths, subplot_row: Optional[int] = None):
        """Add atmospheric transmission overlay to the plot"""
        # Global instance for easy access
        atmospheric_data = AtmosphericTransmission(data_file_path="data/Atmos_constits.xls")
        if not atmospheric_data.data_loaded:
            print("Atmospheric data not loaded.")
            return
        
        # Get atmospheric transmission data for the wavelength range
        wl_range = (wavelengths.min(), wavelengths.max())
        atm_wavelengths, atm_transmission = atmospheric_data.get_transmission(wl_range)
        
        if atm_wavelengths is None or len(atm_wavelengths) == 0:
            return
        
        # Add atmospheric transmission trace to secondary y-axis
        fig.add_trace(
            go.Scatter(
                x=atm_wavelengths,
                y=atm_transmission,
                mode='lines',
                name='Atmospheric Transmission',
                line=dict(color='gray', width=1, dash='dot'),
                opacity=0.7,
                hovertemplate="<b>Atmospheric Transmission</b><br>" +
                            "Wavelength: %{x:.3f} μm<br>" +
                            "Transmission: %{y:.3f}<extra></extra>",
                showlegend=True,
                legendgroup='atmosphere'
            ),
            secondary_y=True,
            row=subplot_row, col=1 if subplot_row else None
        )
        print("Atmops-transmission added to plot.")
        # Configure secondary y-axis
        if subplot_row:
            # For subplots - only configure for the main plot (row 1)
            if subplot_row == 1:
                fig.update_yaxes(
                    title_text="Atmospheric Transmission",
                    range=[0, 1],
                    showgrid=False,
                    tickfont=dict(color='gray', size=10),
                    secondary_y=True,
                    row=subplot_row, col=1
                )
        else:
            # For single plot
            fig.update_yaxes(
                title_text="Atmospheric Transmission",
                range=[0, 1],
                showgrid=False,
                tickfont=dict(color='gray', size=10),
                secondary_y=True
            )