import gspread
from gspread_dataframe import get_as_dataframe
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import folium
from folium import Element
import json
from datetime import datetime
import calendar
from pathlib import Path


# Set up Google Sheet
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("jmt-bridge-inspection-7c14005fbc92.json", scope)
client = gspread.authorize(creds)

spreadsheet = client.open("JMT Inspection List")
sheet = spreadsheet.sheet1
df = get_as_dataframe(sheet).dropna(how="all").dropna(axis=1, how="all")



# Fill missing values
for col in ['STDs', 'Active Flags', 'Load Posting', 'Special Access', 'SpE', 'Flags Issued']:
    df[col] = df[col].fillna('None')



# Clean up BINs and other fields
def clean_bin(x):
    try:
        return str(int(x)) if isinstance(x, float) and x.is_integer() else str(x).strip()
    except:
        return ""
for col in ['BIN', 'Spans', 'Region', 'Prev GR']:
    df[col] = df[col].apply(clean_bin)

# Group by week label
def get_week_label(value):
    try:
        if pd.isna(value) or str(value).strip() == "":
            return "Unscheduled"
        
        # Ensure it's a string and add the implicit year
        mm_dd = str(value).strip()
        full_date_str = f"2025/{mm_dd}"  # prepend year
        dt = pd.to_datetime(full_date_str, format="%Y/%m/%d")

        # Get start of calendar week (Monday)
        monday = dt - pd.Timedelta(days=dt.weekday())
        return f"Week of {monday.strftime('%m-%d')}"
    except Exception as e:
        return "Unscheduled"


def get_due_month(value):
    try:
        if pd.isna(value) or str(value).strip() == "":
            return "Unscheduled"
        mm = str(value).strip().split("/")[0]
        return calendar.month_name[int(mm)]
    except:
        return "Unscheduled"



# Create data for injection
bridge_data = []
for _, row in df.iterrows():
    try:
        lat = float(row["Latitude"])
        lon = float(row["Longitude"])
        if pd.isna(lat) or pd.isna(lon):
            continue
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            continue
    except:
        continue

    bridge_data.append({
        "bin": str(row["BIN"]),
        "lat": lat,
        "lon": lon,
        "region": row.get("Region", ""),
        "county": row.get("County", ""),
        "due": str(row.get("Inspection Due Date", "")),
        "prev_gr": row.get("Prev GR", ""),
        "spans": row.get("Spans", ""),
        "flags": "Yes" if str(row.get("Active Flags", "None")).strip().lower() != "none" else "No",
        "flags_info": str(row.get("Active Flags", "None")).strip(),
        "posting": "Yes" if str(row.get("Load Posting", "None")).strip().lower() != "none" else "No",
        "posting_info": str(row.get("Load Posting", "None")).strip(),
        "access": "Yes" if str(row.get("Special Access", "None")).strip().lower() != "none" else "No",
        "access_info": str(row.get("Special Access", "None")).strip(),
        "spe": row.get("SpE", "None"),
        "stds": row.get("STDs", "No"),
        "field_time": row.get("Estimated Field Time", ""),
        "week": get_week_label(row.get("Proposed Field Date", "")),
        "completed": row.get("Inspection Completed Date", ""),
        "issued": row.get("Flags Issued", ""),
        "due_month": get_due_month(row.get("Inspection Due Date", "")),
    })





# Generate the map
ny_map = folium.Map(location=[43.0, -75.0], zoom_start=7)


ny_map.get_root().html.add_child(Element(f"""
<script>
const bridgeData = {json.dumps(bridge_data)};
</script>
"""))

# Save bridge data as a separate JSON file for use in GitHub Pages or Service Worker caching
json_output_path = Path("data/bridges.json")  # or use absolute path if needed
json_output_path.parent.mkdir(parents=True, exist_ok=True)  # create data/ folder if needed

with open(json_output_path, "w", encoding="utf-8") as f:
    json.dump(bridge_data, f, indent=2)


