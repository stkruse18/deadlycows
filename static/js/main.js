document.addEventListener('DOMContentLoaded', () => {
    // 1. Floating Cow Animation System
    initFloatingCows();

    // 2. Interactive Emoji Explosions
    initEmojiExplosions();

    // 3. Stats Table Sorting
    initTableSorting();

    // 4. Admin Points Auto-Summing
    initAdminAutoSum();
});

/* -------------------------------------------------------------
 * 1. FLOATING COWS SYSTEM
 * Spawns a floating cow emoji at random intervals drifting across
 * ------------------------------------------------------------- */
function initFloatingCows() {
    const container = document.getElementById('animation-container');
    if (!container) return;

    const emojis = ['🐮', '🐄', '🥛', '🌾'];

    function spawnCow() {
        // Limit active floating elements to prevent lagging
        if (container.children.length > 8) return;

        const cow = document.createElement('div');
        cow.className = 'floating-cow-emoji';
        
        // Random emoji selection
        cow.innerText = emojis[Math.floor(Math.random() * emojis.length)];

        // Random starting Y position (avoiding absolute header and footer)
        const startY = Math.random() * 80 + 10; // percentage
        cow.style.top = `${startY}vh`;
        cow.style.left = `-100px`;

        // Random sizing (1.5rem to 3.5rem)
        const size = Math.random() * 2 + 1.5;
        cow.style.fontSize = `${size}rem`;

        // Random animation duration (15s to 30s)
        const duration = Math.random() * 15 + 15;
        cow.style.animationDuration = `${duration}s`;

        container.appendChild(cow);

        // Remove element after animation completes
        setTimeout(() => {
            cow.remove();
        }, duration * 1000);
    }

    // Spawn first cow quickly, then set periodic interval
    setTimeout(spawnCow, 1000);
    setInterval(spawnCow, 7000);
}

/* -------------------------------------------------------------
 * 2. EMOJI BURSTS / EXPLOSIONS
 * Creates particles flying out from clicks on MVP and LVP cards
 * ------------------------------------------------------------- */
function initEmojiExplosions() {
    const mvpCard = document.querySelector('.spotlight-mvp');
    const lvpCard = document.querySelector('.spotlight-lvp');

    if (mvpCard) {
        mvpCard.addEventListener('click', (e) => {
            const rect = mvpCard.getBoundingClientRect();
            // Centered on the click or card center
            const x = e.clientX || (rect.left + rect.width / 2);
            const y = e.clientY || (rect.top + rect.height / 2);
            createBurst(x, y, ['🐮', '👑', '🔥', '🏀', '🥛']);
        });
    }

    if (lvpCard) {
        lvpCard.addEventListener('click', (e) => {
            const rect = lvpCard.getBoundingClientRect();
            const x = e.clientX || (rect.left + rect.width / 2);
            const y = e.clientY || (rect.top + rect.height / 2);
            createBurst(x, y, ['🥛', '❌', '🐄', '💨', '⚠️']);
        });
    }
}

function createBurst(x, y, particlesList) {
    const particleCount = 20;
    for (let i = 0; i < particleCount; i++) {
        const p = document.createElement('div');
        p.innerText = particlesList[Math.floor(Math.random() * particlesList.length)];
        p.style.position = 'fixed';
        p.style.left = `${x}px`;
        p.style.top = `${y}px`;
        p.style.fontSize = `${Math.random() * 1.5 + 1}rem`;
        p.style.pointerEvents = 'none';
        p.style.zIndex = '10000';
        p.style.transition = 'all 1s cubic-bezier(0.1, 0.8, 0.3, 1)';
        
        // Calculate random vector direction
        const angle = Math.random() * Math.PI * 2;
        const velocity = Math.random() * 120 + 60; // speed
        const targetX = Math.cos(angle) * velocity;
        const targetY = Math.sin(angle) * velocity;

        document.body.appendChild(p);

        // Apply transition translation and opacity fade
        requestAnimationFrame(() => {
            p.style.transform = `translate(${targetX}px, ${targetY}px) rotate(${Math.random() * 720}deg)`;
            p.style.opacity = '0';
        });

        // Clean up
        setTimeout(() => p.remove(), 1000);
    }
}

