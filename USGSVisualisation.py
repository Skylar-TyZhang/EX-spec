import matplotlib.pyplot as plt
import numpy as np

class USGSVisualisation:
    """
    Class for visualisation of USGS data.
    """

    def __init__(self, spectra, spectrometer, wavelengths, bands, bandpass):
        self.spectra = spectra
        self.spectrometer = spectrometer
        self.wavelengths = wavelengths
        self.bands = bands
        self.bandpass = bandpass

    def plot_minerals(self, minerals, show_band_centers = True, show_band_ranges = True, max_samples=10, figsize=(12, 8)):
        """
        Plot spectra for a mineral family

        Parameters:
        -----------
        minerals : list
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
        # Plot the spectra
            
        fig, ax = plt.subplots(figsize=figsize)
        for mineral in minerals:
            
            # Find matching spectra
            matching_keys = [
                key
                for key in self.spectra.keys()
                if (mineral in key and self.spectrometer in key)
            ]

            # Limit the number of samples
            if max_samples and max_samples < len(matching_keys):
                matching_keys = matching_keys[:max_samples]

            if not matching_keys:
                print(f"No spectra found matching mineral family: {minerals}")
                pass

            print(
                f"Found {len(matching_keys)} matching samples for {mineral} measurement type {self.spectrometer}"
            )

            

            for key in matching_keys:
                if key in self.spectra:
                    # get the spectrum and metadata
                    spectrum = self.spectra[key]["spectrum"]
                    metadata = self.spectra[key]["metadata"]

                    # Plot the spectrum
                    ax.plot(
                        self.wavelengths,
                        spectrum,
                        "-",
                        label=f"{metadata['material']} {metadata['sample_id']}",
                    )

        # Add bands lable if available
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
                    ax.axvline(x=band_center, color=color, linestyle='--', alpha=0.8, linewidth=1.5)
                
                # Show band range as shaded region (using bandpass if available)
                if show_band_ranges and band_center is not None:
                    if self.bandpass is not None and band_num <= len(self.bandpass):
                        bandpass = self.bandpass[band_num - 1]
                        band_min = band_center - bandpass / 2
                        band_max = band_center + bandpass / 2
                        
                        ax.axvspan(band_min, band_max, alpha=0.2, color=color)
        
        # Add labels
        ax.set_xlabel("Wavelength (μm)")
        ax.set_ylabel("Reflectance / Transmission")

        ax.set_title(f"Spectral Comparison")

        ax.grid(True, linestyle="--", alpha=0.7)
        ax.legend()

        plt.tight_layout()
        return fig

