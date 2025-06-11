import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple

class PlotlyUSGSVisualiser:
    """Enhanced Plotly-based visualisations for USGS spectral data"""
    
    def __init__(self):
        # Color palette for consistent styling
        self.colors = px.colors.qualitative.Set1 + px.colors.qualitative.Set2
        
        # Default layout settings
        self.default_layout = dict(
            font=dict(family="Arial, sans-serif", size=12),
            hovermode='x unified',
            showlegend=True,
            legend=dict(
                orientation="v",
                yanchor="top",
                y=1,
                xanchor="left",
                x=1.02
            )
        )
    
    def plot_satellite_spectra_with_bands(self, 
                                        lib_obj,
                                        keys: List[str], 
                                        show_response_functions: bool = True,
                                        show_band_centers: bool = True, 
                                        show_band_ranges: bool = True,
                                        title: Optional[str] = None,
                                        height: int = 800) -> go.Figure:
        """
        Create interactive Plotly visualisation for satellite spectra with band information
        
        Parameters:
        -----------
        lib_obj : USGSSatelliteSpectra
            Satellite spectral library object
        keys : List[str]
            List of spectrum keys to plot
        show_response_functions : bool
            Whether to show band response functions subplot
        show_band_centers : bool
            Whether to show vertical lines at band centers
        show_band_ranges : bool
            Whether to show shaded regions for band ranges
        title : str, optional
            Plot title
        height : int
            Total figure height in pixels
            
        Returns:
        --------
        plotly.graph_objects.Figure
            Interactive Plotly figure
        """
        print(f"Plotting {len(keys)} spectra with satellite band information...")
        # Create subplots if showing response functions
        if show_response_functions and lib_obj.bands:
            fig = make_subplots(
                rows=2, cols=1,
                subplot_titles=(f'USGS Library Mineral Spectra', 'Band Response Functions'),
                vertical_spacing=0.08,
                row_heights=[0.7, 0.3]
            )
            main_row = 1
            band_row = 2
        else:
            fig = go.Figure()
            main_row = 1
            band_row = None
        
        # Plot mineral spectra
        for i, key in enumerate(keys):
            if key in lib_obj.spectra:
                spectrum = lib_obj.spectra[key]['spectrum']
                metadata = lib_obj.spectra[key]['metadata']
                
                # Create hover text with detailed information
                hover_text = [
                    f"Wavelength: {wl:.3f} μm<br>"
                    f"Reflectance: {refl:.4f}<br>"
                    f"Material: {metadata['material']}<br>"
                    f"Sample: {metadata['sample_id']}<br>"
                    #f"Measurement: {metadata['measurement_type']}"
                    for wl, refl in zip(lib_obj.wavelengths, spectrum)
                ]
                
                fig.add_trace(
                    go.Scatter(
                        x=lib_obj.wavelengths,
                        y=spectrum,
                        mode='lines+markers',
                        name=f"{metadata['material']} {metadata['sample_id']}",
                        line=dict(color=self.colors[i % len(self.colors)], width=2),
                        marker=dict(size=4, opacity=0.7),
                        hovertemplate='%{hovertext}<extra></extra>',
                        hovertext=hover_text,
                        showlegend=True
                    ),
                    row=main_row, col=1
                )
        
        # Add band information if available
        if lib_obj.bands and lib_obj.wavelengths is not None:
            sorted_bands = sorted(lib_obj.bands.items())
            band_colors = px.colors.qualitative.Set3
            
            for i, (band_num, band_info) in enumerate(sorted_bands):
                # Extract band number for indexing
                band_num_int = ''.join([char for char in band_num if char.isdigit()])
                try:
                    band_num_int = int(band_num_int)
                    band_center = lib_obj.wavelengths[band_num_int - 1] if band_num_int <= len(lib_obj.wavelengths) else None
                except:
                    continue
                
                color = band_colors[i % len(band_colors)]
                
                # Add band center line
                if show_band_centers and band_center is not None:
                    fig.add_vline(
                        x=band_center,
                        line=dict(color=color, width=2, dash="dash"),
                        opacity=0.7,
                        annotation_text=f"Band {band_num}",
                        annotation_font=dict(color=color, size=6),
                        annotation_position="top",
                        row=main_row, col=1
                    )
                
                # Add band range
                if show_band_ranges and band_center is not None:
                    if lib_obj.bandpass_micron is not None and band_num_int <= len(lib_obj.bandpass_micron):
                        bandpass = lib_obj.bandpass_micron[band_num_int - 1]
                        band_min = band_center - bandpass / 2
                        band_max = band_center + bandpass / 2
                        
                        fig.add_vrect(
                            x0=band_min, x1=band_max,
                            fillcolor=color,
                            opacity=0.2,
                            line_width=0,
                            row=main_row, col=1
                        )
        
        # Plot band response functions if requested
        if show_response_functions and band_row is not None and lib_obj.bands and lib_obj.wavelengths_hp is not None:
            sorted_bands = sorted(lib_obj.bands.items())
            
            for i, (band_num, band_info) in enumerate(sorted_bands):
                response = band_info['response']
                wavelengths_band = band_info['wavelengths']
                
                # Ensure same length
                min_len = min(len(wavelengths_band), len(response))
                wavelengths_band = wavelengths_band[:min_len]
                response = response[:min_len]
                
                color = band_colors[i % len(band_colors)]
                
                # Create hover text for band response
                hover_text_band = [
                    f"Wavelength: {wl:.3f} μm<br>"
                    f"Response: {resp:.4f}<br>"
                    f"Band: {band_info['band_name']}"
                    for wl, resp in zip(wavelengths_band, response)
                ]
                
                fig.add_trace(
                    go.Scatter(
                        x=wavelengths_band,
                        y=response,
                        fill='tonexty' if i == 0 else 'tozeroy',
                        mode='lines',
                        name=f"{band_info['band_name']}",
                        line=dict(color=color, width=1),
                        fillcolor=color,
                        opacity=0.6,
                        hovertemplate='%{hovertext}<extra></extra>',
                        hovertext=hover_text_band,
                        showlegend=False,
                        legendgroup=f"band_{i}"
                    ),
                    row=band_row, col=1
                )
        
        # Update layout
        fig.update_layout(
            title=title or f"{lib_obj.satellite} Spectral Analysis",
            height=height,
            **self.default_layout
        )
        
        # Update axes
        fig.update_xaxes(
            title_text="Wavelength (μm)",
            showgrid=True,
            gridwidth=1,
            gridcolor='lightgray',
            zeroline=False,
            row=main_row, col=1
        )
        
        # Determine y-axis label based on measurement type
        if keys and keys[0] in lib_obj.spectra:
            metadata = lib_obj.spectra[keys[0]]['metadata']
            if metadata['measurement_type'] == 'AREF':
                y_label = 'Absolute Reflectance'
            elif metadata['measurement_type'] == 'RREF':
                y_label = 'Relative Reflectance'
            elif metadata['measurement_type'] == 'TRAN':
                y_label = 'Transmission'
            else:
                y_label = 'Value'
        else:
            y_label = 'Reflectance / Transmission'
        
        fig.update_yaxes(
            title_text=y_label,
            showgrid=True,
            gridwidth=1,
            gridcolor='lightgray',
            zeroline=False,
            row=main_row, col=1
        )
        
        if band_row is not None:
            fig.update_xaxes(
                title_text="Wavelength (μm)",
                showgrid=True,
                gridwidth=1,
                gridcolor='lightgray',
                row=band_row, col=1
            )
            fig.update_yaxes(
                title_text="Response",
                showgrid=True,
                gridwidth=1,
                gridcolor='lightgray',
                row=band_row, col=1
            )
        
        # Add crosshair cursor
        fig.update_layout(
            hoverlabel=dict(
                bgcolor="white",
                font_size=12,
                font_family="Arial"
            )
        )
        
        return fig
    
    def plot_full_spectrum_data(self,
                               lib_obj,
                               keys: List[str],
                               wavelength_range: Optional[Tuple[float, float]] = None,
                               title: Optional[str] = None,
                               height: int = 600) -> go.Figure:
        """
        Create interactive Plotly visualisation for full spectrum data
        
        Parameters:
        -----------
        lib_obj : USGSSpectra
            Full spectrum library object
        keys : List[str]
            List of spectrum keys to plot
        wavelength_range : Tuple[float, float], optional
            Wavelength range to display (min, max) in μm
        title : str, optional
            Plot title
        height : int
            Figure height in pixels
            
        Returns:
        --------
        plotly.graph_objects.Figure
            Interactive Plotly figure
        """
        
        fig = go.Figure()
        
        for i, key in enumerate(keys):
            if key in lib_obj.spectra:
                spectrum = lib_obj.spectra[key]['spectrum']
                metadata = lib_obj.spectra[key]['metadata']
                wavelengths = lib_obj.wavelengths
                
                # Apply wavelength filtering if specified
                if wavelength_range:
                    mask = (wavelengths >= wavelength_range[0]) & (wavelengths <= wavelength_range[1])
                    wavelengths = wavelengths[mask]
                    spectrum = spectrum[mask]
                
                # Create detailed hover text
                hover_text = [
                    f"Wavelength: {wl:.4f} μm<br>"
                    f"Reflectance: {refl:.6f}<br>"
                    f"Material: {metadata['material']}<br>"
                    f"Sample: {metadata['sample_id']}<br>"
                    #f"Spectrometer: {metadata['spectrometer']}<br>"
                    #f"Measurement: {metadata['measurement_type']}<br>"
                    #f"Purity: {metadata['purity']}"
                    for wl, refl in zip(wavelengths, spectrum)
                ]
                
                fig.add_trace(
                    go.Scatter(
                        x=wavelengths,
                        y=spectrum,
                        mode='lines',
                        name=f"{metadata['material']} {metadata['sample_id']}",
                        line=dict(
                            color=self.colors[i % len(self.colors)], 
                            width=2
                        ),
                        hovertemplate='%{hovertext}<extra></extra>',
                        hovertext=hover_text,
                        showlegend=True
                    )
                )
        
        # Update layout
        wavelength_info = f" ({wavelength_range[0]:.1f}-{wavelength_range[1]:.1f} μm)" if wavelength_range else ""
        fig.update_layout(
            title=title or f"{lib_obj.spectrometer} Full Spectrum Analysis{wavelength_info}",
            height=height,
            **self.default_layout
        )
        
        # Update axes
        fig.update_xaxes(
            title_text="Wavelength (μm)",
            showgrid=True,
            gridwidth=1,
            gridcolor='lightgray',
            zeroline=False
        )
        
        fig.update_yaxes(
            title_text="Reflectance / Transmission",
            showgrid=True,
            gridwidth=1,
            gridcolor='lightgray',
            zeroline=False
        )
        
        # Enhanced hover behavior
        fig.update_layout(
            hovermode='x unified',
            hoverlabel=dict(
                bgcolor="white",
                font_size=12,
                font_family="Arial"
            )
        )
        
        return fig
    
    def plot_band_responses_detailed(self, 
                                   lib_obj,
                                   width: int = 1200,
                                   height: int = 800) -> go.Figure:
        """
        Create interactive subplot grid of band response functions
        
        Parameters:
        -----------
        lib_obj : USGSSatelliteSpectra
            Satellite library object
        width : int
            Figure width in pixels
        height : int
            Figure height in pixels
            
        Returns:
        --------
        plotly.graph_objects.Figure
            Interactive Plotly figure with subplots
        """
        
        if not lib_obj.bands or lib_obj.wavelengths_hp is None:
            # Create empty figure with message
            fig = go.Figure()
            fig.add_annotation(
                text="No band response data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=16)
            )
            return fig
        
        # Calculate subplot grid
        sorted_bands = sorted(lib_obj.bands.items())
        num_bands = len(sorted_bands)
        cols = min(3, num_bands)
        rows = (num_bands + cols - 1) // cols
        
        # Create subplot titles
        subplot_titles = [
            f"Band {band_num}: {band_info['band_name']}"
            for band_num, band_info in sorted_bands
        ]
        
        fig = make_subplots(
            rows=rows, cols=cols,
            subplot_titles=subplot_titles,
            vertical_spacing=0.08,
            horizontal_spacing=0.06
        )
        
        # Plot each band
        for i, (band_num, band_info) in enumerate(sorted_bands):
            row = i // cols + 1
            col = i % cols + 1
            
            response = band_info['response']
            wavelengths_band = band_info['wavelengths']
            
            # Ensure same length
            min_len = min(len(wavelengths_band), len(response))
            wavelengths_band = wavelengths_band[:min_len]
            response = response[:min_len]
            
            # Calculate statistics for hover info
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
            
            # Create hover text
            hover_text = [
                f"Wavelength: {wl:.4f} μm<br>"
                f"Response: {resp:.4f}<br>"
                f"Band: {band_info['band_name']}<br>"
                f"Peak: {peak_wavelength:.3f} μm<br>"
                f"FWHM: {fwhm:.3f} μm"
                for wl, resp in zip(wavelengths_band, response)
            ]
            
            color = self.colors[i % len(self.colors)]
            
            # Add filled area
            fig.add_trace(
                go.Scatter(
                    x=wavelengths_band,
                    y=response,
                    fill='tozeroy',
                    mode='lines',
                    name=f"Band {band_num}",
                    line=dict(color=color, width=2),
                    fillcolor=color,
                    opacity=0.6,
                    hovertemplate='%{hovertext}<extra></extra>',
                    hovertext=hover_text,
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
                    marker=dict(
                        color='red',
                        size=8,
                        symbol='diamond'
                    ),
                    name=f"Peak {band_num}",
                    hovertemplate=f'Peak: {peak_wavelength:.3f} μm<extra></extra>',
                    showlegend=False
                ),
                row=row, col=col
            )
            
            # Add FWHM markers
            if fwhm > 0:
                fig.add_trace(
                    go.Scatter(
                        x=[fwhm_start, fwhm_end],
                        y=[half_max, half_max],
                        mode='markers+lines',
                        line=dict(color='gray', width=2, dash='dot'),
                        marker=dict(color='gray', size=6),
                        name=f"FWHM {band_num}",
                        hovertemplate=f'FWHM: {fwhm:.3f} μm<extra></extra>',
                        showlegend=False
                    ),
                    row=row, col=col
                )
        
        # Update layout
        fig.update_layout(
            title=f'{lib_obj.satellite} Band Response Functions (Interactive)',
            width=width,
            height=height,
            showlegend=False,
            font=dict(family="Arial, sans-serif", size=10),
            hovermode='closest'
        )
        
        # Update all axes
        for i in range(1, rows + 1):
            for j in range(1, cols + 1):
                fig.update_xaxes(
                    title_text="Wavelength (μm)",
                    showgrid=True,
                    gridwidth=1,
                    gridcolor='lightgray',
                    row=i, col=j
                )
                fig.update_yaxes(
                    title_text="Response",
                    showgrid=True,
                    gridwidth=1,
                    gridcolor='lightgray',
                    row=i, col=j
                )
        
        return fig
    
    def create_comparison_dashboard(self,
                                  satellite_lib,
                                  full_lib,
                                  mineral_keys: List[str],
                                  wavelength_range: Optional[Tuple[float, float]] = None) -> go.Figure:
        """
        Create a comparison dashboard showing both satellite and full spectrum data
        
        Parameters:
        -----------
        satellite_lib : USGSSatelliteSpectra
            Satellite library object
        full_lib : USGSSpectra
            Full spectrum library object
        mineral_keys : List[str]
            Common mineral keys to compare
        wavelength_range : Tuple[float, float], optional
            Wavelength range for full spectrum plot
            
        Returns:
        --------
        plotly.graph_objects.Figure
            Comparison dashboard figure
        """
        
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=(
                f'{satellite_lib.satellite} Satellite Bands',
                f'{full_lib.spectrometer} Full Spectrum'
            ),
            vertical_spacing=0.1,
            row_heights=[0.5, 0.5]
        )
        
        # Plot satellite data
        for i, key in enumerate(mineral_keys):
            if key in satellite_lib.spectra:
                spectrum = satellite_lib.spectra[key]['spectrum']
                metadata = satellite_lib.spectra[key]['metadata']
                
                fig.add_trace(
                    go.Scatter(
                        x=satellite_lib.wavelengths,
                        y=spectrum,
                        mode='lines+markers',
                        name=f"SAT: {metadata['material']}",
                        line=dict(color=self.colors[i % len(self.colors)], width=2),
                        marker=dict(size=6),
                        legendgroup=f"mineral_{i}",
                        showlegend=True
                    ),
                    row=1, col=1
                )
        
        # Plot full spectrum data
        for i, key in enumerate(mineral_keys):
            if key in full_lib.spectra:
                spectrum = full_lib.spectra[key]['spectrum']
                metadata = full_lib.spectra[key]['metadata']
                wavelengths = full_lib.wavelengths
                
                # Apply wavelength filtering
                if wavelength_range:
                    mask = (wavelengths >= wavelength_range[0]) & (wavelengths <= wavelength_range[1])
                    wavelengths = wavelengths[mask]
                    spectrum = spectrum[mask]
                
                fig.add_trace(
                    go.Scatter(
                        x=wavelengths,
                        y=spectrum,
                        mode='lines',
                        name=f"FULL: {metadata['material']}",
                        line=dict(
                            color=self.colors[i % len(self.colors)], 
                            width=2,
                            dash='dot'
                        ),
                        legendgroup=f"mineral_{i}",
                        showlegend=True
                    ),
                    row=2, col=1
                )
        
        # Update layout
        fig.update_layout(
            title="Satellite vs Full Spectrum Comparison",
            height=800,
            **self.default_layout
        )
        
        # Update axes
        for row in [1, 2]:
            fig.update_xaxes(
                title_text="Wavelength (μm)",
                showgrid=True,
                gridwidth=1,
                gridcolor='lightgray',
                row=row, col=1
            )
            fig.update_yaxes(
                title_text="Reflectance / Transmission",
                showgrid=True,
                gridwidth=1,
                gridcolor='lightgray',
                row=row, col=1
            )
        
        return fig