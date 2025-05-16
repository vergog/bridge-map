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