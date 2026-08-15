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
  document.querySelector("#map-empty").style.display = "none";
  document.querySelectorAll(".pin").forEach((pin) => pin.remove());
  const passing = results.filter((result) => result.status !== "fail").length;
  document.querySelector("#result-summary").textContent = `${totalMatches.toLocaleString()} matching parcels found; showing the first ${results.length}.`;
  const map = document.querySelector("#map");
  results.slice(0, 12).forEach((result, index) => {
    const pin = document.createElement("span");
    pin.className = `pin ${index % 2 ? "two" : "one"} ${result.status === "fail" ? "fail" : ""}`;
    pin.title = result.parcel.address || result.parcel.parcel_id;
    map.appendChild(pin);
  });
  document.querySelector("#results").innerHTML = results.map((result) => `
    <details class="result-card">
      <summary>
        <i class="result-status ${result.status === "fail" ? "fail" : ""}"></i>
        <div><strong>Parcel ${result.parcel.parcel_id}</strong><small>${Math.round(result.parcel.land_area_sqm)}m&sup2; &middot; ${result.parcel.planning.zone_name || result.parcel.planning.zone_code} &middot; ${result.status.toUpperCase()}</small></div>
        <span class="score">${Math.round(result.score * 100)}%</span>
      </summary>
      <ul>${result.outcomes.map((outcome) => `<li><strong>${outcome.status.toUpperCase()}</strong> — ${outcome.message}</li>`).join("")}</ul>
    </details>`).join("");
}

initialise();
