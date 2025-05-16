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