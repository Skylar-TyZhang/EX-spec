from shiny import ui

def select_satellite():
    """
    Creates a form for configuring simulation parameters
    """
    return ui.div(
        ui.h4("Simulation Parameters"),
        ui.p("Configure the parameters for your exploration simulation:"),
        
        ui.input_numeric(
            "drill_cost", 
            "Drilling Cost", 
            value=10, 
            min=1, 
            max=100
        ),
        ui.help_text("Cost incurred for each drill operation"),
        
        ui.input_numeric(
            "hit_reward", 
            "Hit Reward", 
            value=100, 
            min=10, 
            max=1000
        ),
        ui.help_text("Reward received when a drill successfully finds minerals"),
        
        ui.input_slider(
            "discount_factor", 
            "Discount Factor", 
            value=0.9, 
            min=0.1, 
            max=1.0, 
            step=0.05
        ),
        ui.help_text("How future rewards are valued (0.9 = future rewards are valued at 90% of immediate rewards)"),
        
        ui.input_action_button(
            "run_simulation",
            "Run Simulation",
            class_="btn-primary"
        ),
    )