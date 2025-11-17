This project builds a complete simulated rover environment and a 10-chapter interactive Streamlit learning console. Each component is designed for teaching: code is heavily commented, contains narrative explanations, ASCII diagrams, debugging notes, and future-improvement sections. The system is modular, extensible, and intended as a full-scale learning environment covering simulation, telemetry pipelines, anomaly detection, storage, and UI engineering.

Claude Code will implement this project strictly according to the PHASES and STEPS defined in this document.
Claude Code must not modify the README after Phase 1.
Every file it generates must include narrative header docstrings, detailed inline teaching commentary, diagrams, debugging tips, and extension notes.

⸻

	1.	TEACHING GOALS

⸻

PRIMARY GOALS:
	•	Architecture and modular system design
	•	Simulation modeling
	•	Telemetry pipeline engineering
	•	Data cleaning and anomaly detection
	•	Streamlit UI engineering

SECONDARY GOALS:
	•	Async programming
	•	Plotly/Matplotlib visualization
	•	Persistent state through SQLite and caches
	•	Code organization patterns and maintainability

⸻

	2.	HIGH-LEVEL ARCHITECTURE (ASCII DIAGRAM)
                     ┌────────────────────┐
                     │   Environment       │
                     │ (terrain, hazards)  │
                     └─────────┬──────────┘
                               │
                     ┌─────────▼──────────┐
                     │   Sensor Engine     │
                     └─────────┬──────────┘
                               │ frames
                ┌──────────────▼───────────────┐
                │       Packetizer Layer        │
                └──────────────┬───────────────┘
                               │ packets
                     ┌─────────▼──────────┐
                     │     Corruptor       │
                     └─────────┬──────────┘
                               │ degraded packets
          ┌────────────────────▼─────────────────────┐
          │      Cleaning & Validation Layer          │
          └────────────────────┬─────────────────────┘
                               │ clean frames
                    ┌──────────▼──────────┐
                    │   Anomaly Detector   │
                    └──────────┬──────────┘
                               │ labeled frames
       ┌───────────────────────▼─────────────────────────┐
       │               Storage & Archive                  │
       └───────────────────────┬─────────────────────────┘
                               │
                ┌──────────────▼───────────────┐
                │    Streamlit Mission Console   │
                └────────────────────────────────┘	3.	DIRECTORY STRUCTURE

⸻

meridian3/
streamlit_app/
Home.py
pages/
01_Sensors_and_Body.py
02_Time_and_Orbits.py
03_Noise_and_Wear.py
04_Terrain_and_Hazards.py
05_Packets_and_Loss.py
06_Cleaning_and_Validation.py
07_Anomaly_Detection.py
08_Mission_Console.py
09_Post_Mission_Archive.py
10_Engineering_Legacy.py
assets/
src/
simulator/
rover_state.py
sensors.py
environment.py
generator.py
pipeline/
packetizer.py
corruptor.py
cleaner.py
anomalies.py
storage.py
utils/
timing.py
math_helpers.py
plotting.py
config/
default_params.yaml
mission_templates/
data/
missions.sqlite
caches/
README.md

⸻

	4.	PROJECT PHASE PLAN (50 STEPS)

⸻

Claude Code will complete these phases only when explicitly instructed.
Do NOT execute future phases early.
Do NOT modify completed phases.
Do NOT alter the README.

All generated files must contain:
	•	Narrative header docstrings
	•	ASCII diagrams where relevant
	•	Inline teaching comments
	•	Debugging notes
	•	Future-extensions section

────────────────────────────────────────────────────────────
PHASE 1 — FOUNDATIONS (10 STEPS)
────────────────────────────────────────────────────────────
	1.	Create directory structure exactly as specified.
	2.	Create empty module files in simulator/, pipeline/, utils/, streamlit_app/.
	3.	Add header docstrings to each file describing its teaching purpose.
	4.	Add ASCII diagrams at the top of each major subsystem file.
	5.	Create RoverState class stub with full teaching commentary.
	6.	Create sensors.py stub with sensor class placeholders + teaching notes.
	7.	Create environment.py stub with terrain abstractions.
	8.	Create generator.py stub describing simulation loop design.
	9.	Initialize placeholder Streamlit pages with only top-level narrative headers.
	10.	Add default_params.yaml with annotated placeholder fields.

