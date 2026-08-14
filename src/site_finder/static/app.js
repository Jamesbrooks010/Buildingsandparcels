const form = document.querySelector("#search-form");
const presetButtons = document.querySelectorAll(".preset");
const fields = {
  name: document.querySelector("#name"), storeys: document.querySelector("#storeys"),
  footprint: document.querySelector("#footprint"), siteArea: document.querySelector("#site-area"),
  frontage: document.querySelector("#frontage"), depth: document.querySelector("#depth"),
  zones: document.querySelector("#zones"),
};
let examples;

function setEnvelope(envelope) {
  fields.name.value = envelope.name;
  fields.storeys.value = envelope.storeys;
  fields.footprint.value = envelope.footprint_sqm;
  fields.siteArea.value = envelope.minimum_site_area_sqm || "";
  fields.frontage.value = envelope.required_frontage_m || "";
  fields.depth.value = envelope.required_depth_m || "";
  fields.zones.value = (envelope.required_zone_codes || []).join(", ");
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
    minimum_site_area_sqm: Number(fields.siteArea.value) || null,
    required_frontage_m: Number(fields.frontage.value) || 0,
    required_depth_m: Number(fields.depth.value) || 0,
    required_zone_codes: fields.zones.value.split(",").map((zone) => zone.trim()).filter(Boolean),
  };
  const button = form.querySelector(".search-button span");
  button.textContent = "Screening parcels?";
  try {
    const response = await fetch("/api/candidates", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ envelope, use_local_dataset: true, limit: 100 }),
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
    <article class="result-card">
      <i class="result-status ${result.status === "fail" ? "fail" : ""}"></i>
      <div><strong>Parcel ${result.parcel.parcel_id}</strong><small>${Math.round(result.parcel.land_area_sqm)}m&sup2; &middot; ${result.parcel.planning.zone_name || result.parcel.planning.zone_code} &middot; ${result.status.toUpperCase()}</small></div>
      <span class="score">${Math.round(result.score * 100)}%</span>
    </article>`).join("");
}

initialise();
