const form = document.querySelector("#search-form");
const presetButtons = document.querySelectorAll(".preset");
const fields = {
  dataSource: document.querySelector("#data-source"),
  name: document.querySelector("#name"), storeys: document.querySelector("#storeys"),
  footprint: document.querySelector("#footprint"), siteArea: document.querySelector("#site-area"),
  designCoverage: document.querySelector("#design-coverage"),
  buildingWidth: document.querySelector("#building-width"),
  buildingDepth: document.querySelector("#building-depth"),
  buildingHeight: document.querySelector("#building-height"),
  frontage: document.querySelector("#frontage"), depth: document.querySelector("#depth"),
  zoneCategories: document.querySelector("#zone-categories"),
};
let examples;
let activeAssumptions = {};

function setEnvelope(envelope) {
  fields.name.value = envelope.name;
  fields.storeys.value = envelope.storeys;
  fields.footprint.value = envelope.footprint_sqm;
  fields.buildingWidth.value = envelope.building_width_m || "";
  fields.buildingDepth.value = envelope.building_depth_m || "";
  fields.buildingHeight.value = envelope.building_height_m || "";
  fields.siteArea.value = envelope.minimum_site_area_sqm || "";
  fields.designCoverage.value = envelope.maximum_design_site_coverage ? envelope.maximum_design_site_coverage * 100 : "";
  fields.frontage.value = envelope.required_frontage_m || "";
  fields.depth.value = envelope.required_depth_m || "";
  fields.zoneCategories.value = (envelope.required_zone_categories || []).join(", ");
  activeAssumptions = envelope.assumptions || {};
  document.querySelector("#scenario-note").textContent = activeAssumptions.screening_note || "";
}

async function initialise() {
  const [exampleResponse, datasetResponse] = await Promise.all([
    fetch("/api/examples"), fetch("/api/dataset"),
  ]);
  examples = await exampleResponse.json();
  const dataset = await datasetResponse.json();
  const status = document.querySelector(".data-status");
  status.innerHTML = `<i></i> ${dataset.connected ? `${dataset.parcel_count.toLocaleString()} real parcels connected` : "Parcel data unavailable"}`;
  document.querySelector(".hero-stat span").textContent = dataset.connected ? "491k" : "02";
  document.querySelector(".hero-stat p").innerHTML = dataset.connected ? "South Australian parcels<br />ready to screen" : "sample parcels<br />ready to screen";
  if (!dataset.connected) {
    fields.dataSource.value = "sample";
    fields.dataSource.querySelector('[value="connected"]').disabled = true;
  }
  setEnvelope(examples.townhouse);
}

presetButtons.forEach((button) => button.addEventListener("click", () => {
  presetButtons.forEach((item) => item.classList.remove("active"));
  button.classList.add("active");
  setEnvelope(examples[button.dataset.preset]);
}));

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const envelope = {
    name: fields.name.value, storeys: Number(fields.storeys.value),
    footprint_sqm: Number(fields.footprint.value),
    building_width_m: Number(fields.buildingWidth.value) || null,
    building_depth_m: Number(fields.buildingDepth.value) || null,
    building_height_m: Number(fields.buildingHeight.value) || null,
    minimum_site_area_sqm: Number(fields.siteArea.value) || null,
    maximum_design_site_coverage: Number(fields.designCoverage.value) ? Number(fields.designCoverage.value) / 100 : null,
    required_frontage_m: Number(fields.frontage.value) || 0,
    required_depth_m: Number(fields.depth.value) || 0,
    required_zone_categories: fields.zoneCategories.value.split(",").map((category) => category.trim()).filter(Boolean),
    assumptions: activeAssumptions,
  };
  const button = form.querySelector(".search-button span");
  button.textContent = "Screening parcels?";
  try {
    const response = await fetch("/api/candidates", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        envelope,
        parcels: examples.parcels,
        use_local_dataset: fields.dataSource.value === "connected",
        limit: 100,
      }),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || "Unable to screen parcels");
    renderResults(payload.results, payload.total_matches);
  } catch (error) {
    document.querySelector("#result-summary").textContent = error.message;
  } finally { button.textContent = "Find suitable sites"; }
});

function renderResults(results, totalMatches) {
  document.querySelector("#result-summary").textContent = `${totalMatches.toLocaleString()} matching parcels found; showing the first ${results.length}.`;
  document.querySelector("#results").innerHTML = results.map((result) => `
    <details class="result-card" data-parcel-id="${result.parcel.parcel_id}">
      <summary>
        <i class="result-status ${result.status}"></i>
        <div><strong>Parcel ${result.parcel.parcel_id}</strong><small>${Math.round(result.parcel.land_area_sqm)}m&sup2; &middot; ${result.parcel.planning.zone_name || result.parcel.planning.zone_code} &middot; ${result.status.toUpperCase()}</small></div>
        <span class="score">${Math.round(result.score * 100)}%</span>
      </summary>
      <ul>${result.outcomes.map((outcome) => `<li><strong>${outcome.status.toUpperCase()}</strong> — ${outcome.message}</li>`).join("")}</ul>
    </details>`).join("");
  renderMap(results);
}

function renderMap(results) {
  const svg = document.querySelector("#result-map");
  const empty = document.querySelector("#map-empty");
  const caption = document.querySelector("#map-caption");
  const mapped = results.filter((result) => Number.isFinite(result.parcel.map_x) && Number.isFinite(result.parcel.map_y));
  svg.replaceChildren();
  if (!mapped.length) {
    empty.style.display = "grid";
    empty.querySelector("strong").textContent = "No recorded geometry for these results";
    empty.querySelector("small").textContent = "Use the result list below; coordinates are never fabricated for sample parcels.";
    caption.textContent = `0 of ${results.length} returned results have recorded map geometry.`;
    return;
  }

  empty.style.display = "none";
  const xs = mapped.map((result) => result.parcel.map_x);
  const ys = mapped.map((result) => result.parcel.map_y);
  const minX = Math.min(...xs), maxX = Math.max(...xs);
  const minY = Math.min(...ys), maxY = Math.max(...ys);
  const xRange = maxX - minX || 1, yRange = maxY - minY || 1;
  mapped.forEach((result) => {
    const marker = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    marker.setAttribute("cx", String(40 + ((result.parcel.map_x - minX) / xRange) * 920));
    marker.setAttribute("cy", String(460 - ((result.parcel.map_y - minY) / yRange) * 420));
    marker.setAttribute("r", "7");
    marker.setAttribute("class", `map-marker ${result.status}`);
    marker.setAttribute("tabindex", "0");
    marker.setAttribute("role", "button");
    marker.setAttribute("aria-label", `Parcel ${result.parcel.parcel_id}, ${result.status}. Open screening reasons.`);
    marker.addEventListener("click", () => selectParcel(result.parcel.parcel_id, marker));
    marker.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") selectParcel(result.parcel.parcel_id, marker);
    });
    svg.appendChild(marker);
  });
  caption.textContent = `Showing ${mapped.length} returned parcel envelope centres in EPSG:7854; search is capped at ${results.length} displayed results.`;
}

function selectParcel(parcelId, marker) {
  document.querySelectorAll(".map-marker.selected,.result-card.selected").forEach((item) => item.classList.remove("selected"));
  marker.classList.add("selected");
  const card = document.querySelector(`.result-card[data-parcel-id="${CSS.escape(String(parcelId))}"]`);
  if (card) {
    card.classList.add("selected");
    card.open = true;
    card.scrollIntoView({behavior: "smooth", block: "nearest"});
  }
}

initialise();
