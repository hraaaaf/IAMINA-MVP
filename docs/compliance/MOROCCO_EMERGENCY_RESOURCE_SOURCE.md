# Morocco emergency-resource source record

- Country: `MA`
- Registry owner: IAmina Safety & Compliance
- Source owner: UK Foreign, Commonwealth & Development Office
- Source: Morocco travel advice, “Getting help”
- Verified: 2026-07-30
- Review due: 2027-01-30
- Configured services: ambulance `150`, fire `150`, police `190`, gendarmerie `177`

## Selection rule

These contacts may be returned only when the authenticated patient has explicitly confirmed `country_code=MA`. Device or location suggestions are non-authoritative.

## Failure rule

An unconfirmed country, an unknown country or a record past its review date returns no country-specific number and routes to the generic safe emergency path.

## Maintenance

Any change requires re-verification against a current authoritative source, a new verification date and review of localized patient-facing wording. Historical values must remain recoverable through Git history.
