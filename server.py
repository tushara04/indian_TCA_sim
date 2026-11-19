from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import CanvasGrid, TextElement
from mesa.visualization.UserParam import UserSettableParameter

from model import NaSchTraffic, ObstacleAgent
from custom_modules import AvgSpeedPlot, SpaceTimePlot, FundamentalPlot

# Define some colours for later use
# Red
STOPPED_COLOR = ["#FF0000", "#FF9999"]
# Orange
SLOW_COLOR = ["#FFAB00", "#FFCB62"]
# Green
FAST_COLOR = ["#2BCB00", "#8EE484"]


class AgentElement(TextElement):
    """
    Display text for the average speed of the agents.
    """

    def __init__(self):
        pass

    def render(self, model):
        text_1 = "Number of agents: " + str(model.schedule.get_agent_count()) + "   "
        text_2 = "Average Speed " + str(model.average_speed) + "   "
        return text_1 + text_2

class LegendElement(TextElement):
    """Colour legend that updates with the max-speed slider."""

    def __init__(self):
        pass

    def render(self, model):
        half = int(model.general_max_speed / 2)
        vmax = model.general_max_speed

        def item(color, label):
            return (
                '<span style="display:inline-block;width:12px;height:12px;'
                'border-radius:50%%;background:%s;margin:0 4px 0 12px;'
                'vertical-align:middle;"></span>%s' % (color, label)
            )

        slow = "speed 1" if half <= 1 else "speed 1&ndash;%d" % half
        fast = "speed %d" % vmax if half + 1 == vmax else "speed %d&ndash;%d" % (half + 1, vmax)

        return (
            "<b>Legend:</b>"
            + item("#FF0000", "Stopped (speed 0)")
            + item("#FFAB00", "Slow (%s)" % slow)
            + item("#2BCB00", "Fast (%s)" % fast)
        )

def vehicle_draw(agent):
    if agent is None:
        return
    if isinstance(agent, ObstacleAgent):
        color = "#000000" if agent.kind == "fixed" else "#6A0DAD"   # black / purple
        return {"Shape": "rect", "w": 1, "h": 1, "Filled": "true",
                "Layer": 0, "Color": color}

    portrayal = {"Shape": "circle", "r": 0.5, "Filled": "true", "Layer": 0}
    if agent.speed == 0:
        color = STOPPED_COLOR
    elif agent.speed > int(agent.max_speed / 2):
        color = FAST_COLOR
    else:
        color = SLOW_COLOR
    portrayal["Color"] = color
    return portrayal

LANES = 5
CANVAS_W = 1000

# define the elements of the visualisation
agent_element = AgentElement()
canvas_element = CanvasGrid(vehicle_draw, 60, LANES, CANVAS_W, 20 * LANES)
legend_element = LegendElement()
speed_chart = AvgSpeedPlot(w=CANVAS_W, h=250)
spacetime_plots = [SpaceTimePlot(lane=l, w=CANVAS_W, h=250) for l in range(LANES)]
fundamental_plot = FundamentalPlot(w=CANVAS_W, h=320)
# define the parameters of the model
model_params = {
    "height": LANES,
    "width": 60,
    "vehicle_quantity": UserSettableParameter("slider", "Vehicle Quantity", 10, 1, 60 * LANES - 1, 1),
    "general_max_speed": UserSettableParameter("slider", "Max speed", 4, 1, 6, 1),
    "slow_prob": UserSettableParameter("slider", "Slowdown probability", 0.3, 0.0, 1.0, 0.05),
    "change_prob": UserSettableParameter("slider", "Lane-change probability", 1.0, 0.0, 1.0, 0.1),

    "obstacle_type": UserSettableParameter("choice", "Obstacle type", value="none",
                                           choices=["none", "fixed", "crossing"]),
    # fixed obstacle
    "obstacle_lane": UserSettableParameter("slider", "Fixed: lane", 0, 0, max(LANES - 1, 1), 1),
    "obstacle_x": UserSettableParameter("slider", "Fixed: position", 30, 0, 59, 1),
    "obstacle_length": UserSettableParameter("slider", "Fixed: length (cells)", 1, 1, 10, 1),
    # crossing obstacle
    "crossing_from": UserSettableParameter("choice", "Crossing: starts at", value="lane 0",
                                           choices=["lane 0", "last lane"]),
    "crossing_x": UserSettableParameter("slider", "Crossing: position", 30, 0, 59, 1),
    "crossing_dwell": UserSettableParameter("slider", "Crossing: steps per lane", 4, 1, 15, 1),
    "crossing_gap": UserSettableParameter("slider", "Crossing: steps between crossings", 15, 1, 100, 1),
}

# instantiate server
server = ModularServer(
    NaSchTraffic,
    [canvas_element, legend_element, agent_element, speed_chart, *spacetime_plots, fundamental_plot],
    "Traffic Model",
    model_params,
)
# set server port
server.port = 8555
# edited
if __name__ == "__main__":
    server.launch()
