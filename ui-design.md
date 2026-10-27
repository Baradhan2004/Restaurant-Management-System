# UI design brief (build this in Figma and link it in the README)
Screens: 1 Login/role select · 2 Floor plan (table status colours: free/occupied/reserved) · 3 Order entry (category tabs, item grid, running total with GST) · 4 Kitchen display (open orders by age) · 5 Billing & payment (cash/card/UPI, tip) · 6 Reservations calendar · 7 Inventory (low-stock banner from `/inventory/low-stock`) · 8 Reports dashboard (daily revenue, top items, peak hours).
Design system: 8-pt grid, 2 type sizes per screen, status colours with text labels (not colour alone), min touch target 44 px.
Flows to prototype: seat guest → take order → send to kitchen → bill → pay; create reservation with conflict error state (maps to API `409`).