────────────────────────────────────────────────────────────
PHASE 2 — SIMULATOR CORE (10 STEPS)
────────────────────────────────────────────────────────────
11. Implement RoverState fields + example baseline values.
12. Implement deterministic + noise-based sensor models.
13. Implement terrain effects engine (tilt, traction, dust, CPU heat).
14. Add hazard event generation (dust burst, radiation spike, slip).
15. Build main simulation generator loop in generator.py.
16. Create teaching diagrams showing signal flow through simulator.
17. Add debugging helpers to visualize raw sensor output.
18. Implement timing utilities with commentary on timestep logic.
19. Implement math_helpers for drift, smoothing, and randomization.
20. Update relevant Streamlit pages to visualize simulator outputs.

────────────────────────────────────────────────────────────
PHASE 3 — TELEMETRY PIPELINE (10 STEPS)
────────────────────────────────────────────────────────────
21. Implement packetizer layer with timestamps + encoding metadata.
22. Implement corruptor with packet loss, jitter, field removal.
23. Build cleaning layer with range checks and interpolation.
24. Add anomaly detectors (threshold, derivative, z-score).
25. Implement storage layer (SQLite + JSON caching).
26. Add I/O teaching commentary explaining durability and failure modes.
27. Add diagrams showing pipeline progression of frames → packets → clean frames.
28. Update Streamlit pages (Packets, Cleaning, Anomalies).
29. Add mission archival logic.
30. Add debugging helpers for packet inspection.

────────────────────────────────────────────────────────────
PHASE 4 — STREAMLIT MISSION CONSOLE (10 STEPS)
────────────────────────────────────────────────────────────
31. Implement Home.py with full layout + narrative introducion.
32. Implement sensors tutorial page with interactive plots.
33. Implement time/orbit tutorial with diurnal cycle controls.
34. Implement noise/wear tutorial with sliders + visualizations.
35. Implement terrain/hazard pages with environment selectors.
36. Implement packets/loss page showing packet corruption in real-time.
37. Implement cleaning/validation page with toggles for strategies.
38. Implement anomaly detection demo with labeled events.
39. Implement mission console (live display + playback UI).
40. Implement mission archive browser.

────────────────────────────────────────────────────────────
PHASE 5 — FULL SYSTEM INTEGRATION & POLISH (10 STEPS)
────────────────────────────────────────────────────────────
41. Integrate simulator + pipeline into a single orchestrated runtime.
42. Add async/await version of the main loop if feasible.
43. Implement session_state wiring across pages.
44. Add cross-page data sharing utilities.
45. Create global plotting helpers with teaching commentary.
46. Optimize simulation tick rate + jitter behavior with explanations.
47. Add export/import options for mission configs.
48. Add final Engineering Legacy reference page.
49. Add full debugging suite (self-test functions).
50. Add future-extensions document and ensure all files contain extension hints.

⸻

	5.	IMPLEMENTATION RULES FOR CLAUDE CODE

⸻

	•	Do not modify this README after Phase 1.
	•	Complete exactly the steps in the phase requested.
	•	Each file must contain a narrative header docstring explaining:
	•	purpose
	•	theory
	•	analogy or story snippet from Meridian-3 (optional)
	•	architecture role
	•	teaching goals
	•	Use rich inline comments.
	•	Include ASCII diagrams in major modules.
	•	Include debugging notes.
	•	Include section on future improvements.
	•	Follow file structure exactly.
	•	Do not merge phases.
	•	Do not skip steps.
	•	Do not invent new directories unless required by a step.
	•	Keep code educational, not minimal.

⸻

	6.	DEVELOPER SETUP (INCLUDED FOR COMPLETENESS)

⸻

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run streamlit_app/Home.py

⸻

	7.	MISSION FLOW SUMMARY

⸻

	1.	Simulator generates sensor frames
	2.	Packetizer encodes frames
	3.	Corruptor applies degradation
	4.	Cleaner validates frames
	5.	Anomaly detector labels events
	6.	Storage archives mission
	7.	Streamlit Console visualizes results
