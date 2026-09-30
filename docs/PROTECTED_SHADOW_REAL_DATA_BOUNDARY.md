# IAMINA — Protected Shadow Real-Data Boundary Audit

Status: **IMPLEMENTED — NO EXTERNAL PROVIDER CALL**

## Goal

Exercise the protected-shadow boundary against a real active staff patient while keeping
all patient-linked clinical content inside IAMINA.

## Success criteria

The audit passes only when:

- subject is an active Django staff account;
- a real local `CLINICIAN_PREP` resolution is produced;
- protected-body reinjection is structurally valid;
- the active module protected verifier accepts the locally reinjected reply;
- the outbound request shape is exactly:
  `locale | script | protected_body_token`;
- deterministic clinical body is absent from the outbound prompt;
- local trigger text is absent from the outbound prompt;
- no processor-policy authorization is invoked;
- no provider adapter is constructed;
- no network/provider call is performed;
- no patient content is persisted by the command.

## Command

```bash
cd backend
python manage.py audit_protected_shadow_real_data_boundary --patient-id <ACTIVE_STAFF_USER_ID> --language fr
```

Use the default neutral clinician-prep trigger. Do not put patient-identifying or
clinical text directly on the shell command line.

## Boundary

This command intentionally stops before processor authorization and provider
construction. It proves that real patient-linked data can reach the local deterministic
resolution and protected-envelope layer without being present in the candidate external
payload.

It does **not**:

- approve Groq governance;
- modify `groq` processor status;
- bypass `authorize_processor_policy()`;
- send patient data or the opaque token to Groq;
- activate patient-visible provider narration;
- deploy Vercel.

## Interpretation

A PASS proves the local real-data boundary for the audited account and exact code HEAD.
It is not evidence of CNDP approval, Groq DPA/ZDR approval, foreign-transfer approval,
or production patient-data egress authorization.
