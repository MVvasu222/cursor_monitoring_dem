(function () {
  const root = document.getElementById("monitor");
  const initial = JSON.parse(document.getElementById("initial-sample").textContent);
  const sampleUrl = root.dataset.sampleUrl;
  const charts = {};

  function formatBytes(value) {
    let size = Number(value) || 0;
    const units = ["B", "KB", "MB", "GB", "TB"];
    for (let i = 0; i < units.length; i += 1) {
      if (size < 1024 || units[i] === "TB") {
        return units[i] === "B" ? Math.round(size) + " B" : size.toFixed(1) + " " + units[i];
      }
      size /= 1024;
    }
    return size.toFixed(1) + " TB";
  }

  function showError(message) {
    const node = document.getElementById("sample-error");
    node.hidden = false;
    node.textContent = message;
  }

  function clearError() {
    const node = document.getElementById("sample-error");
    node.hidden = true;
    node.textContent = "";
  }

  function rootPercent(sample) {
    const disk = (sample.disks || []).find(function (item) { return item.mount === "/"; });
    return disk ? disk.percent : 0;
  }

  function labels(history) {
    return history.map(function (point) {
      return new Date(point.ts * 1000).toLocaleTimeString();
    });
  }

  function series(history, pick) {
    return history.map(pick);
  }

  function draw(id, history, datasets) {
    if (typeof Chart === "undefined") {
      return;
    }
    const canvas = document.getElementById(id);
    const payload = {
      labels: labels(history),
      datasets: datasets,
    };
    if (!charts[id]) {
      charts[id] = new Chart(canvas, {
        type: "line",
        data: payload,
        options: {
          animation: false,
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { labels: { color: "#8ea0b5" } } },
          scales: {
            x: { ticks: { color: "#8ea0b5", maxTicksLimit: 5 }, grid: { color: "#2a3848" } },
            y: { beginAtZero: true, ticks: { color: "#8ea0b5" }, grid: { color: "#2a3848" } },
          },
        },
      });
      return;
    }
    charts[id].data.labels = payload.labels;
    charts[id].data.datasets = datasets;
    charts[id].update();
  }

  function render(payload) {
    const sample = payload.sample;
    const history = payload.history || [];
    if (!sample) {
      return;
    }
    document.getElementById("cpu-value").textContent = sample.cpu_percent.toFixed(1) + "%";
    document.getElementById("cpu-load").textContent = "Load " + sample.load.join(" ");
    document.getElementById("memory-value").textContent = sample.memory.percent.toFixed(1) + "%";
    document.getElementById("memory-detail").textContent =
      formatBytes(sample.memory.used) + " used · " + formatBytes(sample.memory.free) + " free";
    document.getElementById("disk-value").textContent = rootPercent(sample).toFixed(1) + "%";
    document.getElementById("network-value").textContent = formatBytes(sample.rate_in) + "/s";
    document.getElementById("network-detail").textContent =
      "In " + formatBytes(sample.rate_in) + "/s · Out " + formatBytes(sample.rate_out) + "/s";

    fillRows("disk-rows", sample.disks, function (disk) {
      return [disk.mount, formatBytes(disk.used), formatBytes(disk.free), disk.percent.toFixed(1) + "%"];
    });
    fillRows("nic-rows", sample.interfaces, function (nic) {
      return [nic.name, formatBytes(nic.bytes_in), formatBytes(nic.bytes_out)];
    });
    fillRows("port-rows", sample.ports, function (port) {
      return [String(port.port), port.protocol, port.address, port.process];
    });

    draw("cpu-chart", history, [line("CPU %", "#3ddc97", series(history, function (point) { return point.cpu_percent; }))]);
    draw("memory-chart", history, [line("Memory %", "#7eb6ff", series(history, function (point) { return point.memory.percent; }))]);
    draw("disk-chart", history, [line("Root %", "#f0c674", series(history, rootPercent))]);
    draw("network-chart", history, [
      line("In", "#3ddc97", series(history, function (point) { return point.rate_in; })),
      line("Out", "#ff8b7b", series(history, function (point) { return point.rate_out; })),
    ]);
  }

  function line(label, color, data) {
    return {
      label: label,
      data: data,
      borderColor: color,
      backgroundColor: color,
      pointRadius: 0,
      tension: 0.25,
      fill: false,
    };
  }

  function fillRows(id, rows, cells) {
    const body = document.getElementById(id);
    body.replaceChildren();
    rows.forEach(function (row) {
      const tr = document.createElement("tr");
      cells(row).forEach(function (value) {
        const td = document.createElement("td");
        td.textContent = value;
        tr.appendChild(td);
      });
      body.appendChild(tr);
    });
  }

  render(initial);
  window.setInterval(async function () {
    try {
      const response = await fetch(sampleUrl, { headers: { Accept: "application/json" } });
      if (!response.ok) {
        showError("Could not read this machine.");
        return;
      }
      const payload = await response.json();
      if (!payload.ok) {
        showError(payload.error || "Could not read this machine.");
      } else {
        clearError();
      }
      if (payload.sample) {
        render(payload);
      }
    } catch (error) {
      showError("Could not read this machine.");
    }
  }, 5000);
})();
