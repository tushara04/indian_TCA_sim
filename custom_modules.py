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

# 2. space-time diagram (Nagel & Schreckenberg integer-velocity ASCII style, x = space, -y = time)

SPACETIME_JS = """
var SpaceTimeModule = function(W, H, TITLE) {
  var wrap = document.createElement("div");
  wrap.style.width = W + "px";
  wrap.style.border = "1px solid #ccc";
  wrap.style.background = "#fafafa";
  wrap.style.marginBottom = "8px";
  wrap.style.fontFamily = "monospace";

  var header = document.createElement("div");
  header.style.padding = "4px 8px";
  header.style.font = "bold 12px sans-serif";
  header.style.textAlign = "center";
  header.style.borderBottom = "1px solid #ddd";
  header.textContent = "Space — " + TITLE.replace("Space-time, ", "");
  wrap.appendChild(header);

  var body = document.createElement("div");
  body.style.display = "flex";
  body.style.background = "#fff";
  wrap.appendChild(body);

  // Left vertical y-axis label ("Time t ↓")
  var yAxis = document.createElement("div");
  yAxis.style.writingMode = "vertical-rl";
  yAxis.style.transform = "rotate(180deg)";
  yAxis.style.textAlign = "center";
  yAxis.style.padding = "6px 4px";
  yAxis.style.font = "11px sans-serif";
  yAxis.style.color = "#444";
  yAxis.style.borderRight = "1px solid #eee";
  yAxis.textContent = "← Time step (t)";
  body.appendChild(yAxis);

  var scrollBox = document.createElement("div");
  scrollBox.style.flex = "1";
  scrollBox.style.height = H + "px";
  scrollBox.style.overflowY = "auto";
  scrollBox.style.overflowX = "auto";
  body.appendChild(scrollBox);

  var pre = document.createElement("pre");
  pre.style.margin = "0";
  pre.style.padding = "6px 8px";
  pre.style.fontSize = "12px";
  pre.style.lineHeight = "1.15";
  pre.style.background = "#fff";
  scrollBox.appendChild(pre);
  mount(wrap);

  var lines = [], tick = 0;

  function formatRow(t, N, vmax, cars, obs) {
    var cells = new Array(N);
    for (var i = 0; i < N; i++) {
      cells[i] = '<span style="color:#bbb;">.</span>';
    }
    obs.forEach(function(x) {
      if (x >= 0 && x < N) {
        cells[x] = '<span style="color:#000;font-weight:bold;">X</span>';
      }
    });
    var half = Math.floor(vmax / 2);
    cars.forEach(function(car) {
      var x = car[0], v = car[1];
      if (x >= 0 && x < N) {
        var color = (v === 0) ? "#d90429" : (v > half ? "#1b9a00" : "#d97706");
        cells[x] = '<span style="color:' + color + ';font-weight:bold;">' + v + '</span>';
      }
    });
    var tLabel = String(t).padStart(3, " ") + " | ";
    return '<span style="color:#666;">' + tLabel + '</span>' + cells.join(" ");
  }

  this.render = function(d) {
    tick++;
    lines.push(formatRow(tick, d.width, d.vmax, d.cars, d.obstacles));
    pre.innerHTML = lines.join("\\n");
    scrollBox.scrollTop = scrollBox.scrollHeight;
  };
  this.reset = function() {
    lines = [];
    tick = 0;
    pre.innerHTML = "";
  };
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
        cars = model.pre_move_cars if model.pre_move_cars else [
            (a.pos[0], a.pos[1], a.speed) for a in model.schedule.agents
        ]
        return {
            "width": model.width,
            "vmax": model.general_max_speed,
            "cars": [[int(x), int(v)] for (x, y, v) in cars if y == self.lane],
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

PARAM_FILTER_JS = """
(function() {
  var GROUPS = {
    fixed: ["obstacle_lane", "obstacle_x", "obstacle_length"],
    crossing: ["crossing_from", "crossing_dwell", "crossing_gap"],
    traffic_light: ["light_x", "red_start_step", "red_duration"]
  };
  var ALL_KEYS = [].concat(GROUPS.fixed, GROUPS.crossing, GROUPS.traffic_light);
  var currentMode = "none";

  function findRow(key) {
    var ctrl = (
      document.getElementById(key + "_id") ||
      document.getElementById(key) ||
      document.querySelector('[name="' + key + '"]')
    );
    if (!ctrl) return null;
    return (
      ctrl.closest(".input-group") ||
      ctrl.closest(".form-group") ||
      ctrl.parentElement
    );
  }

  function applyVisibility() {
    var active = GROUPS[currentMode] || [];
    ALL_KEYS.forEach(function(key) {
      var row = findRow(key);
      if (!row) return;
      var show = active.indexOf(key) !== -1;
      row.style.display = show ? "" : "none";
      var prev = row.previousElementSibling;
      if (prev && (prev.tagName === "P" || prev.tagName === "LABEL")) {
        prev.style.display = show ? "" : "none";
      }
    });
  }

  // Intercept Mesa's WebSocket submit_params messages directly
  var origSend = WebSocket.prototype.send;
  WebSocket.prototype.send = function(data) {
    try {
      var msg = JSON.parse(data);
      if (msg && msg.type === "submit_params" && msg.param === "obstacle_type") {
        currentMode = msg.value;
        applyVisibility();
      }
    } catch (e) {}
    return origSend.apply(this, arguments);
  };

  function init() {
    if (!findRow("obstacle_lane")) {
      setTimeout(init, 100);
      return;
    }
    applyVisibility();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
"""

class ParamFilter(VisualizationElement):
    package_includes = []
    local_includes = []

    def __init__(self):
        self.js_code = PARAM_FILTER_JS + "\nelements.push({render: function(){}, reset: function(){}});"

    def render(self, model):
        return None