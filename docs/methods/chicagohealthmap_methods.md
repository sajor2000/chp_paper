# Archived Chicago Health Map methods

This document records statements made by the Chicago Health Map website in the
2026-07-13 archive snapshot. It preserves historical claims as evidence; it does not
independently validate them. Citations name the snapshot date and exact ZIP member.

## Clinical source systems and coverage

The site states that CAPriCORN is the primary clinical source and that seven health
systems contribute diagnosis data: Rush University System for Health, Northwestern
Medicine, UChicago Medicine, University of Illinois Hospital & Health Sciences System,
Cook County Health, AllianceChicago, and Endeavor Health. It also states that all seven
systems use the PCORnet Common Data Model and contribute structured demographics,
diagnoses, encounters, and address-history data. [Snapshot 2026-07-13; member
`019f5daa-1fda-75df-b2c2-89792bc47700/chicagohealthmap.com_data-glossary.md`.]

The stated clinical coverage period is January 1, 2019 through December 31, 2024, for
Cook, DuPage, Lake, Will, Kane, and McHenry counties. The included population is adults
age 18 and older who visited a CAPriCORN hospital, clinic, or emergency room at least
once during 2019–2024 and received a diagnosis of at least one condition of interest.
[Snapshot 2026-07-13; members
`019f5daa-1fda-75df-b2c2-89792bc47700/chicagohealthmap.com_data-glossary.md` and
`019f5daa-1fda-75df-b2c2-89792bc47700/chicagohealthmap.com_.md`.]

For the capture-rate denominator, the site defines capture rate as health-system
patients divided by the ACS census-tract adult population. It describes this as the
proportion of the tract's adult population seen at participating health systems in a
given year. [Snapshot 2026-07-13; member
`019f5daa-1fda-75df-b2c2-89792bc47700/chicagohealthmap.com_data-glossary.md`.]

## Person and condition definitions

The site states that MRAIA matches anonymized codes across all seven health systems so
that a person appearing at multiple hospitals is counted once. [Snapshot 2026-07-13;
member
`019f5daa-1fda-75df-b2c2-89792bc47700/chicagohealthmap.com_data-glossary.md`.]

Conditions are identified from ICD-10 diagnosis codes. The site says it uses validated
ICD-10 code sets developed through clinical consensus for each phenotype and publishes
a condition reference for 38 chronic conditions plus firearm injury. [Snapshot
2026-07-13; member
`019f5daa-1fda-75df-b2c2-89792bc47700/chicagohealthmap.com_data-glossary.md`.]

## Privacy and reliability

The site states that values are not displayed when fewer than 10 people have a
condition in an area; such values display as `N/A` or `<10`, not zero. It also states
that secondary suppression is applied when needed. [Snapshot 2026-07-13; member
`019f5daa-1fda-75df-b2c2-89792bc47700/chicagohealthmap.com_data-glossary.md`.]

The four stated capture-rate reliability tiers are: High at at least 20% of adults,
Good at 10–20%, Moderate at 5–10%, and Limited below 5%. Labels may carry an equity
note based on demographic alignment; Limited applies in all cases below 5%. [Snapshot
2026-07-13; member
`019f5daa-1fda-75df-b2c2-89792bc47700/chicagohealthmap.com_data-glossary.md`.]

The site states that reliability flags are assigned at census-tract level using 2023
as the reference year and then applied across all map years. [Snapshot 2026-07-13;
member
`019f5daa-1fda-75df-b2c2-89792bc47700/chicagohealthmap.com_data-glossary.md`.]

The stated age-adjustment method is direct standardization to the 2000 U.S. Standard
Population using strata 18–34, 35–44, 45–54, 55–64, 65–74, 75–84, and 85+.
[Snapshot 2026-07-13; member
`019f5daa-1fda-75df-b2c2-89792bc47700/chicagohealthmap.com_data-glossary.md`.]

## Population, geography, and vulnerability references

The listed population reference is the U.S. Census Bureau American Community Survey
five-year estimates, specifically 2018–2022, for rate calculation and
representativeness assessment. [Snapshot 2026-07-13; member
`019f5daa-1fda-75df-b2c2-89792bc47700/chicagohealthmap.com_data-glossary.md`.]

The listed tract geography source is the U.S. Census Bureau TIGER/Line shapefiles,
2020 vintage for Illinois. [Snapshot 2026-07-13; member
`019f5daa-1fda-75df-b2c2-89792bc47700/chicagohealthmap.com_data-glossary.md`.]

The listed Social Vulnerability Index source is CDC/ATSDR, year 2022, covering all
U.S. census tracts. [Snapshot 2026-07-13; member
`019f5daa-1fda-75df-b2c2-89792bc47700/chicagohealthmap.com_data-glossary.md`.]

## Governance and citation

The archived site identifies the CHAIRb study as `STUDY2025-0712: CONSCIENCE`.
[Snapshot 2026-07-13; member
`019f5daa-1fda-75df-b2c2-89792bc47700/chicagohealthmap.com_data-glossary.md`.]

The site's research-paper citation is: “CONSCIENCE Project. (2026). CONSCIENCE:
CONnecting SCIence, ENgaging Chicago for Equity. Chicago, IL: Rush Health Equity Data
Analytics Studio, Rush University System for Health. https://chicagohealthmap.com”.
[Snapshot 2026-07-13; member
`019f5daa-1fda-75df-b2c2-89792bc47700/chicagohealthmap.com_data-glossary.md`.]

The terms-of-use page separately labels this citation as required: “CONSCIENCE Project.
ChicagoHealthMap.com: CONnecting SCIence—ENgaging Chicago for Equity. Chicago, IL: Rush
University System for Health, Rush Health Equity Data Analytics Studio.
https://chicagohealthmap.com. Accessed [Date].” [Snapshot 2026-07-13; member
`019f5daa-1fda-75df-b2c2-89792bc47700/chicagohealthmap.com_terms-of-use.md`.]
