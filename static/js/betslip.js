// Betslip JS Controller for Cow Book Sportsbook

document.addEventListener("DOMContentLoaded", function() {
    let betslip = [];
    let activeTab = 'singles'; // 'singles' or 'parlay'
    const storageKey = 'deadly_cows_betslip';

    // Load from local storage on load
    try {
        const saved = localStorage.getItem(storageKey);
        if (saved) {
            betslip = JSON.parse(saved);
        }
    } catch (e) {
        console.error("Error loading betslip", e);
    }

    // Odds Conversions
    function americanToDecimal(odds) {
        if (odds > 0) {
            return (odds / 100) + 1;
        } else {
            return (100 / Math.abs(odds)) + 1;
        }
    }

    function decimalToAmerican(decimal) {
        if (decimal >= 2.0) {
            return Math.round((decimal - 1) * 100);
        } else {
            return Math.round(-100 / (decimal - 1));
        }
    }

    function calculateParlayOdds(selections) {
        if (selections.length === 0) return 0;
        let totalDecimal = 1.0;
        selections.forEach(sel => {
            totalDecimal *= americanToDecimal(sel.odds);
        });
        return decimalToAmerican(totalDecimal);
    }

    function saveBetslip() {
        localStorage.setItem(storageKey, JSON.stringify(betslip));
        updateSelectionButtonsUI();
        renderBetslip();
    }

    // Add / Toggle selection
    window.toggleSelection = function(propId, description, selection, odds, lineValue) {
        propId = parseInt(propId);
        odds = parseInt(odds);
        
        // Find if selection on this prop already exists
        const existingIdx = betslip.findIndex(item => item.propId === propId);
        
        if (existingIdx > -1) {
            const existing = betslip[existingIdx];
            if (existing.selection === selection) {
                // Clicking same selection -> remove it
                betslip.splice(existingIdx, 1);
            } else {
                // Clicking opposite selection -> switch selection and update odds
                existing.selection = selection;
                existing.odds = odds;
            }
        } else {
            // Add new selection
            betslip.push({
                propId: propId,
                description: description,
                selection: selection,
                odds: odds,
                lineValue: lineValue,
                wager: ''
            });
        }
        
        // If betslip contains multiple selections and we only have 1, default back to singles
        if (betslip.length < 2 && activeTab === 'parlay') {
            activeTab = 'singles';
        }
        
        saveBetslip();
    };

    window.removeSelection = function(propId) {
        betslip = betslip.filter(item => item.propId !== propId);
        if (betslip.length < 2 && activeTab === 'parlay') {
            activeTab = 'singles';
        }
        saveBetslip();
    };

    window.clearBetslip = function() {
        betslip = [];
        activeTab = 'singles';
        saveBetslip();
    };

    function updateSelectionButtonsUI() {
        // Clear all active classes
        document.querySelectorAll('.selection-label-btn').forEach(btn => {
            btn.classList.remove('active');
        });

        // Add active classes for current selections
        betslip.forEach(item => {
            const id = `btn-${item.propId}-${item.selection}`;
            const btn = document.getElementById(id);
            if (btn) {
                btn.classList.add('active');
            }
        });
    }

    function renderBetslip() {
        const betslipEl = document.getElementById('betslip-container');
        if (!betslipEl) return;

        // If no selections
        if (betslip.length === 0) {
            betslipEl.innerHTML = `
                <div class="betslip-empty-state">
                    <span style="font-size: 2.5rem; display: block; margin-bottom: 0.5rem;">🎫</span>
                    <p>Your Betslip is Empty</p>
                    <p style="font-size: 0.75rem; color: var(--text-secondary); margin-top: 0.2rem;">Click on any odds button to add a selection.</p>
                </div>
            `;
            // Hide betslip actions
            const actionsEl = document.getElementById('betslip-actions-section');
            if (actionsEl) actionsEl.style.display = 'none';
            return;
        }

        // Show betslip actions
        const actionsEl = document.getElementById('betslip-actions-section');
        if (actionsEl) actionsEl.style.display = 'block';

        let html = '';

        // Tab Headers
        html += `
            <div class="betslip-tabs">
                <button class="betslip-tab-btn ${activeTab === 'singles' ? 'active' : ''}" onclick="setBetslipTab('singles')">
                    Singles (${betslip.length})
                </button>
                <button class="betslip-tab-btn ${activeTab === 'parlay' ? 'active' : ''}" ${betslip.length < 2 ? 'disabled style="opacity: 0.4; cursor: not-allowed;" title="Add at least 2 legs to parlay"' : ''} onclick="setBetslipTab('parlay')">
                    Parlay ${betslip.length >= 2 ? `(${betslip.length} Legs)` : ''}
                </button>
            </div>
        `;

        if (activeTab === 'singles') {
            // Render singles list
            html += `<div class="betslip-legs-list">`;
            betslip.forEach(item => {
                const formattedSelection = item.selection === 'over' ? `Over ${item.lineValue}` :
                                            item.selection === 'under' ? `Under ${item.lineValue}` :
                                            item.selection === 'yes' ? 'Yes / Win' : 'No / Loss';
                const sign = item.odds > 0 ? '+' : '';

                html += `
                    <div class="betslip-leg-card">
                        <div class="betslip-leg-header">
                            <strong>${formattedSelection}</strong>
                            <span class="betslip-leg-odds">${sign}${item.odds}</span>
                            <button class="betslip-leg-remove" onclick="removeSelection(${item.propId})">&times;</button>
                        </div>
                        <div class="betslip-leg-desc">${item.description}</div>
                        <div class="betslip-leg-input-row" style="margin-top: 0.8rem; display: flex; align-items: center; justify-content: space-between; gap: 1rem;">
                            <label style="font-size: 0.8rem; color: var(--text-secondary);">Risk amount ($)</label>
                            <input type="number" class="betslip-wager-input" data-prop-id="${item.propId}" value="${item.wager}" oninput="updateSingleWager(${item.propId}, this.value)" placeholder="Wager" min="1" style="width: 100px; padding: 0.4rem; background: rgba(0,0,0,0.4); border: 1px solid var(--border-color); color: var(--text-primary); border-radius: 4px; font-family: var(--font-mono); text-align: right;">
                        </div>
                        <div style="text-align: right; font-size: 0.8rem; color: var(--neon-green); margin-top: 0.4rem; font-family: var(--font-mono);">
                            To Win: $<span id="payout-${item.propId}">${calculateSinglePayout(item.wager, item.odds)}</span>
                        </div>
                    </div>
                `;
            });
            html += `</div>`;
        } else {
            // Render Parlay mode
            html += `<div class="betslip-legs-list">`;
            betslip.forEach(item => {
                const formattedSelection = item.selection === 'over' ? `Over ${item.lineValue}` :
                                            item.selection === 'under' ? `Under ${item.lineValue}` :
                                            item.selection === 'yes' ? 'Yes / Win' : 'No / Loss';
                const sign = item.odds > 0 ? '+' : '';

                html += `
                    <div class="betslip-leg-card" style="padding-bottom: 0.6rem; margin-bottom: 0.5rem; border-bottom: 1px solid rgba(255,255,255,0.03);">
                        <div class="betslip-leg-header" style="font-size: 0.9rem;">
                            <strong>${formattedSelection}</strong>
                            <span class="betslip-leg-odds" style="color: var(--text-secondary); font-size: 0.8rem;">${sign}${item.odds}</span>
                            <button class="betslip-leg-remove" onclick="removeSelection(${item.propId})">&times;</button>
                        </div>
                        <div class="betslip-leg-desc" style="font-size: 0.75rem;">${item.description}</div>
                    </div>
                `;
            });
            html += `</div>`;

            // Parlay Summary Card
            const parlayOdds = calculateParlayOdds(betslip);
            const parlaySign = parlayOdds > 0 ? '+' : '';
            const parlayWagerInputVal = document.getElementById('parlay-wager-amount') ? document.getElementById('parlay-wager-amount').value : '';

            html += `
                <div class="betslip-parlay-card" style="background: rgba(157, 0, 255, 0.08); border: 1px solid rgba(157, 0, 255, 0.3); border-radius: 6px; padding: 1rem; margin-top: 1rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                        <span style="font-family: var(--font-header); text-transform: uppercase; font-size: 0.9rem; color: var(--text-primary); text-shadow: 0 0 5px rgba(157, 0, 255, 0.3);">🔗 Parlay Combined</span>
                        <strong style="color: var(--text-highlight); font-family: var(--font-mono); font-size: 1.1rem;">${parlaySign}${parlayOdds}</strong>
                    </div>
                    <div style="display: flex; align-items: center; justify-content: space-between; gap: 1rem; margin-top: 0.8rem;">
                        <label style="font-size: 0.8rem; color: var(--text-secondary);">Risk amount ($)</label>
                        <input type="number" id="parlay-wager-amount" class="betslip-wager-input" value="${parlayWagerInputVal}" oninput="updateParlayPayout(this.value, ${parlayOdds})" placeholder="Wager" min="1" style="width: 100px; padding: 0.4rem; background: rgba(0,0,0,0.4); border: 1px solid rgba(157, 0, 255, 0.5); color: var(--text-primary); border-radius: 4px; font-family: var(--font-mono); text-align: right;">
                    </div>
                    <div style="text-align: right; font-size: 0.85rem; color: var(--neon-green); margin-top: 0.6rem; font-family: var(--font-mono); font-weight: bold;">
                        To Win: $<span id="parlay-total-payout">${calculateParlayPayoutVal(parlayWagerInputVal, parlayOdds)}</span>
                    </div>
                </div>
            `;
        }

        betslipEl.innerHTML = html;
    }

    window.setBetslipTab = function(tab) {
        activeTab = tab;
        saveBetslip();
    };

    window.updateSingleWager = function(propId, val) {
        const item = betslip.find(i => i.propId === propId);
        if (item) {
            item.wager = val;
            localStorage.setItem(storageKey, JSON.stringify(betslip));
            const payoutSpan = document.getElementById(`payout-${propId}`);
            if (payoutSpan) {
                payoutSpan.textContent = calculateSinglePayout(val, item.odds);
            }
        }
    };

    function calculateSinglePayout(wager, odds) {
        if (!wager || isNaN(wager) || wager <= 0) return '0';
        wager = parseFloat(wager);
        let win = 0;
        if (odds > 0) {
            win = wager * (odds / 100.0);
        } else {
            win = wager * (100.0 / Math.abs(odds));
        }
        return Math.round(win + wager);
    }

    window.updateParlayPayout = function(val, combinedOdds) {
        const payoutSpan = document.getElementById('parlay-total-payout');
        if (payoutSpan) {
            payoutSpan.textContent = calculateParlayPayoutVal(val, combinedOdds);
        }
    };

    function calculateParlayPayoutVal(wager, combinedOdds) {
        if (!wager || isNaN(wager) || wager <= 0) return '0';
        wager = parseFloat(wager);
        let win = 0;
        if (combinedOdds > 0) {
            win = wager * (combinedOdds / 100.0);
        } else {
            win = wager * (100.0 / Math.abs(combinedOdds));
        }
        return Math.round(win + wager);
    }

    // Submit Betslip
    window.submitBetslip = function() {
        const submitBtn = document.getElementById('betslip-submit-btn');
        const errorEl = document.getElementById('betslip-error-msg');
        
        if (errorEl) {
            errorEl.style.display = 'none';
            errorEl.textContent = '';
        }

        if (betslip.length === 0) return;

        let payload = {};
        
        if (activeTab === 'parlay') {
            const wagerVal = document.getElementById('parlay-wager-amount') ? document.getElementById('parlay-wager-amount').value : '';
            const wagerAmount = parseInt(wagerVal);
            if (isNaN(wagerAmount) || wagerAmount <= 0) {
                showError("Please enter a valid wager amount.");
                return;
            }

            payload = {
                is_parlay: true,
                parlay_wager: wagerAmount,
                selections: betslip.map(item => ({
                    prop_id: item.propId,
                    selection: item.selection
                }))
            };
        } else {
            // Singles
            const selections = [];
            let hasError = false;

            betslip.forEach(item => {
                const wagerVal = parseInt(item.wager);
                if (isNaN(wagerVal) || wagerVal <= 0) {
                    hasError = true;
                }
                selections.push({
                    prop_id: item.propId,
                    selection: item.selection,
                    wager_amount: wagerVal
                });
            });

            if (hasError) {
                showError("Please enter wager amounts for all selections.");
                return;
            }

            payload = {
                is_parlay: false,
                selections: selections
            };
        }

        // Disable submit button
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.textContent = 'Submitting...';
        }

        fetch('/betting/place-bets', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        })
        .then(response => response.json().then(data => ({ status: response.status, body: data })))
        .then(res => {
            if (res.status === 200 && res.body.success) {
                alert("🎟️ Bets placed successfully!");
                clearBetslip();
                window.location.reload(); // Reload to refresh balance and ticket list
            } else {
                showError(res.body.message || "An error occurred placing your bet.");
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.textContent = 'Submit Wagers';
                }
            }
        })
        .catch(err => {
            console.error(err);
            showError("Network error. Please try again.");
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Submit Wagers';
            }
        });
    };

    function showError(msg) {
        const errorEl = document.getElementById('betslip-error-msg');
        if (errorEl) {
            errorEl.style.display = 'block';
            errorEl.textContent = msg;
        }
    }

    // Initial render call
    saveBetslip();
});
