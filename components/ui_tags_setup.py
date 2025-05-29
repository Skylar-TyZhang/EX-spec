from shiny import ui 
def ui_tags():
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
            }
            .tab-content {
                padding: 20px 0;
            }
            .mineral-select {
                max-height: 200px;
                overflow-y: auto;
            }
        """)
    )
    