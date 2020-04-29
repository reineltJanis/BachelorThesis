function updateTrace(div, traces, lastIterations) {
  if (typeof div === "string") div = document.getElementById(div);

  if (!div.data) {
    if (traces) {
      Plotly.newPlot(div, traces);
      if (lastIterations) {
        div.lastIterations = lastIterations;
      }
    }
    return;
  }
  if (traces.length == 0) {
    return;
  }
  traces.forEach((trace, index) => {
    console.log(trace);
    let position = div.data.indexOf(
      div.data.find((t) => t["name"] === trace["name"])
    );
    if (position > -1) {
      Plotly.extendTraces(div, { x: [trace.x], y: [trace.y] }, [position]);
    } else {
      Plotly.addTraces(div, [trace]);
    }
  });
  if (lastIterations) {
    div.lastIterations = { ...div.lastIterations, ...lastIterations };
  }
}

function getTrace(traces, name) {
  if (!traces) {
    return;
  }
  let position = traces.find((t) => t["name"] === name);
  if (position) {
    return trace;
  } else {
    return [];
  }
}
