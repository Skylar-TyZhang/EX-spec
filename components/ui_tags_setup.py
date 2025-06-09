from shiny import ui 

def ui_tags():
    """Enhanced UI tags with improved styling for both data types"""
    return ui.tags.head(
        ui.tags.style("""
            .main-container {
                padding: 20px;
                max-width: 1400px;
                margin: 0 auto;
            }
            .card {
                background-color: #fff;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .control-card {
                background-color: #f8f9fa;
                border-left: 4px solid #007bff;
            }
            .plot-card {
                min-height: 500px;
            }
            .info-card {
                background-color: #e8f4f8;
                border-left: 4px solid #17a2b8;
            }
            .download-btn {
                margin: 5px;
            }
            .status-text {
                font-size: 0.9em;
                color: #666;
                background-color: #f1f3f4;
                padding: 8px;
                border-radius: 4px;
                margin-top: 10px;
            }
            .tab-content {
                padding: 20px 0;
            }
            .mineral-select {
                max-height: 200px;
                overflow-y: auto;
            }
            /* Tab-specific styling */
            .nav-tabs .nav-link {
                color: #495057;
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                margin-right: 2px;
            }
            .nav-tabs .nav-link:hover {
                border-color: #e9ecef #e9ecef #dee2e6;
                background-color: #e9ecef;
            }
            .nav-tabs .nav-link.active {
                color: #495057;
                background-color: #fff;
                border-color: #dee2e6 #dee2e6 #fff;
            }
            /* Wavelength range slider styling */
            .form-range {
                width: 100%;
            }
            /* Multi-select styling */
            select[multiple] {
                background-color: #f8f9fa;
                border: 1px solid #ced4da;
                border-radius: 4px;
            }
            select[multiple]:focus {
                border-color: #80bdff;
                box-shadow: 0 0 0 0.2rem rgba(0,123,255,.25);
            }
            /* Responsive adjustments */
            @media (max-width: 768px) {
                .main-container {
                    padding: 10px;
                }
                .card {
                    padding: 15px;
                    margin-bottom: 15px;
                }
            }
        """)
    )