ny_map.get_root().html.add_child(Element("""
<style>
/* Sidebar modal */
#bridgeSidebarOverlay {
    display: none;
    position: fixed;
    z-index: 9998;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0,0,0,0.3);
}
#bridgeSidebar {
    height: 100%;
    width: 350px; /* set to your desired sidebar width */
    position: fixed;
    z-index: 9999;
    top: 0;
    right: 0;
    background-color: #fefefe;
    overflow-x: hidden;
    transition: transform 0.3s cubic-bezier(0.4,0,0.2,1);
    box-shadow: -2px 0 6px rgba(0, 0, 0, 0.2);
    transform: translateX(100%); /* hide by default */
}

#bridgeSidebar.open {
    transform: translateX(0); /* slide in */
}

#modal-body {
    padding: 20px;
}
@media (max-width: 500px) {
    #bridgeSidebar {
        width: 250px;
    }
}


/* BIN label style */
.bin-label {
    display: inline-block;
    font-size: 14px;
    font-weight: bold;
    color: white;
    background-color: rgba(0, 0, 0, 0.45);
    padding: 2px 6px;
    border-radius: 4px;
    white-space: nowrap;
    text-align: center;
    text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.8);
}


/* Searchbar */
#binSearchWrapper {
    position: absolute;
    top: 10px;
    left: 50px;
    z-index: 9999;
    background: white;
    padding: 6px 10px;
    border-radius: 6px;
    box-shadow: 0 1px 6px rgba(0,0,0,0.3);
}
#binSearchInput {
    width: 160px;
}


/* Toggles */
#panelHeaderWrapper {
    position: absolute;
    top: 80px;
    left: 10px;
    z-index: 9999;
    display: flex;
    gap: 10px;
}
.toggle-panel-btn {
    background-color: #ffffff;
    border: 1px solid #ccc;
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 13px;
    cursor: pointer;
    box-shadow: 0 1px 6px rgba(0, 0, 0, 0.3);
}


/* Filter Panel */
#filterPanelWrapper,
#dueSoonPanelWrapper {
    position: absolute;
    top: 115px;
    left: 10px;
    z-index: 9998;
    max-width: 265px;
}

#filterToggleBtn {
    background-color: #ffffff;
    border: 1px solid #ccc;
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 13px;
    cursor: pointer;
    box-shadow: 0 1px 6px rgba(0, 0, 0, 0.3);
}
.toggle-btn {
    font-size: 11px;
    margin-left: 8px;
    padding: 2px 6px;
    background: #eee;
    border: 1px solid #ccc;
    border-radius: 4px;
    cursor: pointer;
}

/* Main panel style */
#filterPanel {
    background: white;
    padding: 10px;
    border-radius: 6px;
    box-shadow: 0 1px 6px rgba(0,0,0,0.3);
    max-height: calc(100vh - 100px);
    overflow-y: auto;
    display: none; /* hidden by default on mobile */
}

/* Always show panel on desktop */
@media (min-width: 768px) {
}

/* Force one checkbox per line */
#filterPanel label {
    display: block;
    margin: 2px 0;
    font-size: 13px;
    white-space: nowrap;
}

/* Make sure each filter category container behaves vertically */
#filterPanel div[id^="filter-"] {
    display: block;
}

/* Due Soon Panel */
#dueSoonPanel {
    display: none;
    background: white;
    padding: 10px;
    border-radius: 6px;
    box-shadow: 0 1px 6px rgba(0, 0, 0, 0.2);
    font-size: 14px;
}

#dueSoonPanel input {
    width: 40px;
    margin: 0 5px;
}

@media (min-width: 768px) {
}

</style>




<!-- Sidebar Modal -->
<div id="bridgeSidebarOverlay" onclick="closeModal()"></div>
<div id="bridgeSidebar">
    <div id="modal-inner">
        <div id="modal-body"></div>
    </div>
</div>

<!-- Searchbar -->
<div id="binSearchWrapper">
    <input type="text" id="binSearchInput" list="binList" placeholder="Search BIN..." />
    <datalist id="binList"></datalist>
</div>

<!-- Filter Panel -->
<div id="panelHeaderWrapper">
    <button id="filterToggleBtn" class="toggle-panel-btn">🔽 Filters</button>
    <button id="dueSoonToggleBtn" class="toggle-panel-btn">🔽 Due Soon</button>
</div>
<div id="filterPanelWrapper">
  <div id="filterPanel">
    <h4>Active Flags <button class="toggle-btn" data-group="flags">All / None</button></h4>
    <div id="filter-flags"></div>
    <h4>Load Posting <button class="toggle-btn" data-group="posting">All / None</button></h4>
    <div id="filter-posting"></div>
    <h4>Special Access <button class="toggle-btn" data-group="access">All / None</button></h4>
    <div id="filter-access"></div>
    <h4>Field Week <button class="toggle-btn" data-group="week">All / None</button></h4>
    <div id="filter-week"></div>
    <h4>Due Month <button class="toggle-btn" data-group="due_month">All / None</button></h4>
    <div id="filter-due_month"></div>
  </div>
</div>

<!-- Due Soon -->
<div id="dueSoonPanelWrapper">
  <div id="dueSoonPanel">
    <label for="dueSoonDays">Show bridges due in next</label>
    <input type="number" id="dueSoonDays" value="14" min="1" />
    <span>days</span>
    <button id="applyDueSoon">Apply</button>
    <button id="clearDueSoon">Clear</button>
  </div>
</div>




<script>
document.addEventListener("DOMContentLoaded", function () {

    // Due Soon
    const filterToggleBtn = document.getElementById("filterToggleBtn");
    const dueSoonToggleBtn = document.getElementById("dueSoonToggleBtn");
    const filterPanel = document.getElementById("filterPanel");
    const dueSoonPanel = document.getElementById("dueSoonPanel");

    filterToggleBtn.addEventListener("click", () => {
        const filterVisible = filterPanel.style.display === "block";
        const dueSoonVisible = dueSoonPanel.style.display === "block";

        filterPanel.style.display = filterVisible ? "none" : "block";
        dueSoonPanel.style.display = "none";

        filterToggleBtn.textContent = filterVisible ? "🔽 Filters" : "🔼 Filters";
        dueSoonToggleBtn.textContent = "🔽 Due Soon";

        // Restore filter-based visibility if filters re-open
        if (!filterVisible && dueSoonVisible) {
            updateMarkers();
            updateBinLabelVisibility();
        }
    });

    dueSoonToggleBtn.addEventListener("click", () => {
        const dueSoonVisible = dueSoonPanel.style.display === "block";
        const filterVisible = filterPanel.style.display === "block";

        dueSoonPanel.style.display = dueSoonVisible ? "none" : "block";
        filterPanel.style.display = "none";

        dueSoonToggleBtn.textContent = dueSoonVisible ? "🔽 Due Soon" : "🔼 Due Soon";
        filterToggleBtn.textContent = "🔽 Filters";

        // Reapply standard filters if due soon was active and now closed
        if (!dueSoonVisible && filterVisible) {
            updateMarkers();
            updateBinLabelVisibility();
        }
    });


    document.getElementById("applyDueSoon").addEventListener("click", () => {
        const days = parseInt(document.getElementById("dueSoonDays").value, 10);
        const today = new Date();

        allMarkers.forEach(({ marker, data }) => {
            try {
                const inspected = data.completed && data.completed.trim() !== "";
                if (inspected) {
                    map.removeLayer(marker);
                    return;
                }

                const dueParts = data.due.split("/");
                const dueDate = new Date(2025, parseInt(dueParts[0]) - 1, parseInt(dueParts[1]));
                const diffDays = Math.ceil((dueDate - today) / (1000 * 60 * 60 * 24));

                if (diffDays >= 0 && diffDays <= days) {
                    map.addLayer(marker);
                } else {
                    map.removeLayer(marker);
                }
            } catch {
                map.removeLayer(marker);  // hide if bad/missing date
            }
        });

        updateBinLabelVisibility();  // keep labels in sync
    });


    document.getElementById("clearDueSoon").addEventListener("click", () => {
        updateMarkers(); // restores based on main filter logic
        updateBinLabelVisibility();
    });

    
    // Searchbar
    const input = document.getElementById("binSearchInput");
    const datalist = document.getElementById("binList");

    input.addEventListener("input", function () {
        const value = input.value.trim();
        datalist.innerHTML = "";

        if (value.length >= 3) {
            const matches = bridgeData
                .filter(({ bin }) => bin.startsWith(value))
                .slice(0, 50);

            matches.forEach(({ bin }) => {
                const opt = document.createElement("option");
                opt.value = bin;
                datalist.appendChild(opt);
            });
        }
    });
    input.addEventListener("change", function () {
        const value = input.value.trim();
        const match = bridgeData.find(b => b.bin === value);
        if (match) {
            map.setView([match.lat, match.lon], 16);
        } else {
            alert("BIN not found on map.");
        }
    });
    const map = Object.values(window).find(m => m instanceof L.Map);
    const markers = [];


    // Label visibility control
    function updateBinLabelVisibility() {
        const visible = map.getZoom() >= 11;
        document.querySelectorAll('.bin-label').forEach(el => {
            el.style.display = visible ? 'inline-block' : 'none';
        });
    }

    map.on("zoomend", updateBinLabelVisibility);
    map.whenReady(updateBinLabelVisibility);


    // Modal open/close
    window.showModal = function(bin) {
        const b = bridgeData.find(d => d.bin === bin);
        if (!b) return;
        const inspected = b.completed && b.completed.trim() !== "";

        const html = `
            <span style="font-size:16px;"><b><u>${b.bin}</u></b></span><br>
            <b>Coordinates:</b> <a href="https://www.google.com/maps/dir/?api=1&destination=${b.lat},${b.lon}" target="_blank" style="color:#1976d2;">${b.lat.toFixed(4)}, ${b.lon.toFixed(4)}</a><br>
            <b>Region:</b> ${b.region}<br>
            <b>County:</b> ${b.county}<br>
            <b>Due Date:</b> ${b.due}/25<br>
            <b>Previous Gen Rec:</b> ${b.prev_gr}<br>
            <b>Spans:</b> ${b.spans}<br>
            <b>Active Flags:</b> ${b.flags_info}<br>
            <b>Load Posting:</b> ${b.posting_info}<br>
            <b>Estimated Field Time:</b> ${b.field_time} hours<br>
            <b>Special Access:</b> ${b.access_info}<br>
            <b>Special Emphasis:</b> ${b.spe}<br>
            <b>New Standards:</b> ${b.stds}<br><br>
            ${inspected ? `<b>Inspection Completed Date:</b> ${b.completed}<br>` : ""}
            ${inspected ? `<b>Flags Issued:</b> ${b.issued}<br>` : ""}
        `;
            document.getElementById("modal-body").innerHTML = html;
            const sidebar = document.getElementById("bridgeSidebar");
            sidebar.classList.add("open");
            document.getElementById("bridgeSidebarOverlay").style.display = "block";
    };

    window.closeModal = function() {
        document.getElementById("bridgeSidebar").classList.remove("open");
        document.getElementById("bridgeSidebarOverlay").style.display = "none";
    };



    //Filtering
    const filters = {
        flags: new Set(),
        posting: new Set(),
        access: new Set(),
        week: new Set(),
        due_month: new Set()
    };

    const allMarkers = [];

    function createCheckbox(containerId, groupKey, values) {
        const container = document.getElementById(containerId);
        values.forEach(val => {
            const safeId = `${containerId}-${val.replace(/\\W+/g, "_")}`;
            const label = document.createElement("label");
            label.innerHTML = `<input type="checkbox" id="${safeId}" value="${val}" data-group="${groupKey}" checked> ${val}`;
            container.appendChild(label);
            filters[groupKey].add(val);  // start with everything selected
        });
    }

    // Gather unique values from bridgeData
    const unique = { flags: new Set(), posting: new Set(), access: new Set(), week: new Set(), due_month: new Set() };
    bridgeData.forEach(b => {
        unique.flags.add(b.flags);
        unique.posting.add(b.posting);
        unique.access.add(b.access);
        unique.week.add(b.week);
        unique.due_month.add(b.due_month);
    });

    const monthOrder = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ];

    function sortMonths(monthSet) {
        return Array.from(monthSet).sort(
            (a, b) => monthOrder.indexOf(a) - monthOrder.indexOf(b)
        );
    }

    function sortWeeks(weekSet) {
        return Array.from(weekSet).sort((a, b) => {
            const dateA = new Date("2025/" + a.replace("Week of ", ""));
            const dateB = new Date("2025/" + b.replace("Week of ", ""));
            return dateA - dateB;
        });
    }

    function pushUnscheduledToEnd(arr) {
        return arr.filter(v => v !== "Unscheduled").concat(
            arr.includes("Unscheduled") ? ["Unscheduled"] : []
        );
    }

    createCheckbox("filter-flags", "flags", unique.flags);
    createCheckbox("filter-posting", "posting", unique.posting);
    createCheckbox("filter-access", "access", unique.access);
    createCheckbox("filter-week", "week", pushUnscheduledToEnd(sortWeeks(unique.week)));
    createCheckbox("filter-due_month", "due_month", sortMonths(unique.due_month));



    // Function to check if a bridge passes all current filters
    function passesFilters(b) {
        return (
            filters.flags.has(b.flags) &&
            filters.posting.has(b.posting) &&
            filters.access.has(b.access) &&
            filters.week.has(b.week) &&
            filters.due_month.has(b.due_month)
        );
    }

    function updateMarkers() {
        allMarkers.forEach(({ marker, data }) => {
            if (passesFilters(data)) {
                if (!map.hasLayer(marker)) map.addLayer(marker);
            } else {
                if (map.hasLayer(marker)) map.removeLayer(marker);
            }
        });
    }

    // Hook up individual checkbox behavior
    document.querySelectorAll("#filterPanel input[type=checkbox]").forEach(cb => {
        cb.addEventListener("change", () => {
            const group = cb.dataset.group;
            const val = cb.value;
            if (cb.checked) {
                filters[group].add(val);
            } else {
                filters[group].delete(val);
            }
            updateMarkers();
            updateBinLabelVisibility();  // keep labels in sync
        });
    });

    //Hook up All/None button behavior
    document.querySelectorAll(".toggle-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            const group = btn.dataset.group;
            const checkboxes = document.querySelectorAll(`#filter-${group} input[type=checkbox]`);

            const allChecked = Array.from(checkboxes).every(cb => cb.checked);

            filters[group] = new Set();  // reset group

            checkboxes.forEach(cb => {
                cb.checked = !allChecked;
                if (!allChecked) {
                    filters[group].add(cb.value);
                }
            });

            updateMarkers();
            updateBinLabelVisibility();
        });
    });


    // Marker + popup creation
    bridgeData.forEach(b => {
        const inspected = b.completed && b.completed.trim() !== "";
        const icon = L.AwesomeMarkers.icon({
            icon: inspected ? "check" : "flag",
            prefix: "fa",
            markerColor: inspected ? "green" : "blue"
        });

        const popup = `
            <span style="font-size:16px;"><b><u>${b.bin}</u></b></span><br>
            <b>Coordinates:</b> <a href="https://www.google.com/maps/dir/?api=1&destination=${b.lat},${b.lon}" target="_blank" style="color:#1976d2;">${b.lat.toFixed(4)}, ${b.lon.toFixed(4)}</a><br>
            <b>New Standards:</b> ${b.stds}<br>
            <b>Due Date:</b> ${b.due}/25<br>
            <b>Active Flags:</b> ${b.flags}<br>
            <b>Load Posting:</b> ${b.posting_label}<br>
            <a href="#" onclick="showModal('${b.bin}'); return false;">See more…</a>
        `;

        const marker = L.marker([b.lat, b.lon], { icon })
            .bindTooltip(b.bin, { permanent: true, direction: 'right', className: 'bin-label' })
            .bindPopup(popup);

        marker.addTo(map);
        allMarkers.push({ marker, data: b });
    });

    updateBinLabelVisibility();
    updateMarkers();  // ensure correct initial state
});
</script>
"""))


# Save the map
output_path = r"G:\My Drive\2024-2025 JMT Bridge Inspection\2025\BridgeMapProject\Bridge Inspection Map.html"
ny_map.save(output_path)
print("Map saved")

# Reopen the saved file and inject manifest and service worker
with open(output_path, "r", encoding="utf-8") as f:
    html = f.read()

# Inject manifest and service worker tags
if '<link rel="manifest"' not in html:
    html = html.replace(
        "<head>",
        """<head>
    <link rel="manifest" href="manifest.json">
    <meta name="theme-color" content="#1976d2">"""
    )

if "navigator.serviceWorker.register" not in html:
    html = html.replace(
        "</body>",
        """<script>
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('service-worker.js')
    .then(() => console.log("✅ Service Worker registered"))
    .catch(err => console.error("Service Worker failed:", err));
}
</script>
</body>"""
    )

# Save the modified HTML
with open(output_path, "w", encoding="utf-8") as f:
    f.write(html)
