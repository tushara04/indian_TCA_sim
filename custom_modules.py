from mesa.visualization.ModularVisualization import VisualizationElement

# Shared JS helper: draws the box, tick labels, axis labels and title.
HELPER = """
var PL=55, PR=15, PT=25, PB=45;
function drawAxes(ctx, W, H, xlabel, ylabel, title, xr, yr) {
  ctx.clearRect(0, 0, W, H);
  ctx.fillStyle = "#000"; ctx.strokeStyle = "#000"; ctx.font = "12px sans-serif";
  ctx.textAlign = "center";
  ctx.fillText(title, W / 2, 14);
  ctx.fillText(xlabel, PL + (W - PL - PR) / 2, H - 6);
  ctx.save(); ctx.translate(14, PT + (H - PT - PB) / 2); ctx.rotate(-Math.PI / 2);
  ctx.fillText(ylabel, 0, 0); ctx.restore();
  ctx.strokeRect(PL, PT, W - PL - PR, H - PT - PB);
  for (var i = 0; i <= 4; i++) {
    var f = i / 4;
    ctx.textAlign = "center";
    ctx.fillText((xr[0] + f * (xr[1] - xr[0])).toFixed(xr[2]), PL + f * (W - PL - PR), H - PB + 15);
    ctx.textAlign = "right";
    ctx.fillText((yr[0] + f * (yr[1] - yr[0])).toFixed(yr[2]), PL - 5, PT + (1 - f) * (H - PT - PB) + 4);
  }
}
function mount(c) {
  var el = document.getElementById("elements");
  if (el) { el.appendChild(c); }
  else {
    document.addEventListener("DOMContentLoaded", function() {
      document.getElementById("elements").appendChild(c);
    });
  }
}
"""

# 1. average speed vs time (replaces ChartModule)
LINE_JS = """
var LineModule = function(W, H) {
  var c = document.createElement("canvas"); c.width = W; c.height = H;
  c.style.border = "1px solid #ccc"; mount(c);
  var ctx = c.getContext("2d"), vals = [];
  var pw = W - PL - PR, ph = H - PT - PB;
  function draw() {
    var ymax = Math.max(1, Math.ceil(Math.max.apply(null, vals.concat([0]))));
    var xmax = Math.max(10, vals.length);
    drawAxes(ctx, W, H, "Time step", "Average speed (cells/step)",
             "Average speed vs time", [0, xmax, 0], [0, ymax, 1]);
    ctx.strokeStyle = "#1f77b4"; ctx.beginPath();
    vals.forEach(function(v, i) {
      var x = PL + i / xmax * pw, y = PT + (1 - v / ymax) * ph;
      if (i) ctx.lineTo(x, y); else ctx.moveTo(x, y);
    });
    ctx.stroke();
  }
  this.render = function(d) { vals.push(d); draw(); };
  this.reset = function() { vals = []; draw(); };
  draw();
};
"""

# 2. space-time diagram
SPACETIME_JS = """
var SpaceTimeModule = function(W, H, TITLE) {
  var c = document.createElement("canvas"); c.width = W; c.height = H;
  c.style.border = "1px solid #ccc"; mount(c);
  var ctx = c.getContext("2d"), rows = [], tick = 0, N = 60, VMAX = 4, MAXR = 100;
  var pw = W - PL - PR, ph = H - PT - PB;
  function draw() {
    var t0 = tick - rows.length;
    drawAxes(ctx, W, H, "Position (cell)", "Time step (downwards)",
             TITLE + " (colour = speed)", [0, N, 0], [t0 + MAXR, t0, 0]);
    var cw = pw / N, rh = ph / MAXR;
    rows.forEach(function(row, i) {
      row.obs.forEach(function(x) {
        ctx.fillStyle = "#000";
        ctx.fillRect(PL + x * cw, PT + i * rh, Math.max(1, cw), Math.max(1, rh));
      });
      row.cars.forEach(function(car) {
        var hue = 120 * car[1] / Math.max(1, VMAX);
        ctx.fillStyle = "hsl(" + hue + ",90%,42%)";
        ctx.fillRect(PL + car[0] * cw, PT + i * rh, Math.max(1, cw), Math.max(1, rh));
      });
    });
  }
  this.render = function(d) {
    N = d.width; VMAX = d.vmax; tick++;
    rows.push({cars: d.cars, obs: d.obstacles});
    if (rows.length > MAXR) rows.shift();
    draw();
  };
  this.reset = function() { rows = []; tick = 0; draw(); };
  draw();
};
"""

# 3. flow vs density (builds up across resets)
FUNDAMENTAL_JS = """
var FundamentalModule = function(W, H) {
  var c = document.createElement("canvas"); c.width = W; c.height = H;
  c.style.border = "1px solid #ccc"; mount(c);
  var ctx = c.getContext("2d"), pts = [], last = null;
  var pw = W - PL - PR, ph = H - PT - PB;
  function dot(p, color) {
    ctx.fillStyle = color; ctx.beginPath();
    ctx.arc(PL + p.density * pw, PT + (1 - p.flow / ymax) * ph, 4, 0, 6.283); ctx.fill();
  }
  var ymax = 1;
  function draw() {
    var m = Math.max.apply(null, pts.map(function(p) { return p.flow; })
                           .concat([last ? last.flow : 0, 0.1]));
    ymax = Math.ceil(m * 12) / 10;
    drawAxes(ctx, W, H, "Density (cars per cell)", "Flow (cars per step)",
             "Flow vs density",
             [0, 1, 2], [0, ymax, 2]);
    pts.forEach(function(p) { dot(p, "#1f77b4"); });
    if (last) dot(last, "#d62728");   // red = current run
  }
  this.render = function(d) { last = d; draw(); };
  this.reset = function() {
    if (last && last.t >= 50) pts.push(last);   // keep finished runs
    last = null; draw();
  };
  draw();
};
"""


class AvgSpeedPlot(VisualizationElement):
    package_includes = []
    local_includes = []

    def __init__(self, w=600, h=250):
        self.js_code = HELPER + LINE_JS + "elements.push(new LineModule(%d,%d));" % (w, h)

    def render(self, model):
        return model.average_speed


class SpaceTimePlot(VisualizationElement):
    package_includes = []
    local_includes = []

    def __init__(self, lane=0, w=600, h=300):
        self.lane = lane
        self.js_code = (HELPER + SPACETIME_JS +
            'elements.push(new SpaceTimeModule(%d,%d,"Space-time, lane %d"));' % (w, h, lane))

    def render(self, model):
        return {
            "width": model.width,
            "vmax": model.general_max_speed,
            "cars": [[int(a.pos[0]), int(a.speed)]
                     for a in model.schedule.agents if a.pos[1] == self.lane],
            "obstacles": [int(o.pos[0]) for o in model.active_obstacles()
                          if o.pos[1] == self.lane],
        }

class FundamentalPlot(VisualizationElement):
    package_includes = []
    local_includes = []

    def __init__(self, w=600, h=300):
        self.js_code = HELPER + FUNDAMENTAL_JS + "elements.push(new FundamentalModule(%d,%d));" % (w, h)

    def render(self, model):
        density = model.vehicle_quantity / (model.width * model.lanes)
        recent = model.averages[-50:]
        mean_v = sum(recent) / len(recent) if recent else 0
        return {"density": density, "flow": density * mean_v, "t": model.schedule.steps}
