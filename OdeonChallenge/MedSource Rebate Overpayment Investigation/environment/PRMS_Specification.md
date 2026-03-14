# Pharmacy Rebate Management System Specification

Version 4.2.1 - January 2024

## Overview

This document describes how MedSource Distribution calculates pharmacy rebates. The rebate system was built in the late nineties and has evolved over the years. Please read this entire document carefully as important details are scattered throughout the sections.

## Rebate Calculation Basics

The total rebate for any pharmacy customer combines four factors. First we look at the base revenue which is everything the pharmacy bought from us during the quarter. Then we apply a volume index that rewards larger purchasers. After that we factor in the product mix which accounts for specialty certifications and purchasing patterns. Finally we multiply by the customer class rate based on what type of pharmacy they are.

All four factors multiply together to produce the final rebate amount. Each factor is calculated independently using the rules described in the following sections.

## Volume Rewards

We reward pharmacies that purchase in higher quantities. A pharmacy buying less than ten thousand units in a quarter gets a volume index of zero point nine five. Between ten thousand and twenty four thousand units the index is one point zero zero. Between twenty five thousand and forty nine thousand units we apply one point zero five. Between fifty thousand and ninety nine thousand units the index goes to one point one zero. Any pharmacy purchasing one hundred thousand or more units receives the maximum index of one point one five.

## Product Categories and Certifications

Pharmacies that handle specialty pharmaceuticals can earn enhanced rebate rates. To qualify for specialty enhanced rates a pharmacy must hold active specialty certification that has been in place for more than one hundred eighty days. This means they need at least one hundred eighty one days of certification history to qualify. A pharmacy certified for exactly one hundred eighty days does not yet meet the threshold.

Pharmacies purchasing large volumes in a quarter may also qualify for enhanced rates. The volume threshold for this bonus is fifty thousand units. A pharmacy needs to exceed fifty thousand units to qualify.

When a pharmacy qualifies for both specialty certification and high volume status we apply a compound rate. The compound rate is higher than either individual rate to reward our strongest partners. Specifically the compound rate is one point two eight. Specialty certification alone earns one point one eight. High volume alone earns one point one two. Standard pharmacies without either qualification receive one point zero zero.

The evaluation order matters significantly. We check compound qualifications before checking individual qualifications. This ensures pharmacies receive the highest rate they qualify for rather than an intermediate rate.

## Customer Classifications

We serve five types of pharmacy customers. Independent pharmacies receive a base rate of two percent. Chain pharmacies receive two point five percent. Hospital pharmacies receive three percent. Specialty pharmacies receive four percent. Government accounts receive five percent.

The customer classification is determined when the pharmacy is onboarded and rarely changes.

## Rounding and Precision

All intermediate calculations use four decimal places. Volume index values and product mix factors are stored with full precision during the calculation. Customer class rates use three decimal places. The final rebate amount is rounded to two decimal places which represents cents.

## What This Document Covers

This specification covers the core rebate calculation. It does not cover hospital contracting which operates under separate agreements. It does not cover seasonal inventory planning which is a forecasting function. It does not cover price list management which affects base pricing but not rebate percentages.

## Technical Notes

The calculation engine was written many years ago and has been reliable. The engine reads customer data and outputs the calculated rebate. A Flask API wraps the calculation engine for modern integration. The analytics service provides reporting capabilities.

## Troubleshooting

When investigating rebate amounts always verify the customer class assignment matches what type of pharmacy they actually are. Verify the certification date for specialty pharmacies to confirm they meet the duration requirement. Check the quarterly unit totals to verify volume index assignments.

If rebates seem incorrect compare the actual calculation against this specification. The most common issues involve threshold boundaries where a value is exactly at the cutoff point. Less than a threshold means the threshold value itself is not included. More than a threshold means the threshold value itself is not included either. At least a certain number means exactly that number qualifies.

## Revision History

Version 4.2.1 January 2024 clarified certification duration language.
Version 4.2.0 October 2023 added compound qualification rules.
Version 4.1.0 July 2023 added seasonal factors documentation.
Version 4.0.0 January 2023 integrated API gateway.