/* -------------------------------------------------------------
 * 3. STATS TABLE SORTING
 * Allows tables with class 'sortable' to sort by numbers/strings
 * ------------------------------------------------------------- */
function initTableSorting() {
    const tables = document.querySelectorAll('table.stats-table');
    tables.forEach(table => {
        const headers = table.querySelectorAll('th.sortable');
        headers.forEach(header => {
            header.addEventListener('click', () => {
                const columnIndex = Array.from(header.parentNode.children).indexOf(header);
                const isDescending = !header.classList.contains('sort-desc');
                
                // Clear all active sorting header classes
                headers.forEach(h => {
                    h.classList.remove('sort-asc', 'sort-desc');
                    h.style.color = ''; // reset color
                });

                header.classList.add(isDescending ? 'sort-desc' : 'sort-asc');
                header.style.color = '#39ff14'; // highlight active sort

                sortRows(table, columnIndex, isDescending);
            });
        });
    });
}

function sortRows(table, columnIndex, desc) {
    const tbody = table.querySelector('tbody');
    if (!tbody) return;
    const rows = Array.from(tbody.querySelectorAll('tr'));

    rows.sort((rowA, rowB) => {
        let cellA = rowA.children[columnIndex].textContent.trim();
        let cellB = rowB.children[columnIndex].textContent.trim();

        // Remove jerseys or percent signs for pure numbers if necessary
        cellA = cellA.replace(/%/, '');
        cellB = cellB.replace(/%/, '');

        // Convert to floats if they are numbers
        const numA = parseFloat(cellA);
        const numB = parseFloat(cellB);

        if (!isNaN(numA) && !isNaN(numB)) {
            return desc ? numB - numA : numA - numB;
        }

        // Fallback string sort
        return desc 
            ? cellB.localeCompare(cellA) 
            : cellA.localeCompare(cellB);
    });

    // Re-append rows in new sorted order
    rows.forEach(row => tbody.appendChild(row));
}

/* -------------------------------------------------------------
 * 4. ADMIN AUTO-SUM SCORE
 * Sums up individual player points to compute Cows Score dynamically
 * ------------------------------------------------------------- */
function initAdminAutoSum() {
    const pointsInputs = document.querySelectorAll('.player-points-input');
    const cowsScoreInput = document.getElementById('cows_score');
    
    if (pointsInputs.length === 0 || !cowsScoreInput) return;

    function sumPoints() {
        let total = 0;
        pointsInputs.forEach(input => {
            // Find checkbox in the same row
            const tr = input.closest('tr');
            const playedCheckbox = tr ? tr.querySelector('.player-played-checkbox') : null;
            
            // Only count points if the player has played
            const played = playedCheckbox ? playedCheckbox.checked : true;

            if (played) {
                total += parseInt(input.value || 0);
            }
        });
        cowsScoreInput.value = total;
    }

    // Attach listeners to points inputs
    pointsInputs.forEach(input => {
        input.addEventListener('input', sumPoints);
    });

    const playedCheckboxes = document.querySelectorAll('.player-played-checkbox');
    playedCheckboxes.forEach(checkbox => {
        const updateRowState = () => {
            const tr = checkbox.closest('tr');
            if (tr) {
                tr.classList.toggle('player-inactive', !checkbox.checked);
                // Enable/disable all other inputs inside this row
                const rowInputs = tr.querySelectorAll('input:not(.player-played-checkbox)');
                rowInputs.forEach(inp => {
                    inp.disabled = !checkbox.checked;
                });
            }
        };

        checkbox.addEventListener('change', () => {
            updateRowState();
            sumPoints();
        });

        // Run initial setup for each row on page load
        updateRowState();
    });

    // Trigger initial sum on load to align values if editing
    sumPoints();
}
