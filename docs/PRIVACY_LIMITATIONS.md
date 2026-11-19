# PulseIQ Explorer — Privacy Limitations

## Current local-demo safeguards

- Department rows below the metric-specific minimum group size are suppressed.
- Invalid group-size inputs (missing, non-numeric, infinite, negative, or fractional values) are suppressed by fail-closed validation.
- The Explorer displays only the latest warehouse reporting month.
- The historical month selector is disabled to reduce straightforward
  month-to-month differencing through the user interface.
- Manager demonstration mode is scoped to its configured department.

## Important limitations

These controls are risk-reduction measures for a local demonstration. They
do not provide differential privacy, formal protection against re-identification,
or a guarantee against differencing attacks.

The role is selected through environment variables, not verified identity.
A person with access to the local environment, database, or application
configuration may be able to change the role or inspect underlying data.
Repeated snapshots over time may also reveal changes.

Before any production or public release, PulseIQ requires, at minimum:

1. Verified identity and server-side authorization.
2. A reviewed privacy threat model and adversarial testing across metrics,
   departments, time periods, and overlapping groups.
3. A controlled query policy with appropriate auditing and protections
   against repeated or overlapping aggregate queries.
4. Security review of the database, API, exports, logs, and deployment.

Do not expose the current demonstration application or its database publicly.
