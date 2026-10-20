# Primary references and attribution

Sources checked during package preparation, September 2026. Product stock,
prices and instrument compatibility are not guaranteed by this package.

- [Coilcraft 0603HP SPICE model](https://www.coilcraft.com/getmedia/353e55d2-1d20-470a-9567-550d989b0e5d/spice_0603hp.pdf): topology and typical parameter fits used in `rf915.py`. PCB effects still require evaluation.
- [Coilcraft 15 nH part](https://www.coilcraft.com/en-us/products/rf/ceramic-core-chip-inductors/0603-(1608)/0603hp/0603hp-15n/) and [1.8 nH part](https://www.coilcraft.com/en-us/products/rf/ceramic-core-chip-inductors/0603-(1608)/0603hp/0603hp-1n8/): component family, order-code variants and tolerance selection.
- [Johanson 10 pF part specification](https://www.johansondielectrics.com/search/pn-pdf/QSCF500Q100J1GV001T/): active identifier, 0402 C0G, 50 V, +/-5%, cross-reference to 500R07S100JV4T.
- [Microchip RF reference-design user guide](https://ww1.microchip.com/downloads/aemDocuments/documents/OTH/ProductDocuments/UserGuides/70005123A.pdf): BOM identifies Johanson 500R07S1R8BV4T as a 1.8 pF 0402 part. [Johanson high-Q 0402 family](https://www.johansontechnology.com/products/rf-capacitors/high-q-multilayer-capacitors/0402-sseries/) provides family information. Verify the current orderable code and tolerance before substitution.
- [Amphenol 132134 mechanical drawing](https://www.amphenolrf.com/library/download/link/link_id/593003/parent/132134/): vertical SMA lead pattern and physical dimensions.
- [NanoVNA calibration guidance](https://nanovna.com/?page_id=2), [measurement guidance](https://nanovna.com/?page_id=64), [software information](https://nanovna.com/?page_id=90).
- [NanoVNA-Saver project](https://github.com/NanoVNA-Saver/nanovna-saver): instrument support, acquisition and Touchstone export documentation. Check the current release against your exact model.
- [KiCad 9 CLI documentation](https://docs.kicad.org/9.0/en/cli/cli.html): ERC, DRC and fabrication exports. Local `kicad-cli --help` was used for installed-version options.
- [KiCad library license](https://www.kicad.org/libraries/license/): the three vendored standard footprints originate from KiCad 9 libraries and retain their source metadata; consult the library license and exception for redistribution. Custom circuit/software/report text is project material, not a claim of ownership over vendor documentation.

Manufacturer PDFs retained in `references/` are reference documents, not original
project work. The distributable project ZIP excludes downloaded vendor PDFs and
intermediate reference screenshots; use these links to obtain current copies.
