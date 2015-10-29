function parseGetArgument(val) {
    var result = null,
        tmp = [];
    location.search
    .substr(1)
        .split("&")
        .forEach(function (item) {
        tmp = item.split("=");
        if (tmp[0] === val) result = decodeURIComponent(tmp[1]);
    });
    return result;
}

var lastHours = parseInt(parseGetArgument('lasthours')) || 72;

var pressure_chart = null;
var light_chart = null;
var presence_chart = null;

var pressureOptions = {
  size: {
      height: 500,
  },
  bindto: '#pressure-chart',
  data: {
    type: 'line',
    x: 'date',
    xFormat: '%Y-%m-%d %H:%M:%S',
    axes: {
      internal_temperature: 'y',
      temperature: 'y',
      pressure: 'y2'
    },
    names: {
      internal_temperature: 'Internal Temperature',
      temperature: 'External Temperature',
      pressure: 'Pressure'
    }
  },
  grid: {
    y: {
      show: true
    }
  },
  axis: {
    x: {
      type: 'timeseries',
      localtime: true,
      tick: {
        count: 8,
        format: '%Y-%m-%d %H:%M'
      }
    },
    y: {
      label: {
        text: 'Temperature',
        position: 'outer-middle'
      },
      tick: {
        format: function (d) { return d3.round(d, 2) + "°C"; }
      }
    },
    y2: {
      show: true,
      label: {
        text: 'Pressure',
        position: 'outer-middle'
      },
      tick: {
        format: function (d) { return d3.round(d, 2) + " Pa"; }
      }
    }
  },
  subchart: {
    show: true
  },
  zoom: {
    enabled: true
  }
};

var lightOptions = {
  size: {
      height: 500,
  },
  bindto: '#light-chart',
  data: {
    type: 'line',
    x: 'date',
    xFormat: '%Y-%m-%d %H:%M:%S',
    axes: {
      internal_temperature: 'y',
      temperature: 'y',
      light: 'y2'
    },
    names: {
      internal_temperature: 'Internal Temperature',
      temperature: 'External Temperature',
      light: 'Light'
    }
  },
  grid: {
    y: {
      show: true
    }
  },
  axis: {
    x: {
      type: 'timeseries',
      localtime: true,
      tick: {
        count: 8,
        format: '%Y-%m-%d %H:%M'
      }
    },
    y: {
      label: {
        text: 'Temperature',
        position: 'outer-middle'
      },
      tick: {
        format: function (d) { return d3.round(d, 2) + "°C"; }
      }
    },
    y2: {
      show: true,
      label: {
        text: 'Light Intensity',
        position: 'outer-middle'
      },
      tick: {
        format: function (d) { return d3.round(d, 2) + " lx"; }
      }
    }
  },
  subchart: {
    show: true
  },
  zoom: {
    enabled: true
  }
};

var presenceOptions = {
  size: {
      height: 500,
  },
  bindto: '#presence-chart',
  data: {
    type: 'line',
    x: 'date',
    xFormat: '%Y-%m-%d %H:%M:%S',
    axes: {
      presence: 'y'
    },
    names: {
      presence: 'Presence'
    }
  },
  grid: {
    y: {
      show: true
    }
  },
  axis: {
    x: {
      type: 'timeseries',
      localtime: true,
      tick: {
        count: 8,
        format: '%Y-%m-%d %H:%M'
      }
    },
    y: {
      label: {
        text: 'Presence',
        position: 'outer-middle'
      },
      tick: {
        format: function (d) { return d3.round(d, 2); }
      }
    }
  },
  subchart: {
    show: true
  },
  zoom: {
    enabled: true
  }
};

function getJSON(url, callback) {
  var request = new XMLHttpRequest();
  request.open("GET", url);
  request.send(null);
  request.onreadystatechange = function () {
    if (request.readyState != 4) return;
    if (request.status != 200 && request.status != 304) {
      return;
    }
    callback(JSON.parse(request.responseText));
  }
}

function loadChart() {
  console.log('Loading pressure chart');
  var options = pressureOptions;
  options.data.url = './pressure.csv';
  pressure_chart = c3.generate(options);

  console.log('Loading light chart');
  var options = lightOptions;
  options.data.url = './light.csv';
  light_chart = c3.generate(options);

  console.log('Loading presence chart');
  var options = presenceOptions;
  options.data.url = './presence.csv';
  presence_chart = c3.generate(options);

  setupNextUpdate();
}

function updateChart() {
  console.log("Updating pressure chart...");
  var options = pressureOptions.data;
  options.url = './pressure.csv';
  pressure_chart.load(options);

  console.log("Updating light chart...");
  var options = lightOptions.data;
  options.url = './light.csv';
  light_chart.load(options);
  setupNextUpdate();
  
  console.log("Updating presence chart...");
  var options = presenceOptions.data;
  options.url = './presence.csv';
  presence_chart.load(options);
  setupNextUpdate();
}

function setupNextUpdate() {
  var ONE_HOUR = 60 * 60 * 1000;
  timeoutID = window.setTimeout(updateChart, ONE_HOUR);
}
