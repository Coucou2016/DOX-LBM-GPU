# Paste pack — Round 2 (Methods review)

**Same ChatGPT chat as Round 1 preferred.** Web search ON. Paste below.

---

Continue advising https://github.com/Coucou2016/DOX-LBM-GPU (web search ON).

**Methods audit request.** Review these design choices for accuracy and claim risk:

### A. λ-modified MS (inward current only)
```python
# cardiac_ms/ms_modified.py
# J_in = h * u * (u - λ) * (u_max - u) / τ_in
# When λ=0, u_max=1 → classical Mitchell–Schaeffer / finitewave calc_J_in
# Healthy paper default λ=0.01 (not 0)
# NOT claiming identity with Corrado full mMS (λ:=v_gate + outward gating)
```

### B. Cycle-required VA
```python
# cardiac_ms/protocol_s1s2.py :: classify_reentry
# require_cycle=True (default): VA iff n_extra_cycles≥1 OR n_probes_relapped≥3
# persist≥1000 ms alone is NOT VA; also persist is NOT required when cycle present
# require_cycle=False recovers paper-like persist≥1000 OR cycle
```

### C. Wavelength geometry
- Design APD=250 ms → λ_wave≈CV×APD≈0.70×250≈175 mm
- Measured 0D APD90≈256.6 ms (golden regression; report separately from design value)
- Small disc ~24 mm diameter → expected Non-VA (wavelength mismatch)
- Default pinned annulus path ≈107 mm (between healthy and strongly slowed wavelengths)

**Ask:** (1) any Methods wording that overclaims vs Villar-Valero; (2) whether cycle-required endpoint is publishable; (3) suggested Methods subsection titles.
