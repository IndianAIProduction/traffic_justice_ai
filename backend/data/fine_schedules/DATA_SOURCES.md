# Traffic Fine Data Sources & Verification Guide

## Data Confidence Levels

Each state fine schedule JSON includes a `confidence` field:

- **high** — Data verified against official gazette notification or government portal
- **medium** — Data based on reliable news sources, government press releases, or cross-referenced reports
- **low** — Data assumed to follow central rates; needs verification from official state sources

## High Confidence States (verified)
| State/UT | Source | Notes |
|----------|--------|-------|
| Central | Motor Vehicles (Amendment) Act, 2019 (No. 32 of 2019) | Official Act text from indiacode.nic.in |
| Delhi | Central Act (UT) | Follows central rates directly |
| Chandigarh | Central Act (UT) | Follows central rates directly |
| Haryana | State notification Sep 2019 | Among first to adopt full central rates |
| Karnataka | State notification 2019 | Largely central rates |
| Maharashtra | State notification 2019 | Largely central rates |
| Gujarat | State notification Oct 2019 | Well-documented reduction after backlash |
| Telangana | State notification 2019 | Advanced eChallan system |

## Medium Confidence States (needs periodic verification)
| State/UT | Source | Verification Needed |
|----------|--------|-------------------|
| Uttar Pradesh | State notification Dec 2019 | Verify exact reduced amounts |
| Rajasthan | State notification Oct 2019 | Verify specific reductions |
| Tamil Nadu | State notification 2020 | Verify delayed adoption amounts |
| West Bengal | Pre-2019 rates maintained | Verify if any sections updated post-2022 |
| Kerala | State notification 2019 | Verify partial reductions |
| Madhya Pradesh | State notification 2019 | Verify specific reductions |
| Punjab | State notification 2019-2020 | Verify delayed adoption amounts |
| Bihar | State notification 2019 | Verify central rate adoption |
| Odisha | State notification 2019 | Verify specific reductions |
| Goa | State notification 2019 | Verify reductions |
| Uttarakhand | State notification 2019 | Verify central rate adoption |
| Chhattisgarh | State notification 2020 | Verify delayed adoption |
| Jharkhand | State notification 2019 | Verify near-central rates |
| Himachal Pradesh | State notification 2019 | Verify central rate adoption |
| Assam | State notification 2019 | Verify with state portal |
| Jammu & Kashmir | Post-reorganisation Oct 2019 | Verify current implementation |
| Puducherry | Central Act (UT) | Verify enforcement |

## Low Confidence States (NE states, default to central)
| State | Notes |
|-------|-------|
| Sikkim | Limited available data; assumed central |
| Meghalaya | Limited available data; assumed central |
| Manipur | Limited available data; assumed central |
| Mizoram | Limited available data; assumed central |
| Nagaland | Limited available data; assumed central |
| Tripura | Limited available data; assumed central |
| Arunachal Pradesh | Limited available data; assumed central |

## Official Data Sources (for verification & updates)

### Central Government
1. **India Code** — https://indiacode.nic.in
   - Full text of Motor Vehicles Act 1988 + 2019 Amendment
   - Search for "Motor Vehicles Act"

2. **Parivahan (MoRTH)** — https://parivahan.gov.in
   - Ministry of Road Transport & Highways
   - Central fine schedules, vehicle data

3. **eChallan National Portal** — https://echallan.parivahan.gov.in
   - National eChallan system
   - State-wise fine amounts visible during challan generation

### State Transport Department Websites
| State | URL |
|-------|-----|
| Andhra Pradesh | https://aptransport.org |
| Assam | https://transport.assam.gov.in |
| Bihar | https://transport.bihar.gov.in |
| Chhattisgarh | https://transport.cg.gov.in |
| Delhi | https://transport.delhi.gov.in |
| Goa | https://goatransport.gov.in |
| Gujarat | https://rtogujarat.gov.in |
| Haryana | https://haryanatransport.gov.in |
| Himachal Pradesh | https://himachal.nic.in/transport |
| Jharkhand | https://jhtransport.gov.in |
| Karnataka | https://transport.karnataka.gov.in |
| Kerala | https://mvd.kerala.gov.in |
| Madhya Pradesh | https://transport.mp.gov.in |
| Maharashtra | https://transport.maharashtra.gov.in |
| Odisha | https://odishatransport.gov.in |
| Punjab | https://punjabtransport.org |
| Rajasthan | https://transport.rajasthan.gov.in |
| Tamil Nadu | https://tnsta.gov.in |
| Telangana | https://transport.telangana.gov.in |
| Uttar Pradesh | https://uptransport.upsdc.gov.in |
| Uttarakhand | https://transport.uk.gov.in |
| West Bengal | https://transport.wb.gov.in |

### Gazette Notifications
- **eGazette of India** — https://egazette.nic.in (central notifications)
- Each state has its own eGazette portal for state-specific notifications

### RTI (Right to Information)
- For any data not publicly available, file RTI requests through:
  - https://rtionline.gov.in (central)
  - State-level RTI portals

## How to Update Fine Data

1. Check the state transport department website for latest notifications
2. Cross-reference with the eChallan portal (echallan.parivahan.gov.in)
3. Update the corresponding `{state_name}.json` file in `backend/data/fine_schedules/`
4. Update the `confidence` field based on source reliability
5. Update the `effective_date` and `gazette_notification` fields
6. Run `python scripts/validate_fine_data.py` to check data integrity
7. Re-run the seed script: `python scripts/seed_fine_data.py`

## Legal Disclaimer

This data is provided for informational purposes and to help citizens verify if they are being overcharged.
Fine amounts may change through state gazette notifications at any time. Always verify with
official sources for the most current fine amounts. This application is not a substitute for legal advice.
