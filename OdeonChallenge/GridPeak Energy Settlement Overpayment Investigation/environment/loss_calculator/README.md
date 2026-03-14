# Loss Calculator Service

This service computes transmission loss factors for energy settlements.

## Overview

The loss calculator is a critical component of the settlement pipeline. It determines how much energy is lost during transmission from generators to load centers.

## Configuration

Loss factors are configured per zone in the database. Each zone has an energy threshold and a base loss rate. The threshold determines when the full loss rate applies.

## Calculation Method

The service accepts a zone identifier and energy amount. It retrieves the applicable threshold and rate from the database, then invokes the core calculation engine.

The calculation engine is implemented in Fortran for numerical precision and performance. It has been maintained since the original system deployment and handles all the complex zone adjustments and tiered bonuses.

## Zone Adjustments

Different zones have different transmission characteristics. The zone adjustment multiplier accounts for these differences:

NORTH zones have a multiplier of one point one two due to longer transmission distances.

SOUTH zones have a multiplier of zero point nine four reflecting newer infrastructure.

EAST zones have a multiplier of one point zero eight for moderate distance factors.

WEST zones have a multiplier of one point zero three for relatively efficient paths.

CENTRAL zones have a multiplier of zero point nine seven as the hub location.

## Tiered Bonuses

High volume deliveries receive additional loss factor adjustments. Deliveries over five hundred megawatt hours get a bonus of zero point zero one five. Deliveries over one thousand megawatt hours get an additional zero point zero zero eight bonus.

For generators in NORTH or EAST zones, tiered bonuses are multiplied by one point zero five.

## Precision Handling

The final loss factor is truncated to four decimal places. This truncation happens after all adjustments are applied.

## API Usage

POST /calculate with zone and energy_mwh to get a single loss factor.

POST /batch_calculate with an array of items for bulk processing.